from __future__ import annotations

from typing import Annotated, Any
from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Path
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, text

from ...core.database import get_db
from ...core.db_models import (
    DBLead, DBInteraction, DBOpportunity, DBTask, DBProject, 
    DBCampaign, DBAdminUser, DBAdminUserRole
)
from ...core.models import Lead, LeadStatus, LeadStage, Interaction
from ...core.logging import get_logger

from ..dependencies import require_admin, require_rate_limit
from ..schemas.leads import (
    AdminLeadCreateRequest, AdminLeadUpdateRequest,
    AdminLeadOpportunityCreateRequest, AdminLeadOpportunityUpdateRequest,
    AdminLeadNoteItemPayload, AdminLeadNotesUpdateRequest,
    AdminLeadAddToCampaignRequest, AdminLeadAutoTaskCreateRequest,
    AdminLeadStageTransitionRequest, AdminLeadReassignRequest,
    AdminBulkDeleteRequest
)

from .. import campaign_service as _campaign_svc
from .. import funnel_service as _funnel_svc
from ..stats_service import list_leads
from ..scoring.engine import ScoringEngine
from ..ai_engine.generator import MessageGenerator

logger = get_logger(__name__)
scoring_engine = ScoringEngine()
message_generator = MessageGenerator()

router = APIRouter(
    prefix="/leads",
    tags=["Leads"],
    dependencies=[Depends(require_admin), Depends(require_rate_limit)],
)
