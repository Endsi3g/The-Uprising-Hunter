from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Optional

import requests

from .logging import get_logger


logger = get_logger(__name__)


RETRYABLE_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}


@dataclass
class HttpRequestConfig:
    timeout: float = 10.0
    max_retries: int = 3
    backoff_base_seconds: float = 0.5
    backoff_cap_seconds: float = 4.0


def _sleep_backoff(attempt: int, cfg: HttpRequestConfig) -> None:
    wait = min(cfg.backoff_cap_seconds, cfg.backoff_base_seconds * (2 ** (attempt - 1)))
    time.sleep(wait)


def request_with_retries(
    session: requests.Session,
    method: str,
    url: str,
    *,
    config: Optional[HttpRequestConfig] = None,
    **kwargs: Any,
) -> requests.Response:
    cfg = config or HttpRequestConfig()
    last_exc: Exception | None = None

    for attempt in range(1, cfg.max_retries + 1):
        try:
            response = session.request(method, url, timeout=cfg.timeout, **kwargs)
            if response.status_code in RETRYABLE_STATUS_CODES and attempt < cfg.max_retries:
                logger.warning(
                    "Retryable HTTP status while calling provider.",
                    extra={
                        "http_method": method.upper(),
                        "url": url,
                        "status_code": response.status_code,
                        "attempt": attempt,
                    },
                )
                _sleep_backoff(attempt, cfg)
                continue
            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            last_exc = exc
            if attempt >= cfg.max_retries:
                break
            logger.warning(
                "HTTP request failed, retrying.",
                extra={
                    "http_method": method.upper(),
                    "url": url,
                    "attempt": attempt,
                    "error": str(exc),
                },
            )
            _sleep_backoff(attempt, cfg)

    if last_exc is None:
        raise RuntimeError("HTTP request failed without a captured exception.")
    raise last_exc


def request_json(
    session: requests.Session,
    method: str,
    url: str,
    *,
    config: Optional[HttpRequestConfig] = None,
    **kwargs: Any,
) -> Any:
    response = request_with_retries(
        session,
        method,
        url,
        config=config,
        **kwargs,
    )
    return response.json()
