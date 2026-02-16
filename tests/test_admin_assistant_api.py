"""Tests for the Assistant Prospect (IA) API endpoints.

Run with:
    pytest tests/test_admin_assistant_api.py -v
"""
from __future__ import annotations

import importlib
import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.admin.app import create_app
from src.core.database import SessionLocal


@pytest.fixture(scope="module")
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth():
    import os
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "change-me")
    return (username, password)


# ---------------------------------------------------------------
# POST /api/v1/admin/assistant/prospect/execute
# ---------------------------------------------------------------
class TestAssistantExecute:
    """Test the execute endpoint (uses mock when Khoj is unavailable)."""

    def test_execute_returns_run_with_actions(self, client: TestClient, auth: tuple[str, str]):
        resp = client.post(
            "/api/v1/admin/assistant/prospect/execute",
            json={
                "prompt": "Trouve 5 leads dentistes à Lyon",
                "max_leads": 5,
                "source": "apify",
                "auto_confirm": True,
            },
            auth=auth,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["prompt"] == "Trouve 5 leads dentistes à Lyon"
        assert data["status"] in {"pending", "running", "completed", "completed_with_errors", "failed"}
        assert isinstance(data.get("actions"), list)

    def test_execute_without_prompt_returns_422(self, client: TestClient, auth: tuple[str, str]):
        resp = client.post(
            "/api/v1/admin/assistant/prospect/execute",
            json={"prompt": "", "max_leads": 5},
            auth=auth,
        )
        assert resp.status_code == 422

    def test_execute_requires_auth(self, client: TestClient):
        resp = client.post(
            "/api/v1/admin/assistant/prospect/execute",
            json={"prompt": "test"},
        )
        assert resp.status_code == 401

    def test_execute_falls_back_to_ollama_when_khoj_fails(
        self,
        client: TestClient,
        auth: tuple[str, str],
        monkeypatch,
    ):
        integrations_response = client.put(
            "/api/v1/admin/integrations",
            auth=auth,
            json={
                "providers": {
                    "ollama": {
                        "enabled": True,
                        "config": {
                            "api_base_url": "https://ollama.example.internal",
                            "api_key_env": "OLLAMA_API_KEY",
                            "model_assistant": "llama3.1:8b-instruct",
                        },
                    }
                }
            },
        )
        assert integrations_response.status_code == 200, integrations_response.text

        assistant_module = importlib.import_module("src.admin.assistant_service")
        captured: dict[str, object] = {}

        def fake_khoj_post(*args, **kwargs):
            raise RuntimeError("khoj unavailable")

        def fake_ollama_planner(prompt: str, config: dict | None = None):
            captured["prompt"] = prompt
            captured["config"] = config or {}
            return assistant_module.AssistantPlan(
                summary="Plan Ollama fallback",
                actions=[
                    assistant_module.AssistantActionSpec(
                        action_type="create_task",
                        entity_type="task",
                        payload={"title": "Relancer les prospects IA"},
                        requires_confirm=False,
                    )
                ],
            )

        monkeypatch.setenv("KHOJ_API_BASE_URL", "https://khoj.invalid")
        monkeypatch.setenv("OLLAMA_ASSISTANT_FALLBACK_ENABLED", "true")
        monkeypatch.setattr(assistant_module.requests, "post", fake_khoj_post)
        monkeypatch.setattr(assistant_module, "_call_ollama_planner", fake_ollama_planner)

        resp = client.post(
            "/api/v1/admin/assistant/prospect/execute",
            json={
                "prompt": "Prepare un plan d'actions pour 3 leads",
                "max_leads": 3,
                "source": "apify",
                "auto_confirm": True,
            },
            auth=auth,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["summary"] == "Plan Ollama fallback"
        assert isinstance(data.get("actions"), list)
        assert any(item.get("action_type") == "create_task" for item in data["actions"])
        assert any(item.get("status") == "executed" for item in data["actions"])

        captured_config = captured.get("config")
        assert isinstance(captured_config, dict)
        ollama_config = captured_config.get("ollama_config")
        assert isinstance(ollama_config, dict)
        assert ollama_config.get("api_base_url") == "https://ollama.example.internal"

    def test_execute_research_action_uses_runtime_ollama_config(
        self,
        client: TestClient,
        auth: tuple[str, str],
        monkeypatch,
    ):
        integrations_response = client.put(
            "/api/v1/admin/integrations",
            auth=auth,
            json={
                "providers": {
                    "ollama": {
                        "enabled": True,
                        "config": {
                            "api_base_url": "https://ollama.example.internal",
                            "api_key_env": "OLLAMA_API_KEY",
                            "model_research": "llama3.1:8b-instruct",
                        },
                    }
                }
            },
        )
        assert integrations_response.status_code == 200, integrations_response.text

        assistant_module = importlib.import_module("src.admin.assistant_service")
        research_module = importlib.import_module("src.admin.research_service")
        captured: dict[str, object] = {}

        def fake_khoj_post(*args, **kwargs):
            raise RuntimeError("khoj unavailable")

        def fake_ollama_planner(prompt: str, config: dict | None = None):
            return assistant_module.AssistantPlan(
                summary="Plan Ollama research",
                actions=[
                    assistant_module.AssistantActionSpec(
                        action_type="research",
                        entity_type="lead",
                        payload={
                            "query": "cabinets dentaires lyon",
                            "provider": "ollama",
                            "limit": 2,
                        },
                        requires_confirm=False,
                    )
                ],
            )

        def fake_run_web_research(**kwargs):
            captured["provider_configs"] = kwargs["provider_configs"]
            return {
                "query": kwargs["query"],
                "provider_selector": kwargs["provider_selector"],
                "providers_requested": ["ollama"],
                "providers_used": ["ollama"],
                "total": 1,
                "items": [
                    {
                        "provider": "ollama",
                        "source": "ollama",
                        "title": "Cabinet dentaire Lyon",
                        "url": "https://example.com/dentiste-lyon",
                        "snippet": "Resultat test",
                        "published_at": None,
                    }
                ],
                "warnings": [],
            }

        monkeypatch.setenv("KHOJ_API_BASE_URL", "https://khoj.invalid")
        monkeypatch.setenv("OLLAMA_ASSISTANT_FALLBACK_ENABLED", "true")
        monkeypatch.setattr(assistant_module.requests, "post", fake_khoj_post)
        monkeypatch.setattr(assistant_module, "_call_ollama_planner", fake_ollama_planner)
        monkeypatch.setattr(research_module, "run_web_research", fake_run_web_research)

        resp = client.post(
            "/api/v1/admin/assistant/prospect/execute",
            json={
                "prompt": "Trouve des leads avec recherche Ollama",
                "max_leads": 2,
                "source": "apify",
                "auto_confirm": True,
            },
            auth=auth,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        actions = data.get("actions", [])
        research_actions = [item for item in actions if item.get("action_type") == "research"]
        assert research_actions
        assert research_actions[0].get("status") == "executed"
        assert research_actions[0].get("result", {}).get("total_items") == 1

        provider_configs = captured.get("provider_configs")
        assert isinstance(provider_configs, dict)
        ollama_provider = provider_configs.get("ollama")
        assert isinstance(ollama_provider, dict)
        assert ollama_provider.get("enabled") is True
        assert ollama_provider.get("config", {}).get("api_base_url") == "https://ollama.example.internal"


# ---------------------------------------------------------------
# GET /api/v1/admin/assistant/prospect/runs
# ---------------------------------------------------------------
class TestAssistantListRuns:
    """Test list runs endpoint."""

    def test_list_runs(self, client: TestClient, auth: tuple[str, str]):
        resp = client.get("/api/v1/admin/assistant/prospect/runs", auth=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_list_runs_with_limit(self, client: TestClient, auth: tuple[str, str]):
        resp = client.get("/api/v1/admin/assistant/prospect/runs?limit=5&offset=0", auth=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["limit"] == 5
        assert data["offset"] == 0


# ---------------------------------------------------------------
# GET /api/v1/admin/assistant/prospect/runs/{run_id}
# ---------------------------------------------------------------
class TestAssistantGetRun:
    """Test get single run endpoint."""

    def test_get_run_not_found(self, client: TestClient, auth: tuple[str, str]):
        resp = client.get("/api/v1/admin/assistant/prospect/runs/nonexistent", auth=auth)
        assert resp.status_code == 404

    def test_get_existing_run(self, client: TestClient, auth: tuple[str, str]):
        # Create a run first
        create_resp = client.post(
            "/api/v1/admin/assistant/prospect/execute",
            json={"prompt": "Test run for detail", "max_leads": 5},
            auth=auth,
        )
        assert create_resp.status_code == 200, f"Setup failed: {create_resp.status_code} {create_resp.text}"
        run_id = create_resp.json()["id"]

        resp = client.get(f"/api/v1/admin/assistant/prospect/runs/{run_id}", auth=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == run_id
        assert "actions" in data


# ---------------------------------------------------------------
# POST /api/v1/admin/assistant/prospect/confirm
# ---------------------------------------------------------------
class TestAssistantConfirm:
    """Test confirm/reject endpoint."""

    def test_confirm_unknown_action_graceful(self, client: TestClient, auth: tuple[str, str]):
        resp = client.post(
            "/api/v1/admin/assistant/prospect/confirm",
            json={"action_ids": ["nonexistent_id"], "approve": True},
            auth=auth,
        )
        # Should succeed, but with no effect
        assert resp.status_code == 200

    def test_reject_actions(self, client: TestClient, auth: tuple[str, str]):
        resp = client.post(
            "/api/v1/admin/assistant/prospect/confirm",
            json={"action_ids": ["nonexistent_id"], "approve": False},
            auth=auth,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("rejected") is True
