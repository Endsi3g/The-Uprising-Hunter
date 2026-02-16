from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.db_models import (
    DBAdminUser,
    DBLead,
    DBOpportunity,
    DBSmartRecommendation,
    DBStageEvent,
    DBTask,
)
from ..core.models import LeadStage, LeadStatus


CANONICAL_STAGES: tuple[str, ...] = (
    "new",
    "enriched",
    "qualified",
    "contacted",
    "engaged",
    "opportunity",
    "won",
    "post_sale",
)
TERMINAL_STAGES = {"lost", "disqualified"}
VALID_STAGES = set(CANONICAL_STAGES) | TERMINAL_STAGES

LEGACY_STATUS_TO_CANONICAL: dict[str, str] = {
    "NEW": "new",
    "ENRICHED": "enriched",
    "SCORED": "qualified",
    "CONTACTED": "contacted",
    "INTERESTED": "engaged",
    "CONVERTED": "won",
    "LOST": "lost",
    "DISQUALIFIED": "disqualified",
}

LEGACY_LEAD_STAGE_TO_CANONICAL: dict[str, str] = {
    "NEW": "new",
    "CONTACTED": "contacted",
    "OPENED": "engaged",
    "REPLIED": "engaged",
    "BOOKED": "opportunity",
    "SHOW": "opportunity",
    "SOLD": "won",
    "LOST": "lost",
}

LEGACY_OPPORTUNITY_STAGE_TO_CANONICAL: dict[str, str] = {
    "prospect": "contacted",
    "qualified": "qualified",
    "qualification": "qualified",
    "discovery": "engaged",
    "proposed": "opportunity",
    "proposal": "opportunity",
    "negotiation": "opportunity",
    "won": "won",
    "lost": "lost",
}

STAGE_SLA_HOURS: dict[str, int] = {
    "new": 24,
    "enriched": 24,
    "qualified": 24,
    "contacted": 48,
    "engaged": 48,
    "opportunity": 72,
    "won": 24,
    "post_sale": 24 * 7,
    "lost": 24 * 7,
    "disqualified": 24 * 7,
}

NEXT_ACTION_HOURS: dict[str, int] = {
    "new": 4,
    "enriched": 6,
    "qualified": 8,
    "contacted": 12,
    "engaged": 12,
    "opportunity": 18,
    "won": 4,
    "post_sale": 48,
    "lost": 48,
    "disqualified": 48,
}


def normalize_stage(value: str) -> str:
    candidate = (value or "").strip().lower()
    if candidate in VALID_STAGES:
        return candidate
    allowed = ", ".join(sorted(VALID_STAGES))
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=f"Unsupported canonical stage: {value}. Allowed: {allowed}",
    )


def canonical_from_lead(lead: DBLead) -> str:
    raw = (lead.stage_canonical or "").strip().lower()
    if raw:
        return normalize_stage(raw)
    status_key = str(getattr(lead.status, "value", lead.status) or "").strip().upper()
    if status_key in LEGACY_STATUS_TO_CANONICAL:
        return LEGACY_STATUS_TO_CANONICAL[status_key]
    stage_key = str(getattr(lead.stage, "value", lead.stage) or "").strip().upper()
    if stage_key in LEGACY_LEAD_STAGE_TO_CANONICAL:
        return LEGACY_LEAD_STAGE_TO_CANONICAL[stage_key]
    return "new"


def canonical_from_opportunity(opportunity: DBOpportunity) -> str:
    raw = (opportunity.stage_canonical or "").strip().lower()
    if raw:
        return normalize_stage(raw)
    stage_key = str(opportunity.stage or "").strip().lower()
    if stage_key in LEGACY_OPPORTUNITY_STAGE_TO_CANONICAL:
        return LEGACY_OPPORTUNITY_STAGE_TO_CANONICAL[stage_key]
    return "opportunity"


def _legacy_lead_status_from_canonical(stage: str) -> LeadStatus:
    mapping = {
        "new": LeadStatus.NEW,
        "enriched": LeadStatus.ENRICHED,
        "qualified": LeadStatus.SCORED,
        "contacted": LeadStatus.CONTACTED,
        "engaged": LeadStatus.INTERESTED,
        "opportunity": LeadStatus.INTERESTED,
        "won": LeadStatus.CONVERTED,
        "post_sale": LeadStatus.CONVERTED,
        "lost": LeadStatus.LOST,
        "disqualified": LeadStatus.DQ,
    }
    return mapping.get(stage, LeadStatus.NEW)


