from __future__ import annotations


def test_tasks_crud_flow(client):
    create_payload = {
        "title": "Relancer lead inbound",
        "status": "To Do",
        "priority": "Medium",
        "assigned_to": "Vous",
    }
    create_response = client.post(
        "/api/v1/admin/tasks",
        auth=("admin", "secret"),
        json=create_payload,
    )
    assert create_response.status_code == 200
    created = create_response.json()
    assert created["title"] == create_payload["title"]
    assert created["id"]

    update_response = client.patch(
        f"/api/v1/admin/tasks/{created['id']}",
        auth=("admin", "secret"),
        json={"status": "Done", "priority": "High"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["status"] == "Done"
    assert updated["priority"] == "High"

    delete_response = client.delete(
        f"/api/v1/admin/tasks/{created['id']}",
        auth=("admin", "secret"),
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted"] is True
