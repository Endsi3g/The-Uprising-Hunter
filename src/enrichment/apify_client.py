from typing import List, Dict, Any
from apify_client import ApifyClient
from .client import SourcingClient
import os

class ApifyMapsClient(SourcingClient):
    """
    Client for sourcing leads via Apify (Google Maps Scraper).
    """
    def __init__(self, api_token: str):
        self.client = ApifyClient(api_token)
        # Using the Compass Google Maps crawler (compass/crawler-google-places) or similar
        self.actor_id = "compass/crawler-google-places" 

    def search_leads(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Searches Google Maps for businesses matching the criteria.
        Criteria should include 'query' (e.g. 'Software companies in New York') or 'searchStrings' and 'location'.
        """
        # Construct search input for the actor
        # If 'search_term' is provided directly, use it. Otherwise construct from industry+location
        search_terms = criteria.get("search_terms", [])
        if not search_terms:
            industry = criteria.get("industry", "")
            location = criteria.get("location", "")
            if industry and location:
                search_terms = [f"{industry} in {location}"]
            elif criteria.get("query"):
                 search_terms = [criteria.get("query")]

        if not search_terms:
             print("Apify: No search terms provided.")
             return []

        run_input = {
            "searchStringsArray": search_terms,
            "maxCrawledPlacesPerSearch": criteria.get("limit", 10),
            "language": "en",
            "proxyConfig": {
                "useApifyProxy": True
            }
        }

        print(f"Apify: Starting run for {search_terms}...")
        try:
            run = self.client.actor(self.actor_id).call(run_input=run_input)
            
            leads = []
            # Fetch results from the run's dataset
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                # Map Google Maps data to our Lead structure
                # Note: Google Maps gives *Business* info, not *Person* info usually.
                # We will create a "Business Lead" where first_name is generic or parsed from contact info if avail.
                
                company_name = item.get("title")
                website = item.get("website")
                phone = item.get("phoneUnformatted") or item.get("phone")
                address = item.get("address")
                
                # Check if we have enough info to be useful
                if not company_name:
                    continue

                leads.append({
                    "first_name": "Team", # Generic contact
                    "last_name": company_name,
                    "email": item.get("email"), # Some scrapers find email, otherwise might need enrichment
                    "title": "Main Office",
                    "company_name": company_name,
                    "company_domain": self._extract_domain(website),
                    "location": address,
                    "phone": phone,
                    "website": website,
                    "source": "Google Maps"
                })
            
            print(f"Apify: Found {len(leads)} raw results.")
            return leads

        except Exception as e:
            print(f"Apify Error: {e}")
            return []

    def enrich_company(self, company_domain: str) -> Dict[str, Any]:
        """
        Apify isn't primarily an enrichment tool like Apollo, 
        but we could use a different actor here if needed.
        For now, returns basic info or we could daisy-chain to Apollo if we had hybrid setup.
        """
        return {"domain": company_domain, "source": "Apify"}

    def _extract_domain(self, url: str) -> str:
        if not url: return None
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