def _legacy_lead_stage_from_canonical(stage: str) -> LeadStage:
    mapping = {
        "new": LeadStage.NEW,
        "enriched": LeadStage.NEW,
        "qualified": LeadStage.NEW,
        "contacted": LeadStage.CONTACTED,
        "engaged": LeadStage.OPENED,
        "opportunity": LeadStage.BOOKED,
        "won": LeadStage.SOLD,
        "post_sale": LeadStage.SOLD,
        "lost": LeadStage.LOST,
        "disqualified": LeadStage.LOST,
    }
    return mapping.get(stage, LeadStage.NEW)


def _opportunity_stage_from_canonical(stage: str) -> str:
    mapping = {
        "new": "Prospect",
        "enriched": "Prospect",
        "qualified": "Qualified",
        "contacted": "Prospect",
        "engaged": "Qualified",
        "opportunity": "Proposed",
        "won": "Won",
        "post_sale": "Won",
        "lost": "Lost",
        "disqualified": "Lost",
    }
    return mapping.get(stage, "Prospect")


def _opportunity_status_from_canonical(stage: str) -> str:
    if stage in {"won", "post_sale"}:
        return "won"
    if stage in {"lost", "disqualified"}:
        return "lost"
    return "open"


def _stage_deadline(stage: str, now: datetime | None = None) -> tuple[datetime, datetime]:
    current = now or datetime.utcnow()
    return (
        current + timedelta(hours=int(STAGE_SLA_HOURS.get(stage, 24))),
        current + timedelta(hours=int(NEXT_ACTION_HOURS.get(stage, 8))),
    )


def serialize_stage_event(event: DBStageEvent) -> dict[str, Any]:
    return {
        "id": event.id,
        "entity_type": event.entity_type,
        "entity_id": event.entity_id,
        "from_stage": event.from_stage,
        "to_stage": event.to_stage,
        "reason": event.reason,
        "actor": event.actor,
        "source": event.source,
        "metadata": event.metadata_json or {},
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }


def _create_stage_event(
    db: Session,
    *,
    entity_type: str,
    entity_id: str,
    from_stage: str | None,
    to_stage: str,
    reason: str | None,
    actor: str,
    source: str,
    metadata: dict[str, Any] | None = None,
) -> DBStageEvent:
    event = DBStageEvent(
        id=str(uuid.uuid4()),
        entity_type=entity_type,
        entity_id=entity_id,
        from_stage=from_stage,
        to_stage=to_stage,
        reason=(reason or "").strip() or None,
        actor=(actor or "system").strip() or "system",
        source=(source or "manual").strip() or "manual",
        metadata_json=metadata or {},
    )
    db.add(event)
    return event


def _default_owner_user(db: Session) -> DBAdminUser | None:
    return (
        db.query(DBAdminUser)
        .filter(DBAdminUser.status == "active")
        .order_by(DBAdminUser.updated_at.desc(), DBAdminUser.created_at.asc())
        .first()
    )


def resolve_owner_user(
    db: Session,
    *,
    user_id: str | None = None,
    email: str | None = None,
    display_name: str | None = None,
) -> DBAdminUser:
    if user_id and user_id.strip():
        user = db.query(DBAdminUser).filter(DBAdminUser.id == user_id.strip()).first()
        if user:
            return user
    if email and email.strip():
        user = (
            db.query(DBAdminUser)
            .filter(func.lower(DBAdminUser.email) == email.strip().lower())
            .first()
        )
        if user:
            return user
    if display_name and display_name.strip():
        user = (
            db.query(DBAdminUser)
            .filter(func.lower(func.coalesce(DBAdminUser.display_name, "")) == display_name.strip().lower())
            .first()
        )
        if user:
            return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner user not found.")


def ensure_lead_funnel_defaults(db: Session, lead: DBLead) -> None:
    changed = False
    canonical = canonical_from_lead(lead)
    if (lead.stage_canonical or "").strip().lower() != canonical:
        lead.stage_canonical = canonical
        changed = True

    if lead.stage_entered_at is None:
        lead.stage_entered_at = lead.updated_at or lead.created_at or datetime.utcnow()
        changed = True
    if lead.sla_due_at is None or lead.next_action_at is None:
        sla_due_at, next_action_at = _stage_deadline(canonical, lead.stage_entered_at)
        lead.sla_due_at = lead.sla_due_at or sla_due_at
        lead.next_action_at = lead.next_action_at or next_action_at
        changed = True
    if lead.lead_owner_user_id is None:
        fallback = _default_owner_user(db)
        if fallback is not None:
            lead.lead_owner_user_id = fallback.id
            changed = True
    if changed:
        db.add(lead)


