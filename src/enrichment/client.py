from abc import ABC, abstractmethod
from typing import List, Dict, Any

import requests

from ..core.http import HttpRequestConfig, request_json
from ..core.logging import get_logger
from ..core.models import Lead, Company, LeadStatus


logger = get_logger(__name__)

class SourcingClient(ABC):
    @abstractmethod
    def search_leads(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def enrich_company(self, company_domain: str) -> Dict[str, Any]:
        pass

class ApolloClient(SourcingClient):
    """
    Real implementation of Apollo.io API client.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.apollo.io/v1"
        self.request_config = HttpRequestConfig(timeout=12.0, max_retries=3)
        self.headers = {
            "Content-Type": "application/json",
            "Cache-Control": "no-cache"
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def search_leads(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/mixed_people/search"
        
        # Map generic criteria to Apollo-specific payload
        payload = {
            "api_key": self.api_key,
            "q_organization_domains": criteria.get("company_domains"),
            "person_titles": [criteria.get("role")] if criteria.get("role") else [],
            "person_locations": [criteria.get("location")] if criteria.get("location") else [],
            "organization_num_employees_ranges": criteria.get("size_ranges"),
            "page": 1,
            "per_page": max(1, min(int(criteria.get("limit", 10)), 100))
        }
        
        try:
            data = request_json(
                self.session,
                "POST",
                url,
                config=self.request_config,
                json=payload,
            )
            
            leads = []
            for person in data.get("people", []):
                # Normalize data structure
                leads.append({
                    "first_name": person.get("first_name"),
                    "last_name": person.get("last_name"),
                    "email": person.get("email"),
                    "title": person.get("title"),
                    "linkedin_url": person.get("linkedin_url"),
                    "company_name": person.get("organization", {}).get("name"),
                    "company_domain": person.get("organization", {}).get("primary_domain"),
                    "location": person.get("city") or person.get("state") or person.get("country"),
                    "phone": person.get("phone_numbers", [{}])[0].get("raw_number") if person.get("phone_numbers") else None
                })
            return leads
            
        except (requests.RequestException, ValueError, TypeError) as exc:
            logger.warning(
                "Apollo search failed.",
                extra={
                    "error": str(exc),
                    "role": criteria.get("role"),
                    "location": criteria.get("location"),
                },
            )
            return []

    def enrich_company(self, company_domain: str) -> Dict[str, Any]:
        url = f"{self.base_url}/organizations/enrich"
        params = {
            "api_key": self.api_key,
            "domain": company_domain
        }
        
        try:
            body = request_json(
                self.session,
                "GET",
                url,
                config=self.request_config,
                params=params,
            )
            data = body.get("organization", {})
            
            loc_parts = [data.get('city'), data.get('country')]
            location = ", ".join([str(p) for p in loc_parts if p])
            return {
                "name": data.get("name"),
                "industry": data.get("industry"),
                "size_range": data.get("estimated_num_employees"),
                "revenue_range": data.get("annual_revenue_printed"),
                "tech_stack": [t.get("name") for t in data.get("keywords", [])[:10]], 
                "description": data.get("short_description"),
                "linkedin_url": data.get("linkedin_url"),
                "location": location
            }
        except (requests.RequestException, ValueError, TypeError) as exc:
            logger.warning(
                "Apollo company enrichment failed.",
                extra={
                    "company_domain": company_domain,
                    "error": str(exc),
                },
            )
            return {"name": "Unknown", "domain": company_domain}

class MockApolloClient(SourcingClient):
    """
    Simulates interactions with Apollo.io API.
    Returns dummy data for testing purposes.
    """
    def search_leads(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Simulation of API response
        logger.info("Using mock Apollo search.", extra={"criteria": criteria})
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
        logger.info("Using mock company enrichment.", extra={"company_domain": company_domain})
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
