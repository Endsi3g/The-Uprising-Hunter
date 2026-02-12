from datetime import datetime, timedelta
from typing import Optional
from ..core.models import Lead, LeadStage, InteractionType

class FollowUpManager:
    """
    Manages the state machine for lead follow-ups.
    """
    
    def __init__(self):
        # Delays in days between actions
        self.delays = {
            "Tier A": [2, 3, 4], # Aggressive: J+2, J+5, J+9
            "Tier B": [3, 4, 5], # Standard: J+3, J+7, J+12
            "Tier C": [5, 7, 0], # Passive: J+5, J+12, Stop
            "Tier D": [7, 0, 0]  # Very Passive
        }

    def determine_next_action(self, lead: Lead) -> str:
        """
        Determines the next action and updates the next_action_date based on Tier and Stage.
        Returns a string describing the action (e.g. "Send Email 2", "Call", "Stop").
        """
        tier = "Tier C" # Default
        if lead.tags:
            for t in ["Tier A", "Tier B", "Tier C", "Tier D"]:
                if t in lead.tags:
                    tier = t
                    break
                    
        delays = self.delays.get(tier, self.delays["Tier C"])
        heat_status = str(lead.details.get("heat_status", "Cold")).lower()
        
        # Logic based on current stage
        if lead.stage == LeadStage.CONTACTED:
            if heat_status == "hot":
                lead.next_action_date = datetime.now()
                return "Immediate Call + Stripe-close option"
            if heat_status == "warm":
                delay = 1
                lead.next_action_date = datetime.now() + timedelta(days=delay)
                return "Plan Loom Audit Follow-up in 1 day"

            # Move to Step 2
            delay = delays[0]
            lead.next_action_date = datetime.now() + timedelta(days=delay)
            return f"Plan Follow-up 1 in {delay} days"
            
        elif lead.stage == LeadStage.OPENED:
            # Interested? Faster follow-up
            delay = max(1, delays[0] - 1) 
            lead.next_action_date = datetime.now() + timedelta(days=delay)
            return f"Plan Follow-up (Interested) in {delay} days"
            
        elif lead.stage == LeadStage.REPLIED:
            # Manual intervention usually, but set a reminder
            lead.next_action_date = datetime.now() + timedelta(days=1)
            return "Manual Reply Required (Reminder set for tomorrow)"
            
        elif lead.stage == LeadStage.BOOKED:
             lead.next_action_date = lead.details.get('meeting_date')
             return "Prepare for Meeting"

        return "No automated action"

    def process_interaction(self, lead: Lead, interaction_type: InteractionType):
        """
        Updates the lead stage based on a new interaction.
        """
        if interaction_type == InteractionType.EMAIL_OPENED:
            if lead.stage == LeadStage.CONTACTED:
                lead.stage = LeadStage.OPENED
                
        elif interaction_type == InteractionType.EMAIL_REPLIED:
            lead.stage = LeadStage.REPLIED
            lead.next_action_date = datetime.now() # Action needed now
            
        elif interaction_type == InteractionType.MEETING_BOOKED:
            lead.stage = LeadStage.BOOKED
            
        # Recalculate next action based on new stage
        self.determine_next_action(lead)
