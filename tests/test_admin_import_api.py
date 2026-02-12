from __future__ import annotations


def test_csv_import_preview_leads(client):
    csv_payload = (
        "first_name,last_name,email,company_name,status,segment\n"
        "Alice,Dupont,alice@example.com,Acme,NEW,SMB\n"
        "Bob,Martin,bob@example.com,Globex,CONTACTED,ENT\n"
    )
    response = client.post(
        "/api/v1/admin/import/csv/preview",
        auth=("admin", "secret"),
        files={"file": ("leads.csv", csv_payload, "text/csv")},
        data={"table": "leads"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["selected_table"] == "leads"
    assert payload["total_rows"] == 2
    assert payload["valid_rows"] == 2
    assert payload["invalid_rows"] == 0
    assert len(payload["preview"]) >= 1


def test_csv_import_commit_leads(client):
    csv_payload = (
        "first_name,last_name,email,company_name,status,segment\n"
        "Nina,Lopez,nina@example.com,Acme,NEW,SMB\n"
        "Rene,Lopez,rene@example.com,Acme,INTERESTED,ENT\n"
    )
    commit_response = client.post(
        "/api/v1/admin/import/csv/commit",
        auth=("admin", "secret"),
        files={"file": ("leads.csv", csv_payload, "text/csv")},
        data={"table": "leads"},
    )
    assert commit_response.status_code == 200
    commit_payload = commit_response.json()
    assert commit_payload["table"] == "leads"
    assert commit_payload["created"] == 2
    assert commit_payload["skipped"] == 0

    leads_response = client.get(
        "/api/v1/admin/leads?page=1&page_size=100",
        auth=("admin", "secret"),
    )
    assert leads_response.status_code == 200
    emails = {item["email"] for item in leads_response.json()["items"]}
    assert "nina@example.com" in emails
    assert "rene@example.com" in emails
