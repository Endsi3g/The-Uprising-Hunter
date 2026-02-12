from __future__ import annotations

import os
import secrets
import time
import uuid
from datetime import datetime, time as datetime_time
from pathlib import Path
from threading import Lock
from typing import Annotated, Any

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, or_, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.requests import Request

from ..core.database import Base, engine, get_db
from ..core.db_migrations import ensure_sqlite_schema_compatibility
from ..core.db_models import DBAdminSetting, DBCompany, DBLead, DBProject, DBTask
from ..core.logging import configure_logging, get_logger
from ..core.models import Company, Interaction, Lead, LeadStage, LeadStatus
from ..scoring.engine import ScoringEngine
from .stats_service import compute_core_funnel_stats, list_leads


security = HTTPBasic()
templates = Jinja2Templates(directory=str(Path(__file__).with_name("templates")))
scoring_engine = ScoringEngine()
logger = get_logger(__name__)


DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "change-me"

DEFAULT_ADMIN_SETTINGS: dict[str, Any] = {
    "organization_name": "Prospect",
    "locale": "fr-FR",
    "timezone": "Europe/Paris",
    "default_page_size": 25,
    "dashboard_refresh_seconds": 30,
    "support_email": "support@example.com",
}

PROJECT_STATUSES = {"Planning", "In Progress", "On Hold", "Completed", "Cancelled"}
TASK_STATUSES = {"To Do", "In Progress", "Done"}
TASK_PRIORITIES = {"Low", "Medium", "High", "Critical"}


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._lock = Lock()
        self._hits: dict[str, list[float]] = {}

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.time()
        window_start = now - window_seconds
        with self._lock:
            entries = self._hits.get(key, [])
            entries = [stamp for stamp in entries if stamp >= window_start]
            if len(entries) >= limit:
                self._hits[key] = entries
                return False
            entries.append(now)
            self._hits[key] = entries
            return True


rate_limiter = InMemoryRateLimiter()


class AdminLeadCreateRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None = None
    company_name: str
    status: str | None = None
    segment: str | None = None


class AdminTaskCreateRequest(BaseModel):
    title: str
    status: str | None = None
    priority: str | None = None
    due_date: str | None = None
    assigned_to: str | None = None
    lead_id: str | None = None


class AdminProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    status: str | None = None
    lead_id: str | None = None
    due_date: str | None = None


class AdminProjectUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    status: str | None = None
    lead_id: str | None = None
    due_date: str | None = None


class AdminSettingsPayload(BaseModel):
    organization_name: str
    locale: str
    timezone: str
    default_page_size: int
    dashboard_refresh_seconds: int
    support_email: EmailStr


class AdminSettingsUpdatePayload(BaseModel):
    organization_name: str | None = None
    locale: str | None = None
    timezone: str | None = None
    default_page_size: int | None = None
    dashboard_refresh_seconds: int | None = None
    support_email: EmailStr | None = None


class AdminSearchResultItem(BaseModel):
    type: str
    id: str
    title: str
    subtitle: str
    href: str


class AdminHelpPayload(BaseModel):
    support_email: EmailStr
    faqs: list[dict[str, str]]
    links: list[dict[str, str]]


def _is_production() -> bool:
    env_name = (
        os.getenv("APP_ENV")
        or os.getenv("ENV")
        or os.getenv("ENVIRONMENT")
        or "development"
    )
    return env_name.strip().lower() in {"prod", "production"}


