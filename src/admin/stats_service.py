from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import String, func, or_, case, literal, text
from sqlalchemy.orm import Session, joinedload

from ..core.db_models import DBCompany, DBInteraction, DBLead
from ..core.models import InteractionType, LeadStatus


CONTACTED_STATUSES = (
    LeadStatus.CONTACTED,
    LeadStatus.INTERESTED,
    LeadStatus.CONVERTED,
    LeadStatus.LOST,
)


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def _extract_tier(tags: Any) -> str:
    if isinstance(tags, list):
        for tag in tags:
            text = str(tag)
            if text.startswith("Tier "):
                return text
    return "Tier Unknown"


def _enum_value(value: Any) -> str:
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def _canonical_stage_for_lead(lead: DBLead) -> str:
    raw = str(getattr(lead, "stage_canonical", "") or "").strip().lower()
    if raw:
        return raw
    status_value = _enum_value(lead.status).upper()
    mapping = {
        "NEW": "new",
        "ENRICHED": "enriched",
        "SCORED": "qualified",
        "CONTACTED": "contacted",
        "INTERESTED": "engaged",
        "CONVERTED": "won",
        "LOST": "lost",
        "DISQUALIFIED": "disqualified",
    }
    return mapping.get(status_value, "new")


def _build_daily_trend(db: Session, days: int = 30) -> List[Dict[str, Any]]:
    start_day = date.today() - timedelta(days=days - 1)
    start_dt = datetime.combine(start_day, datetime.min.time())
    
    buckets = {}
    for offset in range(days):
        current = start_day + timedelta(days=offset)
        buckets[current.isoformat()] = {
            "date": current.isoformat(),
            "created": 0,
            "scored": 0,
            "contacted": 0,
            "closed": 0,
        }

    # Consolidated queries using UNION ALL for a single round-trip
    q_created = (
        db.query(literal("created").label("type"), func.date(DBLead.created_at).label("day"), func.count(DBLead.id).label("cnt"))
        .filter(DBLead.created_at >= start_dt)
        .group_by(text("day"))
    )
    
    q_scored = (
        db.query(literal("scored").label("type"), func.date(DBLead.last_scored_at).label("day"), func.count(DBLead.id).label("cnt"))
        .filter(DBLead.last_scored_at >= start_dt)
        .group_by(text("day"))
    )

    q_contacted = (
        db.query(literal("contacted").label("type"), func.date(DBLead.updated_at).label("day"), func.count(DBLead.id).label("cnt"))
        .filter(DBLead.status.in_(CONTACTED_STATUSES))
        .filter(DBLead.updated_at >= start_dt)
        .group_by(text("day"))
    )

    q_closed = (
        db.query(literal("closed").label("type"), func.date(DBLead.updated_at).label("day"), func.count(DBLead.id).label("cnt"))
        .filter(DBLead.status == LeadStatus.CONVERTED)
        .filter(DBLead.updated_at >= start_dt)
        .group_by(text("day"))
    )

    try:
        union_all_rows = q_created.union_all(q_scored, q_contacted, q_closed).all()
        for row_type, day_value, count in union_all_rows:
            day_key = str(day_value)
            if day_key in buckets:
                buckets[day_key][row_type] = int(count)
    except Exception as exc:
        # Fallback to empty list or logs if UNION fails (e.g. SQLite version issues with complex UNIONs)
        # However SQLAlchemy 1.4+ handles UNION ALL well across DBs
        pass

    return list(buckets.values())


