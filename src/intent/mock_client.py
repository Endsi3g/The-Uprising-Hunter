from __future__ import annotations

import hashlib
from typing import Optional

from .base import IntentPayload, IntentProviderClient
from .mapping import normalize_intent_payload


class MockIntentProviderClient(IntentProviderClient):
    provider_name = "mock"

    def fetch_company_intent(
        self,
        company_name: Optional[str],
        company_domain: Optional[str],
    ) -> IntentPayload:
        seed = f"{company_name or ''}:{company_domain or ''}".encode("utf-8")
        digest = hashlib.sha256(seed).hexdigest()
        score = int(digest[:2], 16)  # 0-255
        normalized_score = round((score / 255) * 100, 2)

        if normalized_score >= 70:
            level = "high"
        elif normalized_score >= 40:
            level = "medium"
        else:
            level = "low"

        mock_payload = {
            "intent_level": level,
            "surge_score": normalized_score,
            "topic_count": (score % 5) + 1,
            "topics": ["automation", "ai", "operations"][: ((score % 3) + 1)],
            "confidence": 0.8,
        }
        return normalize_intent_payload(self.provider_name, mock_payload)

