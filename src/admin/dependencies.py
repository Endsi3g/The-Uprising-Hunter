from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.database import get_db
import uuid
from ..core.db_models import DBAdminSession, DBAdminUser, DBAuditLog

def _audit_log(
    db: Session,
    *,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    entry = DBAuditLog(
        id=str(uuid.uuid4()),
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=metadata or {},
    )
    db.add(entry)
    db.commit()
from . import secrets_manager as _sec_svc
from . import funnel_service as _funnel_svc

# --- CONSTANTS ---

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "change-me"
DEFAULT_ADMIN_AUTH_MODE = "hybrid"
DEFAULT_ACCESS_TOKEN_TTL_MINUTES = 15
DEFAULT_REFRESH_TOKEN_TTL_DAYS = 7
DEFAULT_AUTH_COOKIE_SECURE = "auto"

ACCESS_TOKEN_COOKIE_NAME = "admin_access_token"
REFRESH_TOKEN_COOKIE_NAME = "admin_refresh_token"
JWT_ALGORITHM = "HS256"
PASSWORD_HASH_ITERATIONS = 260_000

if hasattr(status, "HTTP_422_UNPROCESSABLE_CONTENT"):
    HTTP_422_STATUS = status.HTTP_422_UNPROCESSABLE_CONTENT
else:
    HTTP_422_STATUS = 422

DEFAULT_ADMIN_SETTINGS: dict[str, Any] = {
    "organization_name": "The Uprising Hunter",
    "locale": "fr-FR",
    "timezone": "Europe/Paris",
    "default_page_size": 25,
    "dashboard_refresh_seconds": 30,
    "support_email": "support@example.com",
    "theme": "system",
    "default_refresh_mode": "polling",
    "notifications": {"email": True, "in_app": True},
}

DEFAULT_INTEGRATION_CATALOG: dict[str, dict[str, Any]] = {
    "duckduckgo": {
        "enabled": True,
        "config": {"region": "us-en", "safe_search": "moderate"},
        "meta": {
            "category": "research",
            "free_tier": "Free (no API key required)",
            "description": "Open web search fallback for advanced research.",
        },
    },
    "perplexity": {
        "enabled": False,
        "config": {
            "api_key_env": "PERPLEXITY_API_KEY",
            "model": "sonar",
            "max_tokens": 550,
        },
        "meta": {
            "category": "research",
            "free_tier": "Free trial / free credits available depending on account",
            "description": "AI-powered web research with cited sources.",
        },
    },
    "firecrawl": {
        "enabled": False,
        "config": {
            "api_key_env": "FIRECRAWL_API_KEY",
            "country": "us",
            "lang": "en",
            "formats": ["markdown"],
        },
        "meta": {
            "category": "research",
            "free_tier": "Free tier available",
            "description": "Structured crawl and extraction from live web pages.",
        },
    },
    "ollama": {
        "enabled": False,
        "config": {
            "api_base_url": "",
            "api_key_env": "OLLAMA_API_KEY",
            "model_research": "llama3.1:8b-instruct",
            "model_content": "llama3.1:8b-instruct",
            "model_assistant": "llama3.1:8b-instruct",
            "temperature": 0.2,
            "max_tokens": 700,
            "timeout_seconds": 25,
        },
        "meta": {
            "category": "ai",
            "free_tier": "Open-source self-hosted model runtime",
            "description": "Hosted Ollama instance for online open-source AI inference.",
        },
    },
    "slack": {
        "enabled": False,
        "config": {"webhook": ""},
        "meta": {
            "category": "automation",
            "free_tier": "Free plan available",
            "description": "Send admin alerts and pipeline events to Slack.",
        },
    },
    "zapier": {
        "enabled": False,
        "config": {"zap_id": ""},
        "meta": {
            "category": "automation",
            "free_tier": "Free plan available",
            "description": "Automate admin workflows with no-code triggers.",
        },
    },
}

PROJECT_STATUSES = {"Planning", "In Progress", "On Hold", "Completed", "Cancelled"}
TASK_STATUSES = {"To Do", "In Progress", "Done"}
TASK_PRIORITIES = {"Low", "Medium", "High", "Critical"}
TASK_CHANNELS = {"email", "linkedin", "call"}
TASK_SOURCES = {"manual", "auto-rule", "assistant"}
OPPORTUNITY_STAGES = {
    "qualification",
    "discovery",
    "proposal",
    "negotiation",
    "won",
    "lost",
}
OPPORTUNITY_STATUSES = {"open", "won", "lost"}
OPPORTUNITY_PIPELINE_STAGES = ("Prospect", "Qualified", "Proposed", "Won", "Lost")
OPPORTUNITY_PIPELINE_STAGE_SET = set(OPPORTUNITY_PIPELINE_STAGES)
AUTO_TASK_DEFAULT_CHANNELS = ["email", "linkedin", "call"]
USER_STATUSES = {"active", "invited", "disabled"}
THEME_OPTIONS = {"light", "dark", "system"}
REFRESH_MODES = {"manual", "polling"}
ROLE_LABELS = {
    "admin": "Administrateur",
    "manager": "Manager",
    "sales": "Commercial",
}
NOTIFICATION_CHANNELS = {"email", "in_app"}
NOTIFICATION_EVENT_KEYS = {
    "lead_created",
    "lead_updated",
    "task_created",
    "task_completed",
    "project_created",
    "report_ready",
    "report_failed",
    "billing_invoice_due",
    "assistant_run_completed",
}
REPORT_FREQUENCIES = {"daily", "weekly", "monthly"}
REPORT_FORMATS = {"pdf", "csv"}
SYNC_STALE_WARNING_SECONDS = 5 * 60
SYNC_STALE_ERROR_SECONDS = 30 * 60
INTEGRITY_STALE_UNSCORED_DAYS = 14
FUNNEL_CONFIG_SETTING_KEY = "funnel_config"
DEFAULT_FUNNEL_CONFIG: dict[str, Any] = {
    "stages": list(_funnel_svc.CANONICAL_STAGES),
    "terminal_stages": sorted(list(_funnel_svc.TERMINAL_STAGES)),
    "stage_sla_hours": dict(_funnel_svc.STAGE_SLA_HOURS),
    "next_action_hours": dict(_funnel_svc.NEXT_ACTION_HOURS),
    "model": "canonical_v1",
}


# Standard Error Codes
ERR_AUTH_INVALID = "AUTH_001"
ERR_AUTH_EXPIRED = "AUTH_002"
ERR_AUTH_FORBIDDEN = "AUTH_003"
ERR_VALIDATION_FAILED = "VALIDATION_001"
ERR_RESOURCE_NOT_FOUND = "NOT_FOUND_001"
ERR_RESOURCE_CONFLICT = "CONFLICT_001"
ERR_SERVER_INTERNAL = "SERVER_001"
ERR_DB_ERROR = "DB_001"
ERR_RATE_LIMIT = "RATE_001"


# --- RATE LIMITER ---

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


class InMemoryRequestMetrics:
    _DYNAMIC_SEGMENT_RE = None  # Lazy-compiled regex

    def __init__(self) -> None:
        self._lock = Lock()
        self._total_requests = 0
        self._total_errors = 0
        self._all_latencies_ms: list[float] = []
        self._by_endpoint: dict[str, dict[str, Any]] = {}
        self._max_samples_per_endpoint = 512
        self._max_global_samples = 4096
        self._max_endpoints = 1024

    @classmethod
    def _normalize_path(cls, path: str) -> str:
        """Replace dynamic path segments (UUIDs, numeric IDs) with placeholders."""
        import re
        if cls._DYNAMIC_SEGMENT_RE is None:
            cls._DYNAMIC_SEGMENT_RE = re.compile(
                r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
                r"|/\d+",
                re.IGNORECASE,
            )
        return cls._DYNAMIC_SEGMENT_RE.sub("/:id", path)

    def observe(self, *, path: str, status_code: int, latency_ms: float) -> None:
        endpoint = self._normalize_path(path) if path else "unknown"
        is_error = status_code >= 400
        with self._lock:
            self._total_requests += 1
            if is_error:
                self._total_errors += 1

            self._all_latencies_ms.append(latency_ms)
            if len(self._all_latencies_ms) > self._max_global_samples:
                self._all_latencies_ms = self._all_latencies_ms[-self._max_global_samples :]

            bucket = self._by_endpoint.get(endpoint)
            if not bucket:
                # Evict least-used endpoint if at capacity
                if len(self._by_endpoint) >= self._max_endpoints:
                    victim = min(self._by_endpoint, key=lambda k: self._by_endpoint[k]["request_count"])
                    del self._by_endpoint[victim]
                bucket = {
                    "request_count": 0,
                    "error_count": 0,
                    "latencies_ms": [],
                }
                self._by_endpoint[endpoint] = bucket

            bucket["request_count"] += 1
            if is_error:
                bucket["error_count"] += 1
            bucket["latencies_ms"].append(latency_ms)
            if len(bucket["latencies_ms"]) > self._max_samples_per_endpoint:
                bucket["latencies_ms"] = bucket["latencies_ms"][-self._max_samples_per_endpoint :]

    @staticmethod
    def _p95(values: list[float]) -> float:
        if not values:
            return 0.0
        ordered = sorted(values)
        index = max(0, min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1)))))
        return round(float(ordered[index]), 2)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            total = self._total_requests
            errors = self._total_errors
            global_latencies = list(self._all_latencies_ms)
            endpoints_payload: list[dict[str, Any]] = []
            for path, bucket in self._by_endpoint.items():
                request_count = int(bucket["request_count"])
                error_count = int(bucket["error_count"])
                latencies = list(bucket["latencies_ms"])
                endpoints_payload.append(
                    {
                        "path": path,
                        "request_count": request_count,
                        "error_rate": round((error_count / request_count) * 100, 2) if request_count else 0.0,
                        "p95_ms": self._p95(latencies),
                    }
                )

        endpoints_payload.sort(key=lambda item: item["request_count"], reverse=True)
        return {
            "request_count": total,
            "error_rate": round((errors / total) * 100, 2) if total else 0.0,
            "p95_ms": self._p95(global_latencies),
            "endpoints": endpoints_payload[:50],
        }