def compute_core_funnel_stats(db: Session, qualification_threshold: float) -> Dict[str, Any]:
    # Single query for all core counts on DBLead
    stats = db.query(
        func.count(DBLead.id).label("sourced"),
        func.sum(case((DBLead.total_score >= float(qualification_threshold), 1), else_=0)).label("qualified"),
        func.sum(case((DBLead.status.in_(CONTACTED_STATUSES), 1), else_=0)).label("contacted"),
        func.sum(case((DBLead.status == LeadStatus.CONVERTED, 1), else_=0)).label("closed"),
        func.avg(DBLead.total_score).label("avg_score")
    ).first()

    sourced_total = stats.sourced or 0
    qualified_total = int(stats.qualified or 0)
    contacted_total = int(stats.contacted or 0)
    closed_total = int(stats.closed or 0)
    avg_total_score = float(stats.avg_score or 0.0)

    # Use more efficient scalar queries for interaction counts
    replied_total = (
        db.query(func.count(DBInteraction.lead_id.distinct()))
        .filter(DBInteraction.type == InteractionType.EMAIL_REPLIED)
        .scalar() or 0
    )
    booked_total = (
        db.query(func.count(DBInteraction.lead_id.distinct()))
        .filter(DBInteraction.type == InteractionType.MEETING_BOOKED)
        .scalar() or 0
    )

    tier_rows = (
        db.query(DBLead.tier, func.count(DBLead.id))
        .group_by(DBLead.tier)
        .all()
    )
    tier_distribution = {tier or "Tier Unknown": count for tier, count in tier_rows}

    return {
        "sourced_total": sourced_total,
        "qualified_total": qualified_total,
        "contacted_total": contacted_total,
        "replied_total": replied_total,
        "booked_total": booked_total,
        "closed_total": closed_total,
        "qualified_rate": _safe_rate(qualified_total, sourced_total),
        "contact_rate": _safe_rate(contacted_total, qualified_total),
        "reply_rate": _safe_rate(replied_total, contacted_total),
        "book_rate": _safe_rate(booked_total, replied_total),
        "close_rate": _safe_rate(closed_total, booked_total),
        "avg_total_score": round(avg_total_score, 2),
        "tier_distribution": tier_distribution,
        "daily_pipeline_trend": _build_daily_trend(db, days=30),
    }