def transition_lead_stage(
    db: Session,
    *,
    lead: DBLead,
    to_stage: str,
    actor: str,
    reason: str | None = None,
    source: str = "manual",
    sync_legacy: bool = True,
) -> dict[str, Any]:
    next_stage = normalize_stage(to_stage)
    previous_stage = canonical_from_lead(lead)
    now = datetime.utcnow()
    if previous_stage == next_stage:
        event = _create_stage_event(
            db,
            entity_type="lead",
            entity_id=lead.id,
            from_stage=previous_stage,
            to_stage=next_stage,
            reason=reason or "no_change",
            actor=actor,
            source=source,
            metadata={"noop": True},
        )
        db.commit()
        db.refresh(event)
        return serialize_stage_event(event)

    lead.stage_canonical = next_stage
    lead.stage_entered_at = now
    lead.sla_due_at, lead.next_action_at = _stage_deadline(next_stage, now)
    lead.handoff_required = next_stage in {"won", "post_sale"}
    if next_stage == "post_sale":
        lead.handoff_completed_at = now

    if sync_legacy:
        lead.status = _legacy_lead_status_from_canonical(next_stage)
        lead.stage = _legacy_lead_stage_from_canonical(next_stage)

    event = _create_stage_event(
        db,
        entity_type="lead",
        entity_id=lead.id,
        from_stage=previous_stage,
        to_stage=next_stage,
        reason=reason,
        actor=actor,
        source=source,
        metadata={"sync_legacy": sync_legacy},
    )

    db.add(lead)
    db.commit()
    db.refresh(event)
    return serialize_stage_event(event)


def transition_opportunity_stage(
    db: Session,
    *,
    opportunity: DBOpportunity,
    to_stage: str,
    actor: str,
    reason: str | None = None,
    source: str = "manual",
) -> dict[str, Any]:
    next_stage = normalize_stage(to_stage)
    previous_stage = canonical_from_opportunity(opportunity)
    now = datetime.utcnow()

    opportunity.stage_canonical = next_stage
    opportunity.stage_entered_at = now
    opportunity.sla_due_at, opportunity.next_action_at = _stage_deadline(next_stage, now)
    opportunity.stage = _opportunity_stage_from_canonical(next_stage)
    opportunity.status = _opportunity_status_from_canonical(next_stage)
    opportunity.handoff_required = next_stage in {"won", "post_sale"}
    if next_stage == "post_sale":
        opportunity.handoff_completed_at = now

    event = _create_stage_event(
        db,
        entity_type="opportunity",
        entity_id=opportunity.id,
        from_stage=previous_stage,
        to_stage=next_stage,
        reason=reason,
        actor=actor,
        source=source,
        metadata={"opportunity_stage": opportunity.stage, "opportunity_status": opportunity.status},
    )

    db.add(opportunity)
    db.commit()
    db.refresh(event)
    return serialize_stage_event(event)


def reassign_lead_owner(
    db: Session,
    *,
    lead: DBLead,
    owner_user: DBAdminUser,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any]:
    previous_owner = lead.lead_owner_user_id
    lead.lead_owner_user_id = owner_user.id
    if lead.next_action_at is None:
        lead.next_action_at = datetime.utcnow() + timedelta(hours=2)
    db.add(lead)
    event = _create_stage_event(
        db,
        entity_type="lead",
        entity_id=lead.id,
        from_stage=canonical_from_lead(lead),
        to_stage=canonical_from_lead(lead),
        reason=reason or "owner_reassigned",
        actor=actor,
        source="assignment",
        metadata={"from_owner_user_id": previous_owner, "to_owner_user_id": owner_user.id},
    )
    db.commit()
    db.refresh(event)
    return {
        "lead_id": lead.id,
        "owner_user_id": owner_user.id,
        "owner_email": owner_user.email,
        "previous_owner_user_id": previous_owner,
        "event": serialize_stage_event(event),
    }


