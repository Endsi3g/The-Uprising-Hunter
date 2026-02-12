from __future__ import annotations

from datetime import datetime

from src.core.db_models import DBCompany, DBLead, DBProject, DBTask
from src.core.models import LeadStage, LeadStatus


def _seed_search_data(db_session):
    company = DBCompany(name="Acme Search", domain="acmesearch.com")
    db_session.add(company)
    db_session.flush()

    lead = DBLead(
        id="acme.lead@example.com",
        email="acme.lead@example.com",
        first_name="Alice",
        last_name="Acme",
        company_id=company.id,
        status=LeadStatus.NEW,
        stage=LeadStage.NEW,
        created_at=datetime.now(),
    )
    task = DBTask(
        id="task-acme",
        title="Appeler Alice Acme",
        status="To Do",
        priority="High",
        assigned_to="Vous",
        created_at=datetime.now(),
    )
    project = DBProject(
        id="proj-acme",
        name="Projet Acme",
        status="Planning",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db_session.add_all([lead, task, project])
    db_session.commit()


def test_search_empty_query(client):
    response = client.get("/api/v1/admin/search?q=&limit=10", auth=("admin", "secret"))
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 0
    assert payload["items"] == []


def test_search_mixed_entities(client, db_session):
    _seed_search_data(db_session)
    response = client.get("/api/v1/admin/search?q=acme&limit=10", auth=("admin", "secret"))
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 2
    item_types = {item["type"] for item in payload["items"]}
    assert "lead" in item_types
    assert "project" in item_types


def test_search_limit_is_applied(client, db_session):
    _seed_search_data(db_session)
    response = client.get("/api/v1/admin/search?q=acme&limit=1", auth=("admin", "secret"))
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] <= 1
    assert len(payload["items"]) <= 1

