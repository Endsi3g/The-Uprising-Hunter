import yaml
import os
from typing import List
from ..core.models import Lead, LeadOutcome

class ScoringOptimizer:
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        self.config_path = config_path
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

    def learn_from_outcomes(self, historical_leads: List[Lead]):
        """
        Adjusts weights in config.yaml based on which features are present in Closed deals.
        Highly simplified logic for 'Intelligence Réelle'.
        """
        closed_leads = [l for l in historical_leads if l.outcome == LeadOutcome.CLOSED]
        lost_leads = [l for l in historical_leads if l.outcome == LeadOutcome.LOST]
        
        if not closed_leads:
            return # Not enough data
            
        # Analyze ICP features correlation with Closes
        icp_adjustments = {}
        
        # Example: Check if 'pain' features correlation with Closes
        
        for feature in self.config['icp_weights']['pain'].keys():
            # Check for breakdown key like 'pain_high_friction'
            breakdown_key = f"pain_{feature}"
            close_count = sum(1 for l in closed_leads if breakdown_key in l.score.icp_breakdown)
            lost_count = sum(1 for l in lost_leads if breakdown_key in l.score.icp_breakdown)
            
            # Simple boost if feature appears more in closed
            if close_count > lost_count:
                self.config['icp_weights']['pain'][feature] += 1
                icp_adjustments[feature] = "+1"
            elif lost_count > close_count:
                self.config['icp_weights']['pain'][feature] -= 1
                icp_adjustments[feature] = "-1"

        # Save back to yaml
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, sort_keys=False)
            
        return icp_adjustments