def bulk_assign_tasks(
    db: Session,
    *,
    task_ids: list[str],
    assigned_to: str,
    actor: str,
    reason: str | None = None,
) -> dict[str, Any]:
    cleaned = [task_id.strip() for task_id in task_ids if task_id and task_id.strip()]
    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="task_ids cannot be empty.",
        )
    normalized_assignee = assigned_to.strip()
    if not normalized_assignee:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="assigned_to cannot be empty.",
        )

    rows = db.query(DBTask).filter(DBTask.id.in_(cleaned)).all()
    updated = 0
    for row in rows:
        row.assigned_to = normalized_assignee
        updated += 1
    db.commit()
    return {
        "updated": updated,
        "requested": len(cleaned),
        "assigned_to": normalized_assignee,
        "actor": actor,
        "reason": (reason or "").strip() or None,
    }


def workload_by_owner(db: Session) -> dict[str, Any]:
    now = datetime.utcnow()
    users = db.query(DBAdminUser).order_by(DBAdminUser.email.asc()).all()
    items: list[dict[str, Any]] = []
    for user in users:
        total = (
            db.query(DBLead)
            .filter(DBLead.lead_owner_user_id == user.id)
            .count()
        )
        active = (
            db.query(DBLead)
            .filter(
                DBLead.lead_owner_user_id == user.id,
                func.lower(func.coalesce(DBLead.stage_canonical, "new")).notin_(TERMINAL_STAGES),
            )
            .count()
        )
        overdue_sla = (
            db.query(DBLead)
            .filter(
                DBLead.lead_owner_user_id == user.id,
                DBLead.sla_due_at.isnot(None),
                DBLead.sla_due_at < now,
                func.lower(func.coalesce(DBLead.stage_canonical, "new")).notin_(TERMINAL_STAGES),
            )
            .count()
        )
        items.append(
            {
                "user_id": user.id,
                "email": user.email,
                "display_name": user.display_name or user.email,
                "status": user.status,
                "lead_count_total": int(total),
                "lead_count_active": int(active),
                "overdue_sla_count": int(overdue_sla),
            }
        )

    unassigned_active = (
        db.query(DBLead)
        .filter(
            DBLead.lead_owner_user_id.is_(None),
            func.lower(func.coalesce(DBLead.stage_canonical, "new")).notin_(TERMINAL_STAGES),
        )
        .count()
    )
    items.sort(key=lambda item: (item["overdue_sla_count"], item["lead_count_active"]), reverse=True)
    return {
        "generated_at": now.isoformat(),
        "items": items,
        "unassigned_active_leads": int(unassigned_active),
    }


def _seed_recommendations(db: Session) -> int:
    now = datetime.utcnow()
    created = 0

    overdue_leads = (
        db.query(DBLead)
        .filter(
            DBLead.sla_due_at.isnot(None),
            DBLead.sla_due_at < now,
            func.lower(func.coalesce(DBLead.stage_canonical, "new")).notin_(TERMINAL_STAGES),
        )
        .limit(100)
        .all()
    )
    for lead in overdue_leads:
        exists = (
            db.query(DBSmartRecommendation)
            .filter(
                DBSmartRecommendation.entity_type == "lead",
                DBSmartRecommendation.entity_id == lead.id,
                DBSmartRecommendation.recommendation_type == "sla_followup",
                DBSmartRecommendation.status == "pending",
            )
            .first()
        )
        if exists:
            continue
        db.add(
            DBSmartRecommendation(
                id=str(uuid.uuid4()),
                entity_type="lead",
                entity_id=lead.id,
                recommendation_type="sla_followup",
                priority=90,
                payload_json={
                    "title": "SLA depasse",
                    "lead_id": lead.id,
                    "stage_canonical": canonical_from_lead(lead),
                    "owner_user_id": lead.lead_owner_user_id,
                },
                requires_confirm=False,
            )
        )
        created += 1

    unowned_qualified = (
        db.query(DBLead)
        .filter(
            DBLead.lead_owner_user_id.is_(None),
            func.lower(func.coalesce(DBLead.stage_canonical, "new")).in_(["qualified", "contacted", "engaged"]),
        )
        .limit(100)
        .all()
    )
    for lead in unowned_qualified:
        exists = (
            db.query(DBSmartRecommendation)
            .filter(
                DBSmartRecommendation.entity_type == "lead",
                DBSmartRecommendation.entity_id == lead.id,
                DBSmartRecommendation.recommendation_type == "assign_owner",
                DBSmartRecommendation.status == "pending",
            )
            .first()
        )
        if exists:
            continue
        db.add(
            DBSmartRecommendation(
                id=str(uuid.uuid4()),
                entity_type="lead",
                entity_id=lead.id,
                recommendation_type="assign_owner",
                priority=80,
                payload_json={"lead_id": lead.id, "stage_canonical": canonical_from_lead(lead)},
                requires_confirm=True,
            )
        )
        created += 1

    won_without_handoff = (
        db.query(DBLead)
        .filter(
            func.lower(func.coalesce(DBLead.stage_canonical, "new")) == "won",
            DBLead.handoff_required.is_(True),
            DBLead.handoff_completed_at.is_(None),
        )
        .limit(100)
        .all()
    )
    for lead in won_without_handoff:
        exists = (
            db.query(DBSmartRecommendation)
            .filter(
                DBSmartRecommendation.entity_type == "lead",
                DBSmartRecommendation.entity_id == lead.id,
                DBSmartRecommendation.recommendation_type == "create_handoff",
                DBSmartRecommendation.status == "pending",
            )
            .first()
        )
        if exists:
            continue
        db.add(
            DBSmartRecommendation(
                id=str(uuid.uuid4()),
                entity_type="lead",
                entity_id=lead.id,
                recommendation_type="create_handoff",
                priority=95,
                payload_json={"lead_id": lead.id},
                requires_confirm=True,
            )
        )
        created += 1

    if created > 0:
        db.commit()
    return created


