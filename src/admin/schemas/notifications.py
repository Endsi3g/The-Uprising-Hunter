from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field

class AdminNotificationCreateRequest(BaseModel):
    event_key: str = Field(min_length=3)
    title: str = Field(min_length=3)
    message: str = Field(min_length=3)
    channel: str = "in_app"
    entity_type: str | None = None
    entity_id: str | None = None
    link_href: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class AdminNotificationMarkReadRequest(BaseModel):
    ids: list[str] = Field(default_factory=list)

class AdminNotificationPreferencesUpdatePayload(BaseModel):
    channels: dict[str, dict[str, bool]] = Field(default_factory=dict)