rate_limiter = InMemoryRateLimiter()

# --- AUTH HELPERS ---

def _get_admin_auth_mode() -> str:
    mode = os.getenv("ADMIN_AUTH_MODE", DEFAULT_ADMIN_AUTH_MODE).strip().lower()
    if mode in {"jwt", "hybrid", "basic"}:
        return mode
    return DEFAULT_ADMIN_AUTH_MODE

def _default_jwt_secret() -> str:
    return "dev-jwt-secret-change-me"

def _get_jwt_secret() -> str:
    return _sec_svc.secrets_manager.resolve_secret(None, "JWT_SECRET", _default_jwt_secret())

def _get_access_token_ttl_minutes() -> int:
    raw = os.getenv("JWT_ACCESS_TTL_MINUTES", str(DEFAULT_ACCESS_TOKEN_TTL_MINUTES))
    try:
        return max(1, min(int(raw), 1440))
    except ValueError:
        return DEFAULT_ACCESS_TOKEN_TTL_MINUTES

def _get_refresh_token_ttl_days() -> int:
    raw = os.getenv("JWT_REFRESH_TTL_DAYS", str(DEFAULT_REFRESH_TOKEN_TTL_DAYS))
    try:
        return max(1, min(int(raw), 30))
    except ValueError:
        return DEFAULT_REFRESH_TOKEN_TTL_DAYS

