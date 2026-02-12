from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


IntentPayload = Dict[str, Any]


class IntentProviderClient(ABC):
    provider_name: str = "unknown"

    @abstractmethod
    def fetch_company_intent(
        self,
        company_name: Optional[str],
        company_domain: Optional[str],
    ) -> IntentPayload:
        """
        Fetch and normalize intent signals for a company.
        """
        raise NotImplementedError