def serialize_recommendation(row: DBSmartRecommendation) -> dict[str, Any]:
    return {
        "id": row.id,
        "entity_type": row.entity_type,
        "entity_id": row.entity_id,
        "recommendation_type": row.recommendation_type,
        "priority": int(row.priority or 0),
        "payload": row.payload_json or {},
        "status": row.status,
        "requires_confirm": bool(row.requires_confirm),
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "resolved_at": row.resolved_at.isoformat() if row.resolved_at else None,
    }


def list_recommendations(
    db: Session,
    *,
    status_filter: str = "pending",
    limit: int = 50,
    offset: int = 0,
    seed: bool = True,
) -> dict[str, Any]:
    if seed:
        _seed_recommendations(db)
    query = db.query(DBSmartRecommendation)
    if status_filter and status_filter.strip():
        query = query.filter(DBSmartRecommendation.status == status_filter.strip().lower())
    total = query.count()
    rows = (
        query.order_by(DBSmartRecommendation.priority.desc(), DBSmartRecommendation.created_at.desc())
        .offset(max(0, offset))
        .limit(max(1, min(limit, 200)))
        .all()
    )
    return {
        "total": total,
        "items": [serialize_recommendation(row) for row in rows],
    }


def apply_recommendation(db: Session, *, recommendation_id: str, actor: str) -> dict[str, Any]:
    row = db.query(DBSmartRecommendation).filter(DBSmartRecommendation.id == recommendation_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found.")
    if row.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Recommendation is already {row.status}.",
        )

    payload = dict(row.payload_json or {})
    action_result: dict[str, Any] = {"applied": False}
    now = datetime.utcnow()

    if row.recommendation_type == "assign_owner":
        lead = db.query(DBLead).filter(DBLead.id == row.entity_id).first()
        if lead:
            owner = _default_owner_user(db)
            if owner:
                lead.lead_owner_user_id = owner.id
                action_result = {"applied": True, "owner_user_id": owner.id, "owner_email": owner.email}
    elif row.recommendation_type == "sla_followup":
        lead = db.query(DBLead).filter(DBLead.id == row.entity_id).first()
        if lead:
            lead.next_action_at = now
            task = DBTask(
                id=str(uuid.uuid4()),
                title=f"Relance SLA - {lead.email}",
                status="To Do",
                priority="High",
                assigned_to=lead.lead_owner_user_id or "Vous",
                lead_id=lead.id,
                source="auto-rule",
                channel="email",
                sequence_step=1,
                score_snapshot_json={"trigger": "sla_followup"},
            )
            db.add(task)
            action_result = {"applied": True, "task_id": task.id}
    elif row.recommendation_type == "create_handoff":
        lead = db.query(DBLead).filter(DBLead.id == row.entity_id).first()
        if lead:
            lead.handoff_required = True
            action_result = {"applied": True, "handoff_required": True}
    else:
        action_result = {"applied": False, "reason": "unsupported_recommendation_type"}

    row.status = "applied"
    row.resolved_at = now
    row.payload_json = {**payload, "result": action_result, "applied_by": actor}
    db.commit()
    return {"recommendation": serialize_recommendation(row), "result": action_result}


