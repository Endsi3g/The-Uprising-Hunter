import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.models import Lead, Company
from src.scoring.engine import ScoringEngine
from src.ai_engine.generator import MessageGenerator
from src.core.payment import StripeService
import json

def verify_funnel():
    print("--- Verifying Funnel Logic ---")
    
    # 1. Create a dummy Clinic Lead
    clinic_lead = Lead(
        id="test-clinic-1",
        first_name="Jean",
        last_name="Dupont",
        email="jean.dupont@clinique-dentaire.fr",
        title="Dentiste Gérant",
        company=Company(
            name="Clinique Sourire Plus",
            industry="Dental / Medical",
            description="Clinique spécialisée en implantologie dentaire."
        )
    )
    
    # 2. Score & Segment (Step A)
    engine = ScoringEngine()
    scored_lead = engine.score_lead(clinic_lead)
    print(f"Step A - Score: {scored_lead.score.total_score}")
    print(f"Step A - Segment: {scored_lead.segment}")
    
    # 3. Generate Email (Step B)
    generator = MessageGenerator()
    email_content = generator.generate_cold_email(scored_lead)
    print("\nStep B - Email Gen (Cold):")
    print(email_content)
    
    follow_up = generator.generate_sequence_email(scored_lead, step=2)
    print("\nStep B - Email Gen (Follow-up):")
    print(follow_up)
    
    # 4. Stripe Link (Step D)
    stripe_service = StripeService()
    link = stripe_service.create_payment_link(option=1)
    print(f"\nStep D - Payment Link: {link}")
    
    # 5. Verify CTA
    assert "15 min" in email_content or "15 min" in follow_up, "CTA should contain '15 min'"
    print("\nVerification Successful!")

if __name__ == "__main__":
    verify_funnel()
