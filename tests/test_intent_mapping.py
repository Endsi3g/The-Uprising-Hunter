from __future__ import annotations

from src.intent.mapping import normalize_intent_payload
from src.intent.mock_client import MockIntentProviderClient


def test_bombora_payload_normalization():
    payload = {
        "intent_score": 82,
        "topics": ["ai agents", "workflow automation"],
    }
    normalized = normalize_intent_payload("bombora", payload)
    assert normalized["provider"] == "bombora"
    assert normalized["intent_level"] == "high"
    assert normalized["topic_count"] == 2


def test_sixsense_payload_normalization():
    payload = {
        "buying_stage": "Decision",
        "intent_score": 77,
        "keywords": ["crm"],
    }
    normalized = normalize_intent_payload("6sense", payload)
    assert normalized["provider"] == "6sense"
    assert normalized["intent_level"] == "high"
    assert normalized["topic_count"] == 1


def test_mock_intent_client_shape():
    client = MockIntentProviderClient()
    result = client.fetch_company_intent(company_name="Acme", company_domain="acme.com")
    assert result["provider"] == "mock"
    assert result["intent_level"] in {"low", "medium", "high"}
    assert "surge_score" in result
    assert "topic_count" in result