def _validate_admin_credentials_security() -> None:
    if not _is_production():
        return

    username = os.getenv("ADMIN_USERNAME", DEFAULT_ADMIN_USERNAME)
    password = os.getenv("ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)
    insecure_username = username == DEFAULT_ADMIN_USERNAME
    insecure_password = password == DEFAULT_ADMIN_PASSWORD
    if insecure_username or insecure_password:
        raise RuntimeError(
            "Refusing startup in production with default admin credentials. "
            "Set ADMIN_USERNAME and ADMIN_PASSWORD."
        )


def _parse_cors_origins() -> list[str]:
    raw = os.getenv(
        "ADMIN_CORS_ALLOW_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return origins or ["http://localhost:3000", "http://127.0.0.1:3000"]


def _init_admin_db() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_schema_compatibility(engine)


def require_admin(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> str:
    expected_username = os.getenv("ADMIN_USERNAME", DEFAULT_ADMIN_USERNAME)
    expected_password = os.getenv("ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)

    is_valid_user = secrets.compare_digest(credentials.username, expected_username)
    is_valid_pass = secrets.compare_digest(credentials.password, expected_password)
    if not (is_valid_user and is_valid_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials.",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def require_rate_limit(request: Request) -> None:
    try:
        limit = int(os.getenv("ADMIN_RATE_LIMIT_PER_MINUTE", "120"))
    except ValueError:
        limit = 120
    try:
        window_seconds = int(os.getenv("ADMIN_RATE_LIMIT_WINDOW_SECONDS", "60"))
    except ValueError:
        window_seconds = 60

    client_host = request.client.host if request.client else "unknown"
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if forwarded_for:
        client_host = forwarded_for.split(",")[0].strip()
    bucket_key = f"{client_host}:{request.url.path}"

    allowed = rate_limiter.allow(bucket_key, limit=limit, window_seconds=window_seconds)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please retry later.",
        )


def _parse_datetime_field(raw_value: str | None, field_name: str) -> datetime | None:
    if raw_value is None:
        return None
    cleaned = raw_value.strip()
    if not cleaned:
        return None
    try:
        normalized = cleaned.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid datetime for {field_name}: {raw_value}",
        ) from exc


def _coerce_lead_status(raw_status: str | None) -> LeadStatus:
    if not raw_status:
        return LeadStatus.NEW
    normalized = raw_status.strip().upper()
    try:
        return LeadStatus(normalized)
    except ValueError:
        return LeadStatus.NEW


def _coerce_project_status(raw_status: str | None) -> str:
    if not raw_status:
        return "Planning"
    candidate = raw_status.strip()
    for known in PROJECT_STATUSES:
        if known.lower() == candidate.lower():
            return known
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=f"Unsupported project status: {raw_status}",
    )


def _coerce_task_status(raw_status: str | None) -> str:
    if not raw_status:
        return "To Do"
    candidate = raw_status.strip()
    for known in TASK_STATUSES:
        if known.lower() == candidate.lower():
            return known
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=f"Unsupported task status: {raw_status}",
    )


def _coerce_task_priority(raw_priority: str | None) -> str:
    if not raw_priority:
        return "Medium"
    candidate = raw_priority.strip()
    for known in TASK_PRIORITIES:
        if known.lower() == candidate.lower():
            return known
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=f"Unsupported task priority: {raw_priority}",
    )


def _db_to_lead(db_lead: DBLead) -> Lead:
    company = Company(
        name=db_lead.company.name if db_lead.company else "Unknown",
        domain=db_lead.company.domain if db_lead.company else None,
        industry=db_lead.company.industry if db_lead.company else None,
        size_range=db_lead.company.size_range if db_lead.company else None,
        revenue_range=db_lead.company.revenue_range if db_lead.company else None,
        linkedin_url=db_lead.company.linkedin_url if db_lead.company else None,
        location=db_lead.company.location if db_lead.company else None,
        tech_stack=db_lead.company.tech_stack if db_lead.company else [],
        description=db_lead.company.description if db_lead.company else None,
    )

    interactions = [
        Interaction(
            id=f"{db_lead.id}-{interaction.id}",
            type=interaction.type,
            timestamp=interaction.timestamp,
            details=interaction.details or {},
        )
        for interaction in db_lead.interactions
    ]

    return Lead(
        id=db_lead.id,
        first_name=db_lead.first_name or "Unknown",
        last_name=db_lead.last_name or "",
        email=db_lead.email,
        title=db_lead.title,
        phone=db_lead.phone,
        linkedin_url=db_lead.linkedin_url,
        company=company,
        status=db_lead.status,
        segment=db_lead.segment,
        interactions=interactions,
        details=db_lead.details or {},
        tags=db_lead.tags or [],
        created_at=db_lead.created_at,
        updated_at=db_lead.updated_at,
    )


def _serialize_task(task: DBTask) -> dict[str, Any]:
    return {
        "id": task.id,
        "title": task.title,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "assigned_to": task.assigned_to,
        "lead_id": task.lead_id,
        "created_at": task.created_at.isoformat() if task.created_at else None,
    }


def _serialize_project(project: DBProject) -> dict[str, Any]:
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "lead_id": project.lead_id,
        "due_date": project.due_date.isoformat() if project.due_date else None,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


