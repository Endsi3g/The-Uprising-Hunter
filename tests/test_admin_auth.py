from __future__ import annotations


def test_admin_requires_auth(client):
    response = client.get("/admin")
    assert response.status_code == 401


def test_admin_accepts_valid_basic_auth(client):
    response = client.get("/admin", auth=("admin", "secret"))
    assert response.status_code == 200
    assert "Admin Dashboard" in response.text

