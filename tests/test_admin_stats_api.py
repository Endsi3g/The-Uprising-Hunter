from __future__ import annotations

from datetime import datetime, timedelta

from src.core.db_models import DBCompany, DBInteraction, DBLead
from src.core.models import InteractionType, LeadStage, LeadStatus


def _seed_data(db_session):
    company = DBCompany(
        name="Acme Health",
        domain="acmehealth.com",
        industry="Healthcare",
        size_range="2-10",
    )
    db_session.add(company)
    db_session.flush()

    now = datetime.now()
    lead_contacted = DBLead(
        id="lead1@example.com",
        email="lead1@example.com",
        first_name="Lead",
        last_name="One",
        company_id=company.id,
        status=LeadStatus.CONTACTED,
        stage=LeadStage.CONTACTED,
        icp_score=68,
        heat_score=22,
        total_score=45,
        tags=["Tier B"],
        created_at=now - timedelta(days=2),
        updated_at=now - timedelta(days=1),
    )
    lead_closed = DBLead(
        id="lead2@example.com",
        email="lead2@example.com",
        first_name="Lead",
        last_name="Two",
        company_id=company.id,
        status=LeadStatus.CONVERTED,
        stage=LeadStage.SOLD,
        icp_score=92,
        heat_score=40,
        total_score=66,
        tags=["Tier A"],
        created_at=now - timedelta(days=4),
        updated_at=now - timedelta(days=1),
    )
    db_session.add_all([lead_contacted, lead_closed])
    db_session.flush()

    db_session.add_all(
        [
            DBInteraction(
                lead_id="lead1@example.com",
                type=InteractionType.EMAIL_REPLIED,
                timestamp=now - timedelta(days=1),
                details={"intent": "positive"},
            ),
            DBInteraction(
                lead_id="lead2@example.com",
                type=InteractionType.MEETING_BOOKED,
                timestamp=now - timedelta(days=1),
                details={},
            ),
        ]
    )
    db_session.commit()


def test_stats_endpoint_returns_core_kpis(client, db_session):
    _seed_data(db_session)

    response = client.get("/api/v1/admin/stats", auth=("admin", "secret"))
    assert response.status_code == 200
    payload = response.json()
    assert payload["sourced_total"] == 2
    assert payload["qualified_total"] == 2
    assert payload["contacted_total"] == 2
    assert payload["replied_total"] == 1
    assert payload["booked_total"] == 1
    assert payload["closed_total"] == 1
    assert "daily_pipeline_trend" in payload
    assert isinstance(payload["daily_pipeline_trend"], list)


def test_leads_endpoint_returns_paginated_rows(client, db_session):
    _seed_data(db_session)

    response = client.get("/api/v1/admin/leads?page=1&page_size=10", auth=("admin", "secret"))
    assert response.status_code == 200

    payload = response.json()
    assert payload["page"] == 1
    assert payload["total"] == 2
    assert len(payload["items"]) == 2


def test_create_lead_endpoint_v1(client, db_session):
    company = DBCompany(name="Create Corp", domain="createcorp.com")
    db_session.add(company)
    db_session.commit()

    payload = {
        "first_name": "Nora",
        "last_name": "Lemieux",
        "email": "nora@example.com",
        "phone": "+1-555-0100",
        "company_name": "Create Corp",
        "status": "NEW",
        "segment": "General",
    }
    response = client.post("/api/v1/admin/leads", auth=("admin", "secret"), json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "nora@example.com"
    assert body["company_name"] == "Create Corp"


def test_score_preview_endpoint(client):
    payload = {
        "id": "preview-1",
        "first_name": "Nadia",
        "last_name": "Gagnon",
        "email": "nadia@example.com",
        "company": {
            "name": "Clinique Nova",
            "industry": "Medical clinic",
            "size_range": "2-5",
            "location": "Montreal, QC",
            "description": "Prise de rendez-vous difficile, appelez-nous",
        },
        "details": {
            "admin_present": True,
            "no_faq": True,
            "missing_essentials": True,
            "low_mobile_score": True,
            "intent": {"intent_level": "high", "surge_score": 80, "topic_count": 3},
        },
        "interactions": [],
    }

    response_v1 = client.post("/api/v1/score/preview", auth=("admin", "secret"), json=payload)
    assert response_v1.status_code == 200
    body = response_v1.json()
    assert body["tier"].startswith("Tier ")
    assert body["heat_status"] in {"Cold", "Warm", "Hot"}
    assert "next_best_action" in body
