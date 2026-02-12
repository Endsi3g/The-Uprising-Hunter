import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.enrichment.client import MockApolloClient
from src.enrichment.service import EnrichmentService
from src.scoring.engine import ScoringEngine
from src.core.models import Interaction, InteractionType
import json

def run_pipeline():
    print("--- 1. INITIALIZATION ---")
    client = MockApolloClient()
    enricher = EnrichmentService(client)
    scorer = ScoringEngine()
    
    print("--- 2. SOURCING & ENRICHMENT ---")
    # Simulate searching for leads
    criteria = {"industry": "Software", "title": "CTO"}
    raw_leads = client.search_leads(criteria)
    
    leads = []
    for raw in raw_leads:
        # Enrich each lead
        lead = enricher.format_lead(raw)
        leads.append(lead)
        print(f"Enriched Lead: {lead.first_name} {lead.last_name} ({lead.company.name})")

    print("\n--- 3. ADDING INTERACTIONS (SIMULATION) ---")
    # Simulate some behavior for the first lead
    lead_0 = leads[0]
    lead_0.interactions.append(Interaction(id="1", type=InteractionType.EMAIL_SENT))
    lead_0.interactions.append(Interaction(id="2", type=InteractionType.EMAIL_OPENED))
    lead_0.interactions.append(Interaction(id="3", type=InteractionType.LINKEDIN_CONNECT))
    print(f"Added interactions to {lead_0.first_name}")

    print("\n--- 4. SCORING ---")
    for lead in leads:
        scorer.score_lead(lead)
        print(f"Lead: {lead.first_name} | Total Score: {lead.score.total_score}")
        print(f"  > ICP: {lead.score.icp_score} | Heat: {lead.score.heat_score}")
        print(f"  > Tier: {lead.score.tier} | Heat Status: {lead.score.heat_status}")
        print(
            f"  > Breakdown: {json.dumps({'icp': lead.score.icp_breakdown, 'heat': lead.score.heat_breakdown}, indent=2)}"
        )

    print("\n--- 5. AI MESSAGE GENERATION ---")
    from src.ai_engine.generator import MessageGenerator
    generator = MessageGenerator()
    
    for lead in leads:
        print(f"\n[Generated Email for {lead.first_name}]")
        email = generator.generate_cold_email(lead)
        print(email)
        print("-" * 30)

if __name__ == "__main__":
    run_pipeline()

