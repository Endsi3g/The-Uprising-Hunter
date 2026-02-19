from typing import Dict, Any, List
from ..core.models import Lead
from ..core.db_models import DBWorkflowRule, DBLead, DBTask
from ..core.logging import get_logger
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

logger = get_logger(__name__)

class RulesEngine:
    def __init__(self, db: Session):
        self.db = db

    def evaluate_and_execute(self, lead: DBLead, trigger_type: str):
        """
        Fetch active rules for the trigger and execute them if criteria match.
        """
        rules = self.db.query(DBWorkflowRule).filter(
            DBWorkflowRule.trigger_type == trigger_type,
            DBWorkflowRule.is_active == True
        ).all()

        for rule in rules:
            if self._check_criteria(lead, rule.criteria_json):
                logger.info(f"Executing rule {rule.name} for lead {lead.id}")
                self._execute_action(lead, rule.action_type, rule.action_config_json)

    def _check_criteria(self, lead: DBLead, criteria: Dict[str, Any]) -> bool:
        """
        Check if lead matches the criteria.
        Supported criteria:
        - min_score: Lead total score >= value
        - status: Lead status == value
        - stage: Lead stage == value
        - source: Lead source == value
        """
        if "min_score" in criteria:
            if (lead.total_score or 0) < criteria["min_score"]:
                return False
        
        if "status" in criteria:
            if lead.status != criteria["status"]:
                return False

        if "stage" in criteria:
            if lead.stage != criteria["stage"]:
                return False

        if "source" in criteria:
            if lead.source != criteria["source"]:
                return False

        return True

    def _execute_action(self, lead: DBLead, action_type: str, config: Dict[str, Any]):
        """
        Execute the action.
        Supported actions:
        - create_task: Create a task for the lead
        - change_stage: Update lead stage
        - change_status: Update lead status
        """
        if action_type == "create_task":
            task = DBTask(
                id=str(uuid.uuid4()),
                title=config.get("title", "Automated Task"),
                description=config.get("description", ""),
                status="To Do",
                priority=config.get("priority", "Medium"),
                lead_id=lead.id,
                source="workflow_automation",
                # rule_id could be added if we had the rule object context here, 
                # but for now we keep it simple or pass it if needed.
            )
            self.db.add(task)
            self.db.commit()
            logger.info(f"Task created for lead {lead.id}")

        elif action_type == "change_stage":
            new_stage = config.get("stage")
            if new_stage:
                lead.stage = new_stage
                lead.updated_at = datetime.now()
                self.db.commit()
                logger.info(f"Lead {lead.id} stage updated to {new_stage}")

        elif action_type == "change_status":
            new_status = config.get("status")
            if new_status:
                lead.status = new_status
                lead.updated_at = datetime.now()
                self.db.commit()
                logger.info(f"Lead {lead.id} status updated to {new_status}")