def _get_expected_admin_credentials() -> tuple[str, str]:
    expected_username = os.getenv("ADMIN_USERNAME", DEFAULT_ADMIN_USERNAME)
    expected_password = os.getenv("ADMIN_PASSWORD", DEFAULT_ADMIN_PASSWORD)
    return expected_username, expected_password

def _is_valid_admin_credentials(username: str, password: str) -> bool:
    expected_username, expected_password = _get_expected_admin_credentials()
    return (
        hmac.compare_digest(username, expected_username)
        and hmac.compare_digest(password, expected_password)
    )

def _normalize_admin_email(value: str) -> str:
    return value.strip().lower()

def _base64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

def _base64url_decode(raw: str) -> bytes:
    pad = "=" * (4 - (len(raw) % 4))
    return base64.urlsafe_b64decode(raw + pad)

def _hash_admin_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_HASH_ITERATIONS,
    )
    return (
        f"pbkdf2_sha256${PASSWORD_HASH_ITERATIONS}"
        f"${_base64url_encode(salt)}${_base64url_encode(digest)}"
    )

def _verify_admin_password(password: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        return False
    try:
        algorithm, iterations_raw, salt_raw, digest_raw = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_raw)
        if iterations <= 0:
            return False
        salt = _base64url_decode(salt_raw)
        expected_digest = _base64url_decode(digest_raw)
    except Exception:
        return False

    computed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(computed, expected_digest)

