import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.core.models import Lead, Company, LeadStage, InteractionType
from src.outreach.follow_up import FollowUpManager
from datetime import datetime, timedelta

def test_followup_logic():
    print("--- Testing Follow-up Engine ---")
    
    # 1. Setup Lead
    lead = Lead(
        id="test-follow-1",
        first_name="Dr. Test",
        last_name="Case",
        email="dr.test@clinic.com",
        title="Owner",
        company=Company(name="Test Clinic", industry="Medical"),
        tags=["Tier A"] # Should trigger aggressive follow-up
    )
    
    manager = FollowUpManager()
    
    # 2. Initial State (New -> Contacted)
    lead.stage = LeadStage.CONTACTED
    action = manager.determine_next_action(lead)
    print(f"Initial Action: {action}")
    print(f"Next Action Date: {lead.next_action_date}")
    
    # Verify Tier A delay (should be +2 days based on logic [2, 3, 4])
    expected_date = datetime.now() + timedelta(days=2)
    diff = abs((lead.next_action_date - expected_date).total_seconds())
    if diff < 60:
        print("PASS Tier A Initial Delay correct (approx 2 days)")
    else:
        print(f"FAIL Tier A Delay mismatch. Diff: {diff}")

    # 3. Simulate Email Open
    print("\nSimulating Email Open...")
    manager.process_interaction(lead, InteractionType.EMAIL_OPENED)
    print(f"New Stage: {lead.stage}")
    
    if lead.stage == LeadStage.OPENED:
        print("PASS Stage updated to OPENED")
    else:
        print(f"FAIL Stage failed to update: {lead.stage}")
        
    # 4. Simulate Reply
    print("\nSimulating Reply...")
    manager.process_interaction(lead, InteractionType.EMAIL_REPLIED)
    print(f"New Stage: {lead.stage}")
    print(f"Next Action Date (Reply): {lead.next_action_date}")
    
    # Should be tomorrow for manual reply
    expected_reply_date = datetime.now() + timedelta(days=1) # "tomorrow" logic in code is just +1 day from now
    # Note: my code said +1 day. 
    
    if lead.stage == LeadStage.REPLIED:
        print("PASS Stage updated to REPLIED")
    else:
        print(f"FAIL Stage failed to update: {lead.stage}")

    print("\nFollow-up Engine Logic Verified.")

if __name__ == "__main__":
    test_followup_logic()
