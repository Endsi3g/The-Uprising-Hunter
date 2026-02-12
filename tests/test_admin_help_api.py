from __future__ import annotations


def test_help_payload_shape(client):
    response = client.get("/api/v1/admin/help", auth=("admin", "secret"))
    assert response.status_code == 200
    payload = response.json()
    assert "support_email" in payload
    assert isinstance(payload["faqs"], list)
    assert isinstance(payload["links"], list)
    assert payload["faqs"]


def test_help_support_email_follows_settings(client):
    settings_payload = {
        "organization_name": "Prospect Support",
        "locale": "fr-FR",
        "timezone": "Europe/Paris",
        "default_page_size": 25,
        "dashboard_refresh_seconds": 30,
        "support_email": "helpdesk@example.com",
    }
    put_response = client.put(
        "/api/v1/admin/settings",
        auth=("admin", "secret"),
        json=settings_payload,
    )
    assert put_response.status_code == 200

    help_response = client.get("/api/v1/admin/help", auth=("admin", "secret"))
    assert help_response.status_code == 200
    assert help_response.json()["support_email"] == "helpdesk@example.com"