def _create_lead_payload(db: Session, payload: AdminLeadCreateRequest) -> dict[str, Any]:
    existing = db.query(DBLead).filter(DBLead.email == str(payload.email)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Lead already exists for email {payload.email}.",
        )

    company = (
        db.query(DBCompany)
        .filter(DBCompany.name == payload.company_name.strip())
        .first()
    )
    if not company:
        company = DBCompany(name=payload.company_name.strip(), domain=None)
        db.add(company)
        db.flush()

    db_lead = DBLead(
        id=str(payload.email),
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        email=str(payload.email),
        phone=payload.phone.strip() if payload.phone else None,
        company_id=company.id,
        status=_coerce_lead_status(payload.status),
        segment=(payload.segment or "General").strip(),
        stage=LeadStage.NEW,
    )
    db.add(db_lead)
    try:
        db.commit()
        db.refresh(db_lead)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to create lead from admin API.", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create lead.",
        ) from exc

    return {
        "id": db_lead.id,
        "email": db_lead.email,
        "first_name": db_lead.first_name,
        "last_name": db_lead.last_name,
        "status": db_lead.status.value if hasattr(db_lead.status, "value") else str(db_lead.status),
        "segment": db_lead.segment,
        "company_name": company.name,
        "created_at": db_lead.created_at.isoformat() if db_lead.created_at else None,
    }


def _create_task_payload(db: Session, payload: AdminTaskCreateRequest) -> dict[str, Any]:
    task = DBTask(
        id=str(uuid.uuid4()),
        title=payload.title.strip(),
        status=_coerce_task_status(payload.status),
        priority=_coerce_task_priority(payload.priority),
        due_date=_parse_datetime_field(payload.due_date, "due_date"),
        assigned_to=(payload.assigned_to or "You").strip(),
        lead_id=payload.lead_id,
    )
    db.add(task)
    try:
        db.commit()
        db.refresh(task)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to create task.", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task.",
        ) from exc
    return _serialize_task(task)


def _create_project_payload(db: Session, payload: AdminProjectCreateRequest) -> dict[str, Any]:
    project = DBProject(
        id=str(uuid.uuid4()),
        name=payload.name.strip(),
        description=payload.description.strip() if payload.description else None,
        status=_coerce_project_status(payload.status),
        lead_id=payload.lead_id,
        due_date=_parse_datetime_field(payload.due_date, "due_date"),
    )
    db.add(project)
    try:
        db.commit()
        db.refresh(project)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to create project.", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project.",
        ) from exc
    return _serialize_project(project)


def _update_project_payload(
    db: Session,
    project_id: str,
    payload: AdminProjectUpdateRequest,
) -> dict[str, Any]:
    project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    update_data = payload.model_dump(exclude_unset=True)
    if "name" in update_data and payload.name is not None:
        project.name = payload.name.strip()
    if "description" in update_data:
        project.description = payload.description.strip() if payload.description else None
    if "status" in update_data:
        project.status = _coerce_project_status(payload.status)
    if "lead_id" in update_data:
        project.lead_id = payload.lead_id
    if "due_date" in update_data:
        project.due_date = _parse_datetime_field(payload.due_date, "due_date")

    try:
        db.commit()
        db.refresh(project)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to update project.", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project.",
        ) from exc
    return _serialize_project(project)


def _delete_project_payload(db: Session, project_id: str) -> dict[str, Any]:
    project = db.query(DBProject).filter(DBProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    db.delete(project)
    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to delete project.", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project.",
        ) from exc
    return {"deleted": True, "id": project_id}


def _get_stats_payload(db: Session) -> dict[str, Any]:
    return compute_core_funnel_stats(
        db=db,
        qualification_threshold=scoring_engine.qualification_threshold,
    )


def _get_leads_payload(db: Session, page: int, page_size: int) -> dict[str, Any]:
    return list_leads(db=db, page=page, page_size=page_size)


