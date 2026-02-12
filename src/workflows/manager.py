from typing import List, Dict, Optional
from ..core.models import Lead, LeadStatus
from ..core.logging import get_logger
from ..enrichment.service import EnrichmentService
from ..enrichment.client import SourcingClient
from ..scoring.engine import ScoringEngine
from ..ai_engine.generator import MessageGenerator
from ..intent.base import IntentProviderClient


logger = get_logger(__name__)


class WorkflowManager:
    def __init__(self, sourcing_client: SourcingClient, intent_client: Optional[IntentProviderClient] = None):
        self.enricher = EnrichmentService(sourcing_client, intent_client=intent_client)
        self.scorer = ScoringEngine()
        self.generator = MessageGenerator()
        
        self.min_score_threshold = self.scorer.qualification_threshold
        
    def process_lead_criteria(self, criteria: Dict) -> List[Lead]:
        logger.info("Workflow processing started.", extra={"criteria": criteria})
        
        # 1. Sourcing & Enrichment
        leads = self.enricher.source_and_enrich(criteria)
        logger.info("Sourcing complete.", extra={"lead_count": len(leads)})
        
        processed_leads = []
        for lead in leads:
            logger.info("Processing lead.", extra={"lead_id": lead.id, "email": lead.email})
            
            # 2. Scoring
            lead = self.scorer.score_lead(lead)
            tier = lead.score.tier
            heat_status = lead.score.heat_status
            next_best_action = lead.score.next_best_action
            logger.info(
                "Lead scored.",
                extra={
                    "lead_id": lead.id,
                    "icp_score": round(lead.score.icp_score, 2),
                    "heat_score": round(lead.score.heat_score, 2),
                    "tier": tier,
                    "heat_status": heat_status,
                },
            )
            
            # 3. Decision Logic
            if tier == "Tier D":
                logger.info("Tier D lead archived.", extra={"lead_id": lead.id})
                lead.status = LeadStatus.DQ
                lead.details["workflow_decision"] = "archive"
                lead.details["workflow_reason"] = "Tier D low ICP fit"
            elif lead.score.total_score >= self.min_score_threshold:
                lead.status = LeadStatus.SCORED
                logger.info(
                    "Lead qualified for outreach.",
                    extra={"lead_id": lead.id, "total_score": round(lead.score.total_score, 2)},
                )
                
                # 4. Generate Outreach
                email_content = self.generator.generate_cold_email(lead)
                logger.info("Generated cold email draft.", extra={"lead_id": lead.id})
                
                # In a real system, we would add to queue here
                lead.details["draft_email"] = email_content
                lead.details["workflow_decision"] = "outreach"
                lead.details["automation_action"] = next_best_action
                lead.status = LeadStatus.CONTACTED # Simulating immediate action

                if lead.details.get("should_send_loom"):
                    logger.info("Loom audit recommended.", extra={"lead_id": lead.id})

                if lead.details.get("propose_stripe_link"):
                    logger.info("Stripe close path suggested.", extra={"lead_id": lead.id})
                
            else:
                logger.info(
                    "Lead disqualified by threshold.",
                    extra={
                        "lead_id": lead.id,
                        "total_score": round(lead.score.total_score, 2),
                        "qualification_threshold": self.min_score_threshold,
                    },
                )
                lead.status = LeadStatus.DQ
                lead.details["workflow_decision"] = "nurture_or_skip"
                lead.details["workflow_reason"] = "Below qualification threshold"
                
            processed_leads.append(lead)
            
        return processed_leads
