from __future__ import annotations

from collections.abc import Callable

from fastapi.testclient import TestClient


def test_auditor_can_view_reports_and_audit_but_not_create_user(
    client: TestClient,
    admin_headers: dict[str, str],
    login_headers: Callable[[str, str], dict[str, str]],
) -> None:
    created = client.post(
        "/api/admin/users",
        headers=admin_headers,
        json={
            "username": "auditor_teste",
            "name": "Auditor Teste",
            "role": "auditor",
            "password": "senha123",
        },
    )
    assert created.status_code == 200

    auditor = login_headers("auditor_teste", "senha123")

    report = client.get("/api/reports/summary", headers=auditor)
    assert report.status_code == 200

    audit = client.get("/api/evidences", headers=auditor)
    assert audit.status_code == 200

    denied = client.post(
        "/api/admin/users",
        headers=auditor,
        json={"username": "xpto", "name": "Xpto", "role": "operacao", "password": "senha123"},
    )
    assert denied.status_code == 403


def test_evidences_are_restricted_by_user_store(
    client: TestClient,
    admin_headers: dict[str, str],
    login_headers: Callable[[str, str], dict[str, str]],
) -> None:
    store_a = client.post("/api/admin/stores", headers=admin_headers, json={"name": "Lia Evid A"}).json()
    store_b = client.post("/api/admin/stores", headers=admin_headers, json={"name": "Lia Evid B"}).json()

    user_b = client.post(
        "/api/admin/users",
        headers=admin_headers,
        json={
            "username": "operador_evid_b",
            "name": "Operador Evid B",
            "role": "operacao",
            "store_id": store_b["id"],
            "password": "senha123",
        },
    )
    assert user_b.status_code == 200

    runs = client.get(f"/api/checklists?store={store_a['name']}", headers=admin_headers).json()
    item_id = runs[0]["items"][0]["id"]
    uploaded = client.post(
        f"/api/checklists/items/{item_id}/evidences",
        headers=admin_headers,
        files={"file": ("evidencia.png", b"fake-image", "image/png")},
    )
    assert uploaded.status_code == 200
    evidence_id = uploaded.json()["id"]

    operator_b = login_headers("operador_evid_b", "senha123")

    denied_list = client.get(f"/api/checklists/items/{item_id}/evidences", headers=operator_b)
    assert denied_list.status_code == 403

    denied_file = client.get(f"/api/evidences/{evidence_id}/file", headers=operator_b, follow_redirects=False)
    assert denied_file.status_code == 403

    admin_file = client.get(f"/api/evidences/{evidence_id}/file", headers=admin_headers)
    assert admin_file.status_code == 200


def test_write_requests_are_recorded_in_audit_log(client: TestClient, admin_headers: dict[str, str]) -> None:
    created = client.post("/api/admin/stores", headers=admin_headers, json={"name": "Lia Auditavel"})
    assert created.status_code == 200

    logs = client.get("/api/audit/logs?entity_type=admin&limit=20", headers=admin_headers)
    assert logs.status_code == 200
    items = logs.json()
    assert any(item["action"] == "POST /api/admin/stores" for item in items)
    created_store_log = next(item for item in items if item["action"] == "POST /api/admin/stores")
    assert created_store_log["actor_username"] == "admin"
    assert created_store_log["actor_role"] == "admin"
    assert created_store_log["status"] == "success"
    assert created_store_log["request_id"]
    assert created_store_log["details"]["status_code"] == 200


def test_audit_logs_require_view_audit_permission(
    client: TestClient,
    admin_headers: dict[str, str],
    login_headers: Callable[[str, str], dict[str, str]],
) -> None:
    store = client.post("/api/admin/stores", headers=admin_headers, json={"name": "Lia Audit Denied"}).json()
    created = client.post(
        "/api/admin/users",
        headers=admin_headers,
        json={
            "username": "operador_audit_denied",
            "name": "Operador Audit Denied",
            "role": "operacao",
            "store_id": store["id"],
            "password": "senha123",
        },
    )
    assert created.status_code == 200

    operator = login_headers("operador_audit_denied", "senha123")
    denied = client.get("/api/audit/logs", headers=operator)
    assert denied.status_code == 403