def _resolve_db_admin_subject(db: Session, username: str, password: str) -> str | None:
    normalized_email = _normalize_admin_email(username)
    if not normalized_email:
        return None
    user = (
        db.query(DBAdminUser)
        .filter(func.lower(DBAdminUser.email) == normalized_email)
        .first()
    )
    if not user:
        return None
    if user.status != "active":
        return None
    if not _verify_admin_password(password, user.password_hash):
        return None
    return str(user.id)

def _resolve_admin_subject(db: Session, username: str, password: str) -> str | None:
    # 1. Check Env/Hardcoded
    valid_env = _is_valid_admin_credentials(username, password)
    if valid_env:
        return "admin"

    # 2. Check DB
    db_subject = _resolve_db_admin_subject(db, username, password)
    if db_subject:
        return db_subject

    return None

def _extract_basic_credentials(request: Request) -> tuple[str, str] | None:
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("basic "):
        return None
    try:
        encoded = auth_header.split(" ", 1)[1]
        decoded = base64.b64decode(encoded).decode("utf-8")
        username, _, password = decoded.partition(":")
        return username, password
    except Exception:
        return None

def _extract_access_payload(request: Request) -> dict[str, Any] | None:
    import jwt
    token = None
    # 1. Header
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1]
    
    # 2. Cookie
    if not token:
        token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
    
    if not token:
        return None
        
    try:
        secret = _get_jwt_secret()
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.InvalidTokenError:
        return None

def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

# --- DEPENDENCIES ---

def require_admin(request: Request, db: Session = Depends(get_db)) -> str:
    # BYPASS AUTH FOR DEV: Always return "admin"
    # return "admin"
    
    # Actually use the real implementation for correctness in refactor
    # But keep the bypass if it was enabled in the original code? 
    # The original code had:
    # def require_admin(...):
    #    # BYPASS AUTH FOR DEV: Always return "admin"
    #    return "admin"
    #    ... unreachable code ...
    
    # I will keep it as is, but maybe uncomment the real logic if I want to be strict?
    # No, keep it as is to match current behavior.
    return "admin"
    
    # Unreachable implementation preserved for reference/future enablement
    auth_mode = _get_admin_auth_mode()

    payload: dict[str, Any] | None = None
    try:
        payload = _extract_access_payload(request)
    except HTTPException as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.detail,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if payload:
        username = str(payload.get("sub") or "").strip()
        session_id = str(payload.get("sid") or "").strip()
        if not username or not session_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token payload.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        session = db.query(DBAdminSession).filter(DBAdminSession.id == session_id).first()
        if not session or session.revoked_at is not None or session.expires_at <= datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session revoked or expired.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Only persist last_seen_at if stale by 2+ minutes to avoid write-per-request
        _now = datetime.utcnow()
        if not session.last_seen_at or (_now - session.last_seen_at).total_seconds() > 120:
            session.last_seen_at = _now
            db.commit()
        return username

    if auth_mode in {"basic", "hybrid"}:
        credentials = _extract_basic_credentials(request)
        if credentials:
            username, password = credentials
            subject = _resolve_admin_subject(db, username, password)
            if subject:
                return subject
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid admin credentials.",
                headers={"WWW-Authenticate": "Basic"},
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required.",
        headers={"WWW-Authenticate": "Bearer"},
    )

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
