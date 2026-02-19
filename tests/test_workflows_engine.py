import pytest
from unittest.mock import MagicMock
from src.workflows.rules_engine import RulesEngine
from src.core.db_models import DBLead, DBWorkflowRule, DBTask

def test_rules_engine_create_task(db_session):
    # Setup
    lead = DBLead(id="test@example.com", email="test@example.com", total_score=90, status="NEW")
    db_session.add(lead)
    
    rule = DBWorkflowRule(
        id="rule-1",
        name="High Score Task",
        trigger_type="lead_scored",
        criteria_json={"min_score": 80},
        action_type="create_task",
        action_config_json={"title": "Follow up High Score", "priority": "High"},
        is_active=True
    )
    db_session.add(rule)
    db_session.commit()
    
    # Execute
    engine = RulesEngine(db_session)
    engine.evaluate_and_execute(lead, "lead_scored")
    
    # Verify
    task = db_session.query(DBTask).filter(DBTask.lead_id == lead.id).first()
    assert task is not None
    assert task.title == "Follow up High Score"
    assert task.priority == "High"

def test_rules_engine_criteria_mismatch(db_session):
    # Setup
    lead = DBLead(id="test2@example.com", email="test2@example.com", total_score=50, status="NEW")
    db_session.add(lead)
    
    rule = DBWorkflowRule(
        id="rule-2",
        name="High Score Task",
        trigger_type="lead_scored",
        criteria_json={"min_score": 80},
        action_type="create_task",
        action_config_json={"title": "Follow up"},
        is_active=True
    )
    db_session.add(rule)
    db_session.commit()
    
    # Execute
    engine = RulesEngine(db_session)
    engine.evaluate_and_execute(lead, "lead_scored")
    
    # Verify
    task = db_session.query(DBTask).filter(DBTask.lead_id == lead.id).first()
    assert task is None
