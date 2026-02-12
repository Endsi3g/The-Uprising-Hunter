from typing import List, Optional
from uuid import uuid4

from ..core.logging import get_logger
from ..core.models import Lead, Company
from .client import SourcingClient
from ..intent.base import IntentProviderClient


logger = get_logger(__name__)

class EnrichmentService:
    def __init__(self, client: SourcingClient, intent_client: Optional[IntentProviderClient] = None):
        self.client = client
        self.intent_client = intent_client

    def enrich_intent(self, lead: Lead) -> None:
        if not self.intent_client:
            return

        intent_data = self.intent_client.fetch_company_intent(
            company_name=lead.company.name,
            company_domain=lead.company.domain,
        )
        if not intent_data:
            return

        lead.details["intent"] = intent_data
        lead.details["intent_provider"] = intent_data.get("provider", self.intent_client.provider_name)

    def format_lead(self, raw_data: dict) -> Lead:
        """
        Converts raw API data into our standardized Lead model.
        """
        # First, enrich company data if domain is present
        company_data = {"name": raw_data.get("company_name", "Unknown")}
        domain = raw_data.get("company_domain")
        
        if domain:
            enriched_company = self.client.enrich_company(domain)
            company_data.update(enriched_company)
        
        company = Company(**company_data)

        # Create Lead object
        # Generate a UUID if email is missing, though we prefer email as ID.
        email = raw_data.get("email")
        lead_id = email if email else str(uuid4())

        lead = Lead(
            id=lead_id,
            first_name=raw_data.get("first_name", "Unknown"),
            last_name=raw_data.get("last_name", ""),
            email=email if email else f"no-email-{lead_id}@placeholder.com", # Placeholder if missing
            title=raw_data.get("title"),
            linkedin_url=raw_data.get("linkedin_url"),
            company=company,
            phone=raw_data.get("phone")
        )

        if isinstance(raw_data.get("details"), dict):
            lead.details.update(raw_data["details"])
        for key in ("source", "website", "location"):
            if key in raw_data and raw_data[key] is not None:
                lead.details[key] = raw_data[key]

        self.enrich_intent(lead)
        
        return lead

    def source_and_enrich(self, criteria: dict) -> List[Lead]:
        """
        Full workflow: Search -> Enrich -> Standardize
        """
        raw_leads = self.client.search_leads(criteria)
        processed_leads = []
        
        for raw in raw_leads:
            try:
                lead = self.format_lead(raw)
                processed_leads.append(lead)
            except (TypeError, ValueError) as exc:
                logger.warning(
                    "Failed to normalize raw lead payload.",
                    extra={"company_name": raw.get("company_name"), "error": str(exc)},
                )
            
        return processed_leads
