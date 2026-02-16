from __future__ import annotations

from datetime import datetime, timedelta

from src.core.db_models import DBLead


def _create_lead(client, email: str = "funnel.lead@example.com") -> str:
    response = client.post(
        "/api/v1/admin/leads",
        auth=("admin", "secret"),
        json={
            "first_name": "Funnel",
            "last_name": "Lead",
            "email": email,
            "company_name": "Stage Co",
            "status": "NEW",
            "segment": "SMB",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def _create_active_user(client, email: str = "owner@example.com") -> dict:
    invite_response = client.post(
        "/api/v1/admin/users/invite",
        auth=("admin", "secret"),
        json={"email": email, "display_name": "Owner User", "roles": ["sales"]},
    )
    assert invite_response.status_code == 200, invite_response.text
    invited = invite_response.json()
    activate_response = client.patch(
        f"/api/v1/admin/users/{invited['id']}",
        auth=("admin", "secret"),
        json={"status": "active", "roles": ["sales"]},
    )
    assert activate_response.status_code == 200, activate_response.text
    return activate_response.json()


def test_funnel_config_and_stage_transition_and_conversion(client):
    config_response = client.get("/api/v1/admin/funnel/config", auth=("admin", "secret"))
    assert config_response.status_code == 200
    assert "new" in config_response.json()["stages"]

    update_response = client.put(
        "/api/v1/admin/funnel/config",
        auth=("admin", "secret"),
        json={
            "model": "canonical_v1_custom",
            "stage_sla_hours": {"qualified": 36, "won": 12},
        },
    )
    assert update_response.status_code == 200, update_response.text
    updated_config = update_response.json()
    assert updated_config["model"] == "canonical_v1_custom"
    assert int(updated_config["stage_sla_hours"]["qualified"]) == 36

    lead_id = _create_lead(client, email="funnel.transition@example.com")
    transition_response = client.post(
        f"/api/v1/admin/leads/{lead_id}/stage-transition",
        auth=("admin", "secret"),
        json={"to_stage": "qualified", "reason": "ICP strong"},
    )
    assert transition_response.status_code == 200, transition_response.text
    transitioned = transition_response.json()
    assert transitioned["lead"]["stage_canonical"] == "qualified"
    assert transitioned["event"]["to_stage"] == "qualified"

    funnel_response = client.get("/api/v1/admin/conversion/funnel?days=30", auth=("admin", "secret"))
    assert funnel_response.status_code == 200, funnel_response.text
    payload = funnel_response.json()
    assert payload["window_days"] == 30
    qualified_row = next(item for item in payload["items"] if item["stage"] == "qualified")
    assert qualified_row["lead_count"] >= 1


def test_reassign_workload_and_bulk_assign_tasks(client):
    owner = _create_active_user(client, email="owner.workload@example.com")
    lead_id = _create_lead(client, email="lead.workload@example.com")

    reassign_response = client.post(
        f"/api/v1/admin/leads/{lead_id}/reassign",
        auth=("admin", "secret"),
        json={"owner_user_id": owner["id"], "reason": "Round robin"},
    )
    assert reassign_response.status_code == 200, reassign_response.text
    assert reassign_response.json()["owner_user_id"] == owner["id"]

    workload_response = client.get("/api/v1/admin/workload/owners", auth=("admin", "secret"))
    assert workload_response.status_code == 200, workload_response.text
    owners = workload_response.json()["items"]
    owner_row = next(item for item in owners if item["user_id"] == owner["id"])
    assert owner_row["lead_count_total"] >= 1

    task_ids: list[str] = []
    for index in range(2):
        task_response = client.post(
            "/api/v1/admin/tasks",
            auth=("admin", "secret"),
            json={
                "title": f"Task {index + 1}",
                "status": "To Do",
                "priority": "Medium",
                "lead_id": lead_id,
            },
        )
        assert task_response.status_code == 200, task_response.text
        task_ids.append(task_response.json()["id"])

    bulk_response = client.post(
        "/api/v1/admin/tasks/bulk-assign",
        auth=("admin", "secret"),
        json={"task_ids": task_ids, "assigned_to": "Owner User", "reason": "Batch ownership"},
    )
    assert bulk_response.status_code == 200, bulk_response.text
    bulk_payload = bulk_response.json()
    assert bulk_payload["updated"] == 2


def test_recommendations_apply_and_dismiss(client, db_session):
    owner = _create_active_user(client, email="owner.reco@example.com")
    lead_id = _create_lead(client, email="lead.reco@example.com")

    transition_response = client.post(
        f"/api/v1/admin/leads/{lead_id}/stage-transition",
        auth=("admin", "secret"),
        json={"to_stage": "qualified", "reason": "Qualified for routing"},
    )
    assert transition_response.status_code == 200

    lead = db_session.query(DBLead).filter(DBLead.id == lead_id).first()
    assert lead is not None
    lead.stage_canonical = "qualified"
    lead.lead_owner_user_id = owner["id"]
    lead.sla_due_at = datetime.utcnow() - timedelta(hours=1)
    db_session.commit()

    recommendations_response = client.get(
        "/api/v1/admin/recommendations?status=pending&limit=50&offset=0&seed=true",
        auth=("admin", "secret"),
    )
    assert recommendations_response.status_code == 200, recommendations_response.text
    items = recommendations_response.json()["items"]
    assert len(items) >= 1

    followup_reco = next(
        item for item in items if item["recommendation_type"] == "sla_followup" and item["entity_id"] == lead_id
    )
    apply_response = client.post(
        f"/api/v1/admin/recommendations/{followup_reco['id']}/apply",
        auth=("admin", "secret"),
    )
    assert apply_response.status_code == 200, apply_response.text
    assert apply_response.json()["recommendation"]["status"] == "applied"

    remaining_response = client.get(
        "/api/v1/admin/recommendations?status=pending&limit=50&offset=0&seed=true",
        auth=("admin", "secret"),
    )
    assert remaining_response.status_code == 200
    remaining = remaining_response.json()["items"]
    if remaining:
        dismiss_response = client.post(
            f"/api/v1/admin/recommendations/{remaining[0]['id']}/dismiss",
            auth=("admin", "secret"),
        )
        assert dismiss_response.status_code == 200, dismiss_response.text
        assert dismiss_response.json()["recommendation"]["status"] == "dismissed"


def test_opportunity_transition_and_handoff(client):
    owner = _create_active_user(client, email="owner.handoff@example.com")
    lead_id = _create_lead(client, email="lead.handoff@example.com")

    opp_response = client.post(
        "/api/v1/admin/opportunities",
        auth=("admin", "secret"),
        json={
            "prospect_id": lead_id,
            "amount": 4500,
            "stage": "Prospect",
            "probability": 35,
            "assigned_to": "Owner User",
        },
    )
    assert opp_response.status_code == 200, opp_response.text
    opportunity_id = opp_response.json()["id"]

    transition_response = client.post(
        f"/api/v1/admin/opportunities/{opportunity_id}/stage-transition",
        auth=("admin", "secret"),
        json={"to_stage": "won", "reason": "Signed"},
    )
    assert transition_response.status_code == 200, transition_response.text
    transitioned = transition_response.json()
    assert transitioned["opportunity"]["stage_canonical"] == "won"
    assert transitioned["event"]["to_stage"] == "won"

    handoff_response = client.post(
        "/api/v1/admin/handoffs",
        auth=("admin", "secret"),
        json={"lead_id": lead_id, "to_user_id": owner["id"], "note": "Start onboarding"},
    )
    assert handoff_response.status_code == 200, handoff_response.text
    handoff = handoff_response.json()
    assert handoff["event"]["to_stage"] == "post_sale"
    assert handoff["to_user"]["id"] == owner["id"]
