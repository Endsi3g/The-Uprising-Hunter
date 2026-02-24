from __future__ import annotations

from typing import Any
from datetime import date
from pydantic import BaseModel, Field, EmailStr, model_validator
from ..dependencies import AUTO_TASK_DEFAULT_CHANNELS

class AdminLeadCreateRequest(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: EmailStr | None = None
    phone: str | None = None
    company_name: str = Field(min_length=1)
    status: str | None = None
    segment: str | None = None

class AdminLeadUpdateRequest(BaseModel):
    first_name: str | None = Field(default=None, min_length=1)
    last_name: str | None = Field(default=None, min_length=1)
    email: EmailStr | None = None
    title: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    status: str | None = None
    segment: str | None = None
    tags: list[str] | None = None
    company_name: str | None = Field(default=None, min_length=1)
    company_domain: str | None = None
    company_industry: str | None = None
    company_location: str | None = None

class AdminLeadOpportunityCreateRequest(BaseModel):
    name: str = Field(min_length=2)
    stage: str | None = None
    status: str | None = None
    amount: float | None = Field(default=None, ge=0)
    probability: int | None = Field(default=None, ge=0, le=100)
    expected_close_date: date | None = None
    details: dict[str, Any] | None = None

class AdminLeadOpportunityUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2)
    stage: str | None = None
    status: str | None = None
    amount: float | None = Field(default=None, ge=0)
    probability: int | None = Field(default=None, ge=0, le=100)
    expected_close_date: date | None = None
    details: dict[str, Any] | None = None

class AdminLeadNoteItemPayload(BaseModel):
    id: str | None = None
    content: str = Field(min_length=1)
    author: str | None = None

class AdminLeadNotesUpdateRequest(BaseModel):
    items: list[AdminLeadNoteItemPayload] = Field(..., min_length=1)

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
    owner_user_id: str | None = Field(default=None, min_length=1)
    owner_email: EmailStr | None = None
    owner_display_name: str | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def validate_owner_identifier(self) -> "AdminLeadReassignRequest":
        if self.owner_user_id is None and self.owner_email is None:
            raise ValueError("Either owner_user_id or owner_email must be provided")
        return self

class LeadCaptureRequest(BaseModel):
    email: EmailStr | None = None
    first_name: str | None = Field(default=None, min_length=1)
    last_name: str | None = Field(default=None, min_length=1)
    company_name: str | None = None
    phone: str | None = None
    message: str | None = None
    source: str = "web_form"

    @model_validator(mode="after")
    def validate_identifying_info(self) -> "LeadCaptureRequest":
        if self.email is None and self.first_name is None and self.last_name is None:
            raise ValueError("Lead capture must include email, first_name, or last_name")
        return self

class AdminBulkDeleteRequest(BaseModel):
    ids: list[Annotated[str, Field(min_length=1)]] = Field(default_factory=list)
    segment: str | None = None

    @model_validator(mode="after")
    def validate_selection(self) -> "AdminBulkDeleteRequest":
        if not self.ids and not self.segment:
            raise ValueError("Bulk delete must specify either 'ids' or a 'segment'")
        return self
