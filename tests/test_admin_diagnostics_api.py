from __future__ import annotations

import importlib


def _app_module():
    return importlib.import_module("src.admin.app")


def test_diagnostics_run_endpoint(client, monkeypatch):
    called = {"auto_fix": None}

    def fake_run_intelligent_diagnostics(*, auto_fix: bool):
        called["auto_fix"] = auto_fix
        return {"ok": True, "auto_fix": auto_fix}

    monkeypatch.setattr(_app_module(), "run_intelligent_diagnostics", fake_run_intelligent_diagnostics)

    response = client.post(
        "/api/v1/admin/diagnostics/run",
        auth=("admin", "secret"),
        json={"auto_fix": False},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert called["auto_fix"] is False


def test_autofix_run_endpoint(client, monkeypatch):
    called = {"auto_fix": None}

    def fake_run_intelligent_diagnostics(*, auto_fix: bool):
        called["auto_fix"] = auto_fix
        return {"ok": True, "auto_fix": auto_fix}

    monkeypatch.setattr(_app_module(), "run_intelligent_diagnostics", fake_run_intelligent_diagnostics)

    response = client.post(
        "/api/v1/admin/autofix/run",
        auth=("admin", "secret"),
    )
    assert response.status_code == 200
    assert response.json()["auto_fix"] is True
    assert called["auto_fix"] is True


def test_diagnostics_latest_endpoint(client, monkeypatch):
    def fake_get_latest() -> dict[str, object]:
        return {"available": True, "ok": True, "artifact": "x"}

    monkeypatch.setattr(_app_module(), "get_latest_diagnostics", fake_get_latest)
    response = client.get("/api/v1/admin/diagnostics/latest", auth=("admin", "secret"))
    assert response.status_code == 200
    assert response.json()["available"] is True


def test_autofix_latest_endpoint(client, monkeypatch):
    def fake_get_latest() -> dict[str, object]:
        return {"available": True, "ok": False, "artifact": "y"}

    monkeypatch.setattr(_app_module(), "get_latest_autofix", fake_get_latest)
    response = client.get("/api/v1/admin/autofix/latest", auth=("admin", "secret"))
    assert response.status_code == 200
    assert response.json()["available"] is True