def _rescore_payload(db: Session) -> dict[str, Any]:
    updated = 0
    failed = 0
    leads = db.query(DBLead).all()
    for db_lead in leads:
        try:
            lead = _db_to_lead(db_lead)
            lead = scoring_engine.score_lead(lead)
        except (ValueError, TypeError, AttributeError) as exc:
            failed += 1
            logger.warning(
                "Skipping lead during rescore due to malformed payload.",
                extra={"lead_id": db_lead.id, "error": str(exc)},
            )
            continue

        db_lead.icp_score = lead.score.icp_score
        db_lead.heat_score = lead.score.heat_score
        db_lead.total_score = lead.score.total_score
        db_lead.tier = lead.score.tier
        db_lead.heat_status = lead.score.heat_status
        db_lead.next_best_action = lead.score.next_best_action
        db_lead.icp_breakdown = lead.score.icp_breakdown
        db_lead.heat_breakdown = lead.score.heat_breakdown
        db_lead.score_breakdown = {
            "icp": lead.score.icp_breakdown,
            "heat": lead.score.heat_breakdown,
        }
        db_lead.last_scored_at = lead.score.last_scored_at
        db_lead.tags = lead.tags
        db_lead.details = lead.details
        updated += 1

    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to commit lead rescoring.", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist rescored leads.",
        ) from exc
    return {"updated": updated, "failed": failed}


def _preview_payload(lead: Lead) -> dict[str, Any]:
    scored = scoring_engine.score_lead(lead)
    return {
        "lead_id": scored.id,
        "company_name": scored.company.name,
        "icp_score": scored.score.icp_score,
        "heat_score": scored.score.heat_score,
        "total_score": scored.score.total_score,
        "tier": scored.score.tier,
        "heat_status": scored.score.heat_status,
        "next_best_action": scored.score.next_best_action,
        "icp_breakdown": scored.score.icp_breakdown,
        "heat_breakdown": scored.score.heat_breakdown,
        "tags": scored.tags,
        "details": {
            "should_send_loom": scored.details.get("should_send_loom", False),
            "propose_stripe_link": scored.details.get("propose_stripe_link", False),
            "tier_action": scored.details.get("tier_action"),
            "heat_action": scored.details.get("heat_action"),
        },
    }


def _get_admin_settings_payload(db: Session) -> dict[str, Any]:
    payload = dict(DEFAULT_ADMIN_SETTINGS)
    rows = db.query(DBAdminSetting).all()
    for row in rows:
        if row.key in payload:
            payload[row.key] = row.value_json

    payload["organization_name"] = str(payload.get("organization_name") or DEFAULT_ADMIN_SETTINGS["organization_name"])
    payload["locale"] = str(payload.get("locale") or DEFAULT_ADMIN_SETTINGS["locale"])
    payload["timezone"] = str(payload.get("timezone") or DEFAULT_ADMIN_SETTINGS["timezone"])

    try:
        payload["default_page_size"] = int(payload.get("default_page_size") or DEFAULT_ADMIN_SETTINGS["default_page_size"])
    except (TypeError, ValueError):
        payload["default_page_size"] = int(DEFAULT_ADMIN_SETTINGS["default_page_size"])
    payload["default_page_size"] = max(5, min(payload["default_page_size"], 200))

    try:
        payload["dashboard_refresh_seconds"] = int(payload.get("dashboard_refresh_seconds") or DEFAULT_ADMIN_SETTINGS["dashboard_refresh_seconds"])
    except (TypeError, ValueError):
        payload["dashboard_refresh_seconds"] = int(DEFAULT_ADMIN_SETTINGS["dashboard_refresh_seconds"])
    payload["dashboard_refresh_seconds"] = max(10, min(payload["dashboard_refresh_seconds"], 3600))

    payload["support_email"] = str(payload.get("support_email") or DEFAULT_ADMIN_SETTINGS["support_email"])
    return AdminSettingsPayload(**payload).model_dump()


def _save_admin_settings_payload(db: Session, payload: AdminSettingsPayload) -> dict[str, Any]:
    normalized = payload.model_dump()
    normalized["default_page_size"] = max(5, min(int(normalized["default_page_size"]), 200))
    normalized["dashboard_refresh_seconds"] = max(
        10,
        min(int(normalized["dashboard_refresh_seconds"]), 3600),
    )

    for key, value in normalized.items():
        row = db.query(DBAdminSetting).filter(DBAdminSetting.key == key).first()
        if not row:
            row = DBAdminSetting(key=key, value_json=value)
            db.add(row)
        else:
            row.value_json = value

    try:
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Failed to persist admin settings.", extra={"error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save settings.",
        ) from exc

    return _get_admin_settings_payload(db)


