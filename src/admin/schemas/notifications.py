from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator, TypeAdapter

class AdminNotificationCreateRequest(BaseModel):
    event_key: str = Field(min_length=3)
    title: str = Field(min_length=3)
    message: str = Field(min_length=3)
    channel: str = "in_app"
    entity_type: str | None = None
    entity_id: str | None = None
    link_href: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("link_href")
    @classmethod
    def validate_link_href(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        # Validate as HttpUrl but return string
        try:
            TypeAdapter(HttpUrl).validate_python(v)
        except Exception as exc:
            raise ValueError(f"Invalid URL format for link_href: {str(exc)}")
        return v

class AdminNotificationMarkReadRequest(BaseModel):
    ids: list[str] = Field(default_factory=list)

class AdminNotificationPreferencesUpdatePayload(BaseModel):
    channels: dict[str, dict[str, bool]] = Field(default_factory=dict)
