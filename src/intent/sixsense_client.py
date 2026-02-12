from __future__ import annotations

from typing import Optional

import requests

from ..core.http import HttpRequestConfig, request_json
from ..core.logging import get_logger
from .base import IntentPayload, IntentProviderClient
from .mapping import normalize_intent_payload


logger = get_logger(__name__)


class SixSenseIntentClient(IntentProviderClient):
    provider_name = "6sense"

    def __init__(self, api_key: str, base_url: Optional[str] = None, timeout: int = 10):
        self.api_key = api_key
        self.base_url = (base_url or "https://api.6sense.com").rstrip("/")
        self.timeout = timeout
        self.request_config = HttpRequestConfig(timeout=float(timeout))
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            }
        )

    def fetch_company_intent(
        self,
        company_name: Optional[str],
        company_domain: Optional[str],
    ) -> IntentPayload:
        params = {}
        if company_domain:
            params["domain"] = company_domain
        if company_name:
            params["company_name"] = company_name

        if not params:
            return normalize_intent_payload(self.provider_name, {})

        try:
            payload = request_json(
                self.session,
                "GET",
                f"{self.base_url}/intent/account",
                config=self.request_config,
                params=params,
            )
        except requests.RequestException as exc:
            logger.warning(
                "6sense intent request failed.",
                extra={
                    "provider": self.provider_name,
                    "company_domain": company_domain,
                    "company_name": company_name,
                    "error": str(exc),
                },
            )
            payload = {
                "intent_level": "none",
                "intent_score": 0,
                "topic_count": 0,
                "topics": [],
                "confidence": 0,
                "error": str(exc),
            }

        return normalize_intent_payload(self.provider_name, payload)
