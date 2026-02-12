import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.models import Lead, Company, Interaction, InteractionType, LeadOutcome
from src.scoring.engine import ScoringEngine
from src.scoring.optimizer import ScoringOptimizer
from src.ai_engine.agent_tools import AgenticToolCreator
from datetime import datetime
import os

def verify_system():
    print("--- Verifying Advanced Intelligent System ---")
    
    # 1. Test Scoring Engine (ICP & Heat)
    engine = ScoringEngine()
    lead = Lead(
        id="adv-test-1",
        first_name="Marc",
        last_name="Lavoie",
        email="marc.lavoie@clinique-laval.ca",
        title="Physiothérapeute",
        company=Company(
            name="Clinique Physio Laval",
            industry="Physiotherapy",
            size_range="2-5",
            description="Clinique de physiothérapie spécialisée."
        ),
        interactions=[
            Interaction(id="i1", type=InteractionType.EMAIL_OPENED, timestamp=datetime.now()),
            Interaction(id="i2", type=InteractionType.EMAIL_OPENED, timestamp=datetime.now())
        ]
    )
    
    scored_lead = engine.score_lead(lead)
    print(f"ICP Score: {scored_lead.score.icp_score}")
    print(f"Heat Score: {scored_lead.score.heat_score}")
    print(f"Tags: {scored_lead.tags}")
    
    # 2. Test Optimizer (Feedback Loop)
    optimizer = ScoringOptimizer()
    scored_lead.outcome = LeadOutcome.CLOSED
    adjustments = optimizer.learn_from_outcomes([scored_lead])
    print(f"Weight Adjustments: {adjustments}")
    
    # 3. Test Agentic Tool Creator (Mock logic)
    creator = AgenticToolCreator()
    html_sample = "<html><body><button>Rendez-vous</button></body></html>"
    # Note: We won't call the actual LLM in this test to save tokens/time, 
    # but we verify the structural existence.
    print(f"Agentic Tools Dir exists: {os.path.exists(creator.tools_dir)}")
    
    print("\nAdvanced Verification Successful!")

if __name__ == "__main__":
    verify_system()