def _get_analytics_payload(db: Session) -> dict[str, Any]:
    total_leads = db.query(DBLead).count()
    status_rows = db.query(DBLead.status, func.count(DBLead.id)).group_by(DBLead.status).all()
    leads_by_status: dict[str, int] = {}
    for status_value, count in status_rows:
        key = status_value.value if hasattr(status_value, "value") else str(status_value)
        leads_by_status[key] = int(count)

    total_tasks = db.query(DBTask).count()
    completed_tasks = db.query(DBTask).filter(DBTask.status == "Done").count()
    task_completion_rate = round((completed_tasks / total_tasks) * 100, 2) if total_tasks else 0.0

    pipeline_raw = db.query(func.sum(DBLead.total_score)).scalar() or 0.0
    pipeline_value = round(float(pipeline_raw) * 1000, 2)

    today_start = datetime.combine(datetime.now().date(), datetime_time.min)
    new_leads_today = db.query(DBLead).filter(DBLead.created_at >= today_start).count()

    return {
        "total_leads": total_leads,
        "leads_by_status": leads_by_status,
        "task_completion_rate": task_completion_rate,
        "pipeline_value": pipeline_value,
        "new_leads_today": new_leads_today,
    }


def _search_payload(db: Session, query: str, limit: int) -> dict[str, Any]:
    clean_query = query.strip()
    if not clean_query:
        return {"query": query, "total": 0, "items": []}

    result_limit = max(1, min(limit, 50))
    pattern = f"%{clean_query}%"

    items: list[dict[str, str]] = []

    lead_rows = (
        db.query(DBLead)
        .filter(
            or_(
                DBLead.first_name.ilike(pattern),
                DBLead.last_name.ilike(pattern),
                DBLead.email.ilike(pattern),
            )
        )
        .order_by(DBLead.created_at.desc())
        .limit(result_limit)
        .all()
    )
    for lead in lead_rows:
        lead_name = f"{lead.first_name or ''} {lead.last_name or ''}".strip() or lead.email
        items.append(
            {
                "type": "lead",
                "id": lead.id,
                "title": lead_name,
                "subtitle": lead.email,
                "href": f"/leads?lead_id={lead.id}",
            }
        )

    task_rows = (
        db.query(DBTask)
        .filter(
            or_(
                DBTask.title.ilike(pattern),
                DBTask.status.ilike(pattern),
                DBTask.assigned_to.ilike(pattern),
            )
        )
        .order_by(DBTask.created_at.desc())
        .limit(result_limit)
        .all()
    )
    for task in task_rows:
        items.append(
            {
                "type": "task",
                "id": task.id,
                "title": task.title,
                "subtitle": f"{task.status} - {task.priority}",
                "href": f"/tasks?task_id={task.id}",
            }
        )

    project_rows = (
        db.query(DBProject)
        .filter(
            or_(
                DBProject.name.ilike(pattern),
                DBProject.status.ilike(pattern),
                DBProject.description.ilike(pattern),
            )
        )
        .order_by(DBProject.created_at.desc())
        .limit(result_limit)
        .all()
    )
    for project in project_rows:
        items.append(
            {
                "type": "project",
                "id": project.id,
                "title": project.name,
                "subtitle": project.status,
                "href": f"/projects?project_id={project.id}",
            }
        )

    unique_items: list[dict[str, str]] = []
    seen = set()
    for item in items:
        unique_key = (item["type"], item["id"])
        if unique_key in seen:
            continue
        seen.add(unique_key)
        unique_items.append(item)
        if len(unique_items) >= result_limit:
            break

    return {
        "query": query,
        "total": len(unique_items),
        "items": unique_items,
    }


def _help_payload(db: Session) -> dict[str, Any]:
    settings = _get_admin_settings_payload(db)
    payload = AdminHelpPayload(
        support_email=settings["support_email"],
        faqs=[
            {
                "question": "Comment creer un lead rapidement ?",
                "answer": "Utilisez le bouton 'Creation rapide de lead' dans la barre laterale.",
            },
            {
                "question": "Comment convertir une tache en projet ?",
                "answer": "Depuis la table des taches, utilisez l'action 'Convertir en projet'.",
            },
            {
                "question": "Ou modifier les parametres globaux ?",
                "answer": "Allez sur la page Parametres puis enregistrez vos preferences.",
            },
        ],
        links=[
            {"label": "Centre d'aide complet", "href": "/help"},
            {"label": "Console backend", "href": "/admin"},
            {"label": "Guide API FastAPI", "href": "https://fastapi.tiangolo.com/"},
        ],
    )
    return payload.model_dump()


