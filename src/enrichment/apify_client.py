from __future__ import annotations

from typing import List, Dict, Any, Optional
from apify_client import ApifyClient
from .client import SourcingClient
from urllib.parse import urlparse
import re
import requests

from ..core.http import HttpRequestConfig, request_with_retries
from ..core.logging import get_logger


logger = get_logger(__name__)

class ApifyMapsClient(SourcingClient):
    """
    Client for sourcing leads via Apify (Google Maps Scraper).
    """
    def __init__(self, api_token: str):
        self.client = ApifyClient(api_token)
        # Using the Compass Google Maps crawler (compass/crawler-google-places) or similar
        self.actor_id = "compass/crawler-google-places" 
        self._website_probe_cache: Dict[str, Dict[str, Any]] = {}
        self._http_session = requests.Session()
        self._http_request_config = HttpRequestConfig(timeout=4.0, max_retries=2)

    @staticmethod
    def _safe_str(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        return str(value)

    def _blob_text(self, item: Dict[str, Any]) -> str:
        parts = []
        candidate_keys = (
            "title",
            "categoryName",
            "address",
            "description",
            "about",
            "website",
            "phone",
            "temporarilyClosed",
            "popularTimesHistogram",
            "reviews",
            "additionalInfo",
            "openingHours",
            "businessStatus",
        )
        for key in candidate_keys:
            raw = item.get(key)
            if raw is None:
                continue
            if isinstance(raw, list):
                parts.extend(self._safe_str(x) for x in raw)
            elif isinstance(raw, dict):
                parts.extend(self._safe_str(v) for v in raw.values())
            else:
                parts.append(self._safe_str(raw))
        return " ".join(parts).lower()

    @staticmethod
    def _contains_any(text: str, keywords: List[str]) -> bool:
        return any(keyword in text for keyword in keywords)

    def _extract_domain(self, url: str) -> Optional[str]:
        if not url:
            return None
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith("www."):
            domain = domain[4:]
        return domain or None

    def _probe_website(self, website_url: Optional[str]) -> Dict[str, Any]:
        if not website_url:
            return {}

        domain = self._extract_domain(website_url)
        if domain and domain in self._website_probe_cache:
            return self._website_probe_cache[domain]

        try:
            response = request_with_retries(
                self._http_session,
                "GET",
                website_url,
                config=self._http_request_config,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            html = response.text.lower()
        except requests.RequestException as exc:
            logger.debug(
                "Website probe failed.",
                extra={"website_url": website_url, "error": str(exc)},
            )
            result = {}
            if domain:
                self._website_probe_cache[domain] = result
            return result

        first_fold = html[:4000]
        visible_blob = re.sub(r"<[^>]+>", " ", html)
        visible_blob = re.sub(r"\s+", " ", visible_blob)

        has_faq = any(token in visible_blob for token in ["faq", "foire aux questions", "questions frequentes"])
        has_contact_form = "<form" in html and any(token in html for token in ["contact", "appointment", "rendez"])
        has_social = any(token in html for token in ["facebook.com", "instagram.com", "linkedin.com", "tiktok.com"])

        cta_tokens = ("prendre rendez", "book now", "book appointment", "contact", "calendly")
        no_fold_cta = not any(token in first_fold for token in cta_tokens)

        mobile_signals_bad = False
        if 'name="viewport"' not in html and "width=device-width" not in html:
            mobile_signals_bad = True
        if "font-size:10px" in html or "font-size: 10px" in html:
            mobile_signals_bad = True

        has_map_or_direction = any(token in html for token in ("google.com/maps", "itineraire", "directions"))
        has_fb_pixel = any(token in html for token in ["fbevents.js", "connect.facebook.net", "facebook-jssdk"])
        
        # Design quality heuristics
        design_quality_high = any(token in html for token in ["tailwind", "next.js", "wp-content", "elementor", "webflow"])
        design_quality_low = any(token in html for token in ["table border=", "frameset", "font face=", "ms-outlook"])

        result = {
            "website_has_faq": has_faq,
            "website_has_contact_form": has_contact_form,
            "website_has_social_links": has_social,
            "website_no_fold_cta": no_fold_cta,
            "website_mobile_signals_bad": mobile_signals_bad,
            "website_has_map_or_directions": has_map_or_direction,
            "has_fb_pixel": has_fb_pixel,
            "design_quality_high": design_quality_high,
            "design_quality_low": design_quality_low,
        }

        if domain:
            self._website_probe_cache[domain] = result

        return result

    def _build_scoring_details(self, item: Dict[str, Any], website_probe: Dict[str, Any]) -> Dict[str, Any]:
        text_blob = self._blob_text(item)
        address = self._safe_str(item.get("address")).lower()

        opening_hours = item.get("openingHours")
        has_hours = bool(opening_hours)
        has_phone = bool(item.get("phoneUnformatted") or item.get("phone"))
        has_website = bool(item.get("website"))

        # ICP fit / pain / digital flags from scraped + website heuristic.
        details: Dict[str, Any] = {
            "source": "Google Maps",
            "location_priority": self._contains_any(
                address,
                ["montreal", "laval", "longueuil", "quebec", "qc"],
            ),
            "admin_present": self._contains_any(
                text_blob,
                ["gestionnaire", "admin", "reception", "manager", "coordinator"],
            ),
            "vague_booking": self._contains_any(
                text_blob,
                ["rendez-vous", "rendez vous", "book", "appointment", "prise de rendez-vous"],
            ),
            "no_faq": not bool(item.get("questionsAndAnswers")) and not website_probe.get("website_has_faq", False),
            "missing_essentials": not has_hours or not has_phone,
            "low_mobile_score": bool(website_probe.get("website_mobile_signals_bad", False)),
            "no_fold_cta": bool(website_probe.get("website_no_fold_cta", False)),
            "weak_contact_page": (
                not has_phone
                or not has_website
                or not website_probe.get("website_has_map_or_directions", False)
            ),
            "has_contact_form": bool(website_probe.get("website_has_contact_form", False)),
            "active_social": bool(website_probe.get("website_has_social_links", False)),
            "recent_post": self._contains_any(
                text_blob,
                ["2026", "2025", "recent", "new post", "nouveau", "actu", "mise a jour"],
            ),
            "hiring": self._contains_any(
                text_blob,
                ["hiring", "join our team", "we are hiring", "recrute", "emploi", "careers"],
            ),
            "new_service": self._contains_any(
                text_blob,
                ["new service", "nouveau service", "now offering", "offre desormais", "nouveaute"],
            ),
            "has_fb_pixel": bool(website_probe.get("has_fb_pixel", False)),
            "high_design_quality": bool(website_probe.get("design_quality_high", False)),
            "low_design_quality": bool(website_probe.get("design_quality_low", False)),
            # Optional site telemetry bucket used by heat scoring.
            "site_events": [
                {
                    "page": "offre" if self._contains_any(text_blob, ["offre", "pricing", "tarif", "price"]) else "home",
                    "return_within_hours": 24 if self._contains_any(text_blob, ["recent", "return", "retour"]) else 72,
                    "multi_page": bool(has_website and has_hours),
                }
            ],
        }

        return details

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
             logger.warning("Apify search called without search terms.")
             return []

        run_input = {
            "searchStringsArray": search_terms,
            "maxCrawledPlacesPerSearch": criteria.get("limit", 10),
            "language": "en",
            "proxyConfig": {
                "useApifyProxy": True
            }
        }

        logger.info("Apify lead search started.", extra={"search_terms": search_terms})
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
                website_probe = self._probe_website(website)
                details = self._build_scoring_details(item, website_probe)

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
                    "source": "Google Maps",
                    "details": details,
                })
            
            logger.info("Apify lead search completed.", extra={"lead_count": len(leads)})
            return leads

        except Exception as exc:
            logger.exception(
                "Apify lead search failed.",
                extra={"search_terms": search_terms, "error": str(exc)},
            )
            return []

    def enrich_company(self, company_domain: str) -> Dict[str, Any]:
        """
        Apify isn't primarily an enrichment tool like Apollo, 
        but we could use a different actor here if needed.
        For now, returns basic info or we could daisy-chain to Apollo if we had hybrid setup.
        """
        return {"domain": company_domain, "source": "Apify"}

class MockApifyMapsClient(SourcingClient):
    """
    Mock implementation for development.
    """
    def search_leads(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        logger.info("Using mock Apify search.", extra={"criteria": criteria})
        return [
            {
                "first_name": "Dr. Jean",
                "last_name": "Tremblay",
                "email": "jtremblay@cliniquedunord.ca",
                "company_name": "Clinique du Nord",
                "company_domain": "cliniquedunord.ca",
                "location": "Montreal, QC",
                "source": "Mock Apify"
            }
        ]

    def enrich_company(self, company_domain: str) -> Dict[str, Any]:
        logger.info("Using mock company enrichment (Apify).", extra={"domain": company_domain})
        return {
            "name": "Clinique Dentaire Mock",
            "industry": "Medical Practice",
            "size_range": "11-50",
            "description": "Une clinique dentaire moderne au coeur de Montreal.",
            "tech_stack": ["WordPress", "Google Analytics"],
            "location": "Montreal, QC"
        }
