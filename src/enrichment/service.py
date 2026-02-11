from typing import List
from ..core.models import Lead, Company
from .client import SourcingClient
import uuid

class EnrichmentService:
    def __init__(self, client: SourcingClient):
        self.client = client

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
        lead_id = email if email else str(uuid.uuid4())

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
            except Exception as e:
                print(f"Error formatting lead {raw.get('company_name')}: {e}")
            
        return processed_leads
