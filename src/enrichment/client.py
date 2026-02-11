from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..core.models import Lead, Company, LeadStatus

class SourcingClient(ABC):
    @abstractmethod
    def search_leads(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def enrich_company(self, company_domain: str) -> Dict[str, Any]:
        pass

class MockApolloClient(SourcingClient):
    """
    Simulates interactions with Apollo.io API.
    Returns dummy data for testing purposes.
    """
    def search_leads(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Simulation of API response
        print(f"Searching Apollo with criteria: {criteria}")
        return [
            {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@techcorp.com",
                "title": "CTO",
                "linkedin_url": "https://linkedin.com/in/johndoe",
                "company_name": "TechCorp",
                "company_domain": "techcorp.com",
                "location": "San Francisco, CA"
            },
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane.smith@healthplus.com",
                "title": "VP of Engineering",
                "linkedin_url": "https://linkedin.com/in/janesmith",
                "company_name": "HealthPlus",
                "company_domain": "healthplus.com",
                "location": "New York, NY"
            }
        ]

    def enrich_company(self, company_domain: str) -> Dict[str, Any]:
        print(f"Enriching company: {company_domain}")
        # Simulation of company enrichment data
        if company_domain == "techcorp.com":
            return {
                "name": "TechCorp",
                "industry": "Software",
                "size_range": "100-500",
                "revenue_range": "10M-50M",
                "tech_stack": ["AWS", "Python", "React"],
                "description": "Leading provider of AI solutions."
            }
        elif company_domain == "healthplus.com":
            return {
                "name": "HealthPlus",
                "industry": "Healthcare",
                "size_range": "500-1000",
                "revenue_range": "50M-100M",
                "tech_stack": ["Azure", ".NET", "Angular"],
                "description": "Innovative healthcare platform."
            }
        return {"name": "Unknown", "domain": company_domain}
