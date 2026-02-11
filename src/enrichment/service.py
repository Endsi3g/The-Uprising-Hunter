from typing import List
from ..core.models import Lead, Company
from .client import SourcingClient

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
        lead = Lead(
            id=raw_data.get("email"), # using email as ID for simplicity
            first_name=raw_data.get("first_name"),
            last_name=raw_data.get("last_name"),
            email=raw_data.get("email"),
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
            lead = self.format_lead(raw)
            processed_leads.append(lead)
            
        return processed_leads