def dismiss_recommendation(db: Session, *, recommendation_id: str, actor: str) -> dict[str, Any]:
    row = db.query(DBSmartRecommendation).filter(DBSmartRecommendation.id == recommendation_id).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found.")
    if row.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Recommendation is already {row.status}.",
        )
    row.status = "dismissed"
    row.resolved_at = datetime.utcnow()
    row.payload_json = {**(row.payload_json or {}), "dismissed_by": actor}
    db.commit()
    return {"recommendation": serialize_recommendation(row)}


def create_handoff(
    db: Session,
    *,
    lead: DBLead | None = None,
    opportunity: DBOpportunity | None = None,
    to_user: DBAdminUser | None = None,
    actor: str,
    note: str | None = None,
) -> dict[str, Any]:
    if lead is None and opportunity is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="lead or opportunity is required for handoff.",
        )
    now = datetime.utcnow()
    metadata: dict[str, Any] = {"note": (note or "").strip() or None}
    if to_user is not None:
        metadata["to_user_id"] = to_user.id
        metadata["to_user_email"] = to_user.email

    entity_type = "lead"
    entity_id = ""

    if lead is not None:
        lead.handoff_required = True
        lead.handoff_completed_at = now
        if to_user is not None:
            lead.lead_owner_user_id = to_user.id
        db.add(lead)
        entity_type = "lead"
        entity_id = lead.id

    if opportunity is not None:
        opportunity.handoff_required = True
        opportunity.handoff_completed_at = now
        if to_user is not None:
            opportunity.owner_user_id = to_user.id
        db.add(opportunity)
        entity_type = "opportunity"
        entity_id = opportunity.id

    event = _create_stage_event(
        db,
        entity_type=entity_type,
        entity_id=entity_id,
        from_stage="won",
        to_stage="post_sale",
        reason="handoff_completed",
        actor=actor,
        source="handoff",
        metadata=metadata,
    )
    db.commit()
    db.refresh(event)
    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "to_user": {
            "id": to_user.id,
            "email": to_user.email,
            "display_name": to_user.display_name,
        }
        if to_user
        else None,
        "event": serialize_stage_event(event),
    }


def conversion_funnel_summary(db: Session, *, days: int = 30) -> dict[str, Any]:
    window_days = max(1, min(int(days), 365))
    now = datetime.utcnow()
    start_at = now - timedelta(days=window_days)

    rows = (
        db.query(DBLead.stage_canonical, func.count(DBLead.id))
        .group_by(DBLead.stage_canonical)
        .all()
    )
    current_counts = {str(stage or "new").lower(): int(count) for stage, count in rows}

    event_rows = (
        db.query(DBStageEvent.to_stage, func.count(DBStageEvent.id))
        .filter(DBStageEvent.created_at >= start_at)
        .group_by(DBStageEvent.to_stage)
        .all()
    )
    event_counts = {str(stage or "").lower(): int(count) for stage, count in event_rows}

    stages = list(CANONICAL_STAGES)
    items: list[dict[str, Any]] = []
    previous_stage_count = None
    for stage in stages:
        count = int(current_counts.get(stage, 0))
        stage_events = int(event_counts.get(stage, 0))
        if previous_stage_count is None:
            rate = 100.0 if count > 0 else 0.0
        else:
            rate = round((count / previous_stage_count) * 100.0, 2) if previous_stage_count > 0 else 0.0
        items.append(
            {
                "stage": stage,
                "lead_count": count,
                "entries_in_window": stage_events,
                "conversion_from_previous_percent": rate,
            }
        )
        previous_stage_count = max(1, count)

    won_count = int(current_counts.get("won", 0))
    post_sale_count = int(current_counts.get("post_sale", 0))
    loss_count = int(current_counts.get("lost", 0))
    disqualified_count = int(current_counts.get("disqualified", 0))
    return {
        "window_days": window_days,
        "from": start_at.isoformat(),
        "to": now.isoformat(),
        "items": items,
        "totals": {
            "won": won_count,
            "post_sale": post_sale_count,
            "lost": loss_count,
            "disqualified": disqualified_count,
        },
    }