def create_app() -> FastAPI:
    configure_logging()
    _validate_admin_credentials_security()
    app = FastAPI(title="Prospect Admin Dashboard", version="1.0.0")
    _init_admin_db()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_parse_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    api_v1 = APIRouter(prefix="/api/v1")
    admin_v1 = APIRouter(
        prefix="/admin",
        dependencies=[Depends(require_admin), Depends(require_rate_limit)],
    )

    @app.get("/healthz")
    def healthcheck(db: Session = Depends(get_db)) -> dict[str, Any]:
        try:
            db.execute(text("SELECT 1"))
            db_ok = True
        except SQLAlchemyError as exc:
            logger.warning("Healthcheck DB query failed.", extra={"error": str(exc)})
            db_ok = False
        return {"ok": db_ok, "service": "prospect-admin-api"}

    @app.get("/admin", response_class=HTMLResponse)
    def admin_dashboard(
        request: Request,
        _: Annotated[str, Depends(require_admin)],
    ) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "admin_dashboard.html",
            {
                "qualification_threshold": scoring_engine.qualification_threshold,
            },
        )

    @admin_v1.get("/stats")
    def get_stats_v1(db: Session = Depends(get_db)) -> dict[str, Any]:
        return _get_stats_payload(db)

    @admin_v1.get("/leads")
    def get_leads_v1(
        db: Session = Depends(get_db),
        page: int = Query(default=1, ge=1),
        page_size: int = Query(default=25, ge=1, le=100),
    ) -> dict[str, Any]:
        return _get_leads_payload(db, page=page, page_size=page_size)

    @admin_v1.post("/leads")
    def create_lead_v1(
        payload: AdminLeadCreateRequest,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        return _create_lead_payload(db, payload)

    @admin_v1.post("/tasks")
    def create_task_v1(
        payload: AdminTaskCreateRequest,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        return _create_task_payload(db, payload)

    @admin_v1.get("/tasks")
    def list_tasks_v1(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
        tasks = db.query(DBTask).order_by(DBTask.created_at.desc()).all()
        return [_serialize_task(task) for task in tasks]

    @admin_v1.post("/rescore")
    def rescore_leads_v1(db: Session = Depends(get_db)) -> dict[str, Any]:
        return _rescore_payload(db)

    @admin_v1.get("/projects")
    def list_projects_v1(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
        projects = db.query(DBProject).order_by(DBProject.created_at.desc()).all()
        return [_serialize_project(project) for project in projects]

    @admin_v1.post("/projects")
    def create_project_v1(
        payload: AdminProjectCreateRequest,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        return _create_project_payload(db, payload)

    @admin_v1.patch("/projects/{project_id}")
    def update_project_v1(
        project_id: str,
        payload: AdminProjectUpdateRequest,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        return _update_project_payload(db, project_id, payload)

    @admin_v1.delete("/projects/{project_id}")
    def delete_project_v1(
        project_id: str,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        return _delete_project_payload(db, project_id)

    @admin_v1.get("/analytics")
    def analytics_v1(db: Session = Depends(get_db)) -> dict[str, Any]:
        return _get_analytics_payload(db)

    @admin_v1.get("/settings")
    def get_settings_v1(db: Session = Depends(get_db)) -> dict[str, Any]:
        return _get_admin_settings_payload(db)

    @admin_v1.put("/settings")
    def put_settings_v1(
        payload: AdminSettingsPayload,
        db: Session = Depends(get_db),
    ) -> dict[str, Any]:
        return _save_admin_settings_payload(db, payload)

    @admin_v1.get("/search")
    def search_v1(
        db: Session = Depends(get_db),
        q: str = Query(default=""),
        limit: int = Query(default=20, ge=1, le=50),
    ) -> dict[str, Any]:
        return _search_payload(db, query=q, limit=limit)

    @admin_v1.get("/help")
    def help_v1(db: Session = Depends(get_db)) -> dict[str, Any]:
        return _help_payload(db)

    @api_v1.post(
        "/score/preview",
        dependencies=[Depends(require_admin), Depends(require_rate_limit)],
    )
    def preview_score_v1(lead: Lead) -> dict[str, Any]:
        return _preview_payload(lead)

    api_v1.include_router(admin_v1)
    app.include_router(api_v1)

    return app


app = create_app()
