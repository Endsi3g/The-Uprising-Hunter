from typing import List, Dict, Any
from ..core.models import Lead, InteractionType, ScoringData

class DemographicScorer:
    def score(self, lead: Lead) -> float:
        points = 0
        breakdown = {}
        
        # Title Scoring
        title = lead.title.lower() if lead.title else ""
        if any(x in title for x in ["cto", "ceo", "vp", "director", "head"]):
            p = 25
            points += p
            breakdown['title_seniority'] = p
        
        # Company Size Scoring
        if lead.company.size_range in ["100-500", "500-1000", "1000+"]:
            p = 25
            points += p
            breakdown['company_size'] = p
            
        # Industry Scoring (Mock)
        if lead.company.industry in ["Software", "Technology", "SaaS"]:
            p = 20
            points += p
            breakdown['industry_match'] = p
            
        return points, breakdown

class BehaviorScorer:
    def score(self, lead: Lead) -> float:
        points = 0
        breakdown = {}
        
        for interaction in lead.interactions:
            p = 0
            if interaction.type == InteractionType.EMAIL_OPENED:
                p = 2
            elif interaction.type == InteractionType.EMAIL_REPLIED:
                p = 20
            elif interaction.type == InteractionType.LINKEDIN_CONNECT:
                p = 10
            elif interaction.type == InteractionType.MEETING_BOOKED:
                p = 50
            
            if p > 0:
                points += p
                k = f"interaction_{interaction.type}_{interaction.timestamp.strftime('%Y%m%d')}"
                breakdown[k] = p
                
        return points, breakdown

class IntentScorer:
    def score(self, lead: Lead) -> float:
        # Mock Intent Scoring - in real world would come from Bombora/6sense data attached to company
        points = 0
        breakdown = {}
        
        # Simulating if we had intent data attached to the company or lead
        # For now, let's assume if they have "Growth" or "Hiring" in description it's a signal
        if lead.company.description and "hiring" in lead.company.description.lower():
             p = 15
             points += p
             breakdown['intent_hiring_signal'] = p
             
        return points, breakdown

class ScoringEngine:
    def __init__(self):
        self.demographic = DemographicScorer()
        self.behavior = BehaviorScorer()
        self.intent = IntentScorer()
        
    def score_lead(self, lead: Lead) -> Lead:
        d_score, d_breakdown = self.demographic.score(lead)
        b_score, b_breakdown = self.behavior.score(lead)
        i_score, i_breakdown = self.intent.score(lead)
        
        total = d_score + b_score + i_score
        
        # Merge breakdowns
        full_breakdown = {**d_breakdown, **b_breakdown, **i_breakdown}
        
        lead.score = ScoringData(
            demographic_score=d_score,
            behavioral_score=b_score,
            intent_score=i_score,
            total_score=total,
            score_breakdown=full_breakdown
        )
        
        return lead
