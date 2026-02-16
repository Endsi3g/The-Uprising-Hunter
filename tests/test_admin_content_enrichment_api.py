from __future__ import annotations

import importlib

from src.core.db_models import DBLead
from src.core.models import LeadStage, LeadStatus


def _seed_content_lead(db_session):
    lead = DBLead(
        id="content-lead@example.com",
        email="content-lead@example.com",
        first_name="Claire",
        last_name="Dubois",
        status=LeadStatus.NEW,
        stage=LeadStage.NEW,
        total_score=72,
        details={
            "company_name": "Clinique Horizon",
            "industry": "Healthcare",
            "location": "Lyon",
        },
    )
    db_session.add(lead)
    db_session.commit()
    return lead


def test_generate_content_email_and_call(client, db_session):
    lead = _seed_content_lead(db_session)

    email_response = client.post(
        "/api/v1/admin/content/generate",
        auth=("admin", "secret"),
        json={
            "lead_id": lead.id,
            "channel": "email",
            "step": 1,
            "template_key": "nurture_intro",
            "context": {"pain_point": "la gestion des relances"},
        },
    )
    assert email_response.status_code == 200, email_response.text
    email_payload = email_response.json()
    assert email_payload["channel"] == "email"
    assert isinstance(email_payload.get("subject"), str)
    assert isinstance(email_payload.get("body"), str)
    assert email_payload.get("confidence", 0) >= 0.6

    call_response = client.post(
        "/api/v1/admin/content/generate",
        auth=("admin", "secret"),
        json={
            "lead_id": lead.id,
            "channel": "call",
            "step": 2,
            "context": {"goal": "reduire les no-shows"},
        },
    )
    assert call_response.status_code == 200, call_response.text
    call_payload = call_response.json()
    assert call_payload["channel"] == "call"
    assert isinstance(call_payload.get("call_script"), str)


def test_enrichment_run_and_fetch(client, db_session):
    lead = _seed_content_lead(db_session)

    run_response = client.post(
        "/api/v1/admin/enrichment/run",
        auth=("admin", "secret"),
        json={
            "query": "clinique horizon lyon prise de rendez-vous",
            "lead_id": lead.id,
            "provider": "mock",
            "context": {"source": "manual"},
        },
    )
    assert run_response.status_code == 200, run_response.text
    run_payload = run_response.json()
    assert run_payload["status"] == "completed"
    assert run_payload["relevance_score"] > 0
    assert run_payload.get("result", {}).get("summary")

    fetch_response = client.get(
        f"/api/v1/admin/enrichment/{run_payload['id']}",
        auth=("admin", "secret"),
    )
    assert fetch_response.status_code == 200, fetch_response.text
    fetch_payload = fetch_response.json()
    assert fetch_payload["id"] == run_payload["id"]
    assert fetch_payload["status"] == "completed"


def test_generate_content_with_ollama_provider(client, db_session, monkeypatch):
    lead = _seed_content_lead(db_session)

    put_response = client.put(
        "/api/v1/admin/integrations",
        auth=("admin", "secret"),
        json={
            "providers": {
                "ollama": {
                    "enabled": True,
                    "config": {
                        "api_base_url": "https://ollama.example.internal",
                        "api_key_env": "OLLAMA_API_KEY",
                        "model_content": "llama3.1:8b-instruct",
                    },
                }
            }
        },
    )
    assert put_response.status_code == 200, put_response.text

    captured: dict[str, object] = {}
    content_module = importlib.import_module("src.admin.content_service")

    def fake_chat_completion(*, messages, config=None, **kwargs):
        captured["messages"] = messages
        captured["config"] = config
        return '{"subject":"Objet Ollama","body":"Bonjour Claire, voici une proposition adaptee."}'

    monkeypatch.setattr(content_module, "chat_completion", fake_chat_completion)

    response = client.post(
        "/api/v1/admin/content/generate",
        auth=("admin", "secret"),
        json={
            "lead_id": lead.id,
            "channel": "email",
            "step": 1,
            "provider": "ollama",
            "context": {"pain_point": "les relances manuelles"},
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["provider"] == "ollama"
    assert payload["subject"] == "Objet Ollama"
    assert "Bonjour Claire" in payload["body"]
    assert isinstance(captured.get("messages"), list)
    assert isinstance(captured.get("config"), dict)
