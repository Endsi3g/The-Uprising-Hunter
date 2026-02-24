from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field, EmailStr
from ..dependencies import AUTO_TASK_DEFAULT_CHANNELS

class AdminLeadCreateRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr | None = None
    phone: str | None = None
    company_name: str
    status: str | None = None
    segment: str | None = None

class AdminLeadUpdateRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    title: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    status: str | None = None
    segment: str | None = None
    tags: list[str] | None = None
    company_name: str | None = None
    company_domain: str | None = None
    company_industry: str | None = None
    company_location: str | None = None

class AdminLeadOpportunityCreateRequest(BaseModel):
    name: str = Field(min_length=2)
    stage: str | None = None
    status: str | None = None
    amount: float | None = Field(default=None, ge=0)
    probability: int | None = Field(default=None, ge=0, le=100)
    expected_close_date: str | None = None
    details: dict[str, Any] | None = None

class AdminLeadOpportunityUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2)
    stage: str | None = None
    status: str | None = None
    amount: float | None = Field(default=None, ge=0)
    probability: int | None = Field(default=None, ge=0, le=100)
    expected_close_date: str | None = None
    details: dict[str, Any] | None = None

class AdminLeadNoteItemPayload(BaseModel):
    id: str | None = None
    content: str = Field(min_length=1)
    author: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

class AdminLeadNotesUpdateRequest(BaseModel):
    items: list[AdminLeadNoteItemPayload] = Field(default_factory=list)

class AdminLeadAddToCampaignRequest(BaseModel):
    campaign_id: str = Field(min_length=1)

class AdminLeadAutoTaskCreateRequest(BaseModel):
    channels: list[str] = Field(default_factory=lambda: list(AUTO_TASK_DEFAULT_CHANNELS))
    mode: str = "append"
    dry_run: bool = False
    assigned_to: str | None = None

class AdminLeadStageTransitionRequest(BaseModel):
    to_stage: str = Field(min_length=2)
    reason: str | None = None
    source: str = "manual"
    sync_legacy: bool = True

class AdminLeadReassignRequest(BaseModel):
    owner_user_id: str | None = None
    owner_email: EmailStr | None = None
    owner_display_name: str | None = None
    reason: str | None = None

class LeadCaptureRequest(BaseModel):
    email: EmailStr | None = None
    first_name: str | None = None
    last_name: str | None = None
    company_name: str | None = None
    phone: str | None = None
    message: str | None = None
    source: str = "web_form"

class AdminBulkDeleteRequest(BaseModel):
    ids: list[str] = Field(default_factory=list)
    segment: str | None = None