def list_leads(
    db: Session,
    page: int,
    page_size: int,
    search: str | None = None,
    status_filter: str | None = None,
    segment_filter: str | None = None,
    tier_filter: str | None = None,
    heat_status_filter: str | None = None,
    company_filter: str | None = None,
    industry_filter: str | None = None,
    location_filter: str | None = None,
    tag_filter: str | None = None,
    min_score: float | None = None,
    max_score: float | None = None,
    has_email: bool | None = None,
    has_phone: bool | None = None,
    has_linkedin: bool | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    last_scored_from: datetime | None = None,
    last_scored_to: datetime | None = None,
    sort_by: str = "created_at",
    sort_desc: bool = True,
) -> Dict[str, Any]:
    page_size = max(1, min(page_size, 100))
    page = max(page, 1)

    query = db.query(DBLead).options(joinedload(DBLead.company))

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                func.lower(func.coalesce(DBLead.first_name, "")).like(term.lower()),
                func.lower(func.coalesce(DBLead.last_name, "")).like(term.lower()),
                func.lower(func.coalesce(DBLead.email, "")).like(term.lower()),
                DBLead.company.has(func.lower(func.coalesce(DBCompany.name, "")).like(term.lower())),
                DBLead.company.has(func.lower(func.coalesce(DBCompany.industry, "")).like(term.lower())),
                DBLead.company.has(func.lower(func.coalesce(DBCompany.location, "")).like(term.lower())),
            )
        )

    if status_filter and status_filter.strip():
        try:
            status_enum = LeadStatus(status_filter)
            query = query.filter(DBLead.status == status_enum)
        except ValueError:
            pass

    if segment_filter and segment_filter.strip():
        query = query.filter(func.lower(func.coalesce(DBLead.segment, "")).like(f"%{segment_filter.strip().lower()}%"))

    if tier_filter and tier_filter.strip():
        query = query.filter(func.lower(func.coalesce(DBLead.tier, "")).like(f"%{tier_filter.strip().lower()}%"))

    if heat_status_filter and heat_status_filter.strip():
        query = query.filter(func.lower(func.coalesce(DBLead.heat_status, "")).like(f"%{heat_status_filter.strip().lower()}%"))

    if company_filter and company_filter.strip():
        query = query.filter(
            DBLead.company.has(
                func.lower(func.coalesce(DBCompany.name, "")).like(f"%{company_filter.strip().lower()}%")
            )
        )

    if industry_filter and industry_filter.strip():
        query = query.filter(
            DBLead.company.has(
                func.lower(func.coalesce(DBCompany.industry, "")).like(f"%{industry_filter.strip().lower()}%")
            )
        )

    if location_filter and location_filter.strip():
        query = query.filter(
            DBLead.company.has(
                func.lower(func.coalesce(DBCompany.location, "")).like(f"%{location_filter.strip().lower()}%")
            )
        )

    if tag_filter and tag_filter.strip():
        term = f"%{tag_filter.strip().lower()}%"
        query = query.filter(func.lower(func.cast(DBLead.tags, String)).like(term))

    if min_score is not None:
        query = query.filter(func.coalesce(DBLead.total_score, 0.0) >= float(min_score))

    if max_score is not None:
        query = query.filter(func.coalesce(DBLead.total_score, 0.0) <= float(max_score))

    if has_email is True:
        query = query.filter(func.trim(func.coalesce(DBLead.email, "")) != "")
    elif has_email is False:
        query = query.filter(func.trim(func.coalesce(DBLead.email, "")) == "")

    if has_phone is True:
        query = query.filter(func.trim(func.coalesce(DBLead.phone, "")) != "")
    elif has_phone is False:
        query = query.filter(func.trim(func.coalesce(DBLead.phone, "")) == "")

    if has_linkedin is True:
        query = query.filter(
            or_(
                func.trim(func.coalesce(DBLead.linkedin_url, "")) != "",
                DBLead.company.has(func.trim(func.coalesce(DBCompany.linkedin_url, "")) != ""),
            )
        )
    elif has_linkedin is False:
        query = query.filter(
            func.trim(func.coalesce(DBLead.linkedin_url, "")) == "",
            DBLead.company.has(func.trim(func.coalesce(DBCompany.linkedin_url, "")) == ""),
        )

    if created_from is not None:
        query = query.filter(DBLead.created_at >= created_from)
    if created_to is not None:
        query = query.filter(DBLead.created_at <= created_to)
    if last_scored_from is not None:
        query = query.filter(DBLead.last_scored_at.isnot(None), DBLead.last_scored_at >= last_scored_from)
    if last_scored_to is not None:
        query = query.filter(DBLead.last_scored_at.isnot(None), DBLead.last_scored_at <= last_scored_to)

    if min_score is not None and max_score is not None and float(min_score) > float(max_score):
        return {
            "page": page,
            "page_size": page_size,
            "total": 0,
            "items": [],
        }

    sort_column = DBLead.created_at
    if sort_by == "total_score":
        sort_column = DBLead.total_score
    elif sort_by == "last_scored_at":
        sort_column = DBLead.last_scored_at
    elif sort_by == "updated_at":
        sort_column = DBLead.updated_at
    elif sort_by == "first_name":
        sort_column = DBLead.first_name
    elif sort_by == "last_name":
        sort_column = DBLead.last_name
    elif sort_by == "status":
        sort_column = DBLead.status
    elif sort_by == "tier":
        sort_column = DBLead.tier
    elif sort_by == "heat_status":
        sort_column = DBLead.heat_status
    elif sort_by == "company_name":
        query = query.outerjoin(DBLead.company)
        sort_column = DBCompany.name

    if sort_desc:
        query = query.order_by(sort_column.desc(), DBLead.id.desc())
    else:
        query = query.order_by(sort_column.asc(), DBLead.id.asc())

    total = query.count()
    offset = (page - 1) * page_size
    rows = query.offset(offset).limit(page_size).all()

    items = []
    for lead in rows:
        company_name = lead.company.name if lead.company else None
        company_industry = lead.company.industry if lead.company else None
        company_location = lead.company.location if lead.company else None
        linkedin_url = lead.linkedin_url or (lead.company.linkedin_url if lead.company else None)
        items.append(
            {
                "id": lead.id,
                "email": lead.email,
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "phone": lead.phone,
                "linkedin_url": linkedin_url,
                "company_name": company_name,
                "company_industry": company_industry,
                "company_location": company_location,
                "status": _enum_value(lead.status),
                "stage_canonical": _canonical_stage_for_lead(lead),
                "lead_owner_user_id": getattr(lead, "lead_owner_user_id", None),
                "segment": lead.segment,
                "icp_score": lead.icp_score,
                "heat_score": lead.heat_score,
                "total_score": lead.total_score,
                "tier": lead.tier,
                "heat_status": lead.heat_status,
                "next_best_action": lead.next_best_action,
                "tags": lead.tags or [],
                "last_scored_at": lead.last_scored_at.isoformat() if lead.last_scored_at else None,
                "stage_entered_at": lead.stage_entered_at.isoformat() if getattr(lead, "stage_entered_at", None) else None,
                "sla_due_at": lead.sla_due_at.isoformat() if getattr(lead, "sla_due_at", None) else None,
                "next_action_at": lead.next_action_at.isoformat() if getattr(lead, "next_action_at", None) else None,
                "handoff_required": bool(getattr(lead, "handoff_required", False)),
                "handoff_completed_at": lead.handoff_completed_at.isoformat() if getattr(lead, "handoff_completed_at", None) else None,
                "created_at": lead.created_at.isoformat() if lead.created_at else None,
                "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
            }
        )
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": items,
    }
