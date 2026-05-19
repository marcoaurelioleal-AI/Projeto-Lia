from __future__ import annotations

from fastapi.testclient import TestClient


def test_leadership_area_requires_dedicated_login_and_records_employee_feedback(
    client: TestClient,
) -> None:
    no_token = client.get("/api/leadership/employees")
    assert no_token.status_code == 401

    invalid_login = client.post("/api/leadership/login", json={"username": "admin", "password": "admin123"})
    assert invalid_login.status_code == 401

    login = client.post("/api/leadership/login", json={"username": "lideranca", "password": "lider123"})
    assert login.status_code == 200
    leadership_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    me = client.get("/api/leadership/me", headers=leadership_headers)
    assert me.status_code == 200
    assert me.json()["area"] == "leadership"

    employee = client.post(
        "/api/leadership/employees",
        headers=leadership_headers,
        json={"name": "Funcionario Teste", "store": "Lia Burguer", "position": "Atendente"},
    )
    assert employee.status_code == 200
    employee_payload = employee.json()
    assert employee_payload["name"] == "Funcionario Teste"
    assert employee_payload["record_count"] == 0

    record = client.post(
        f"/api/leadership/employees/{employee_payload['id']}/records",
        headers=leadership_headers,
        json={
            "record_type": "advertencia",
            "description": "Advertencia aplicada por quebra de procedimento.",
            "applied_at": "2026-05-16",
        },
    )
    assert record.status_code == 200
    assert record.json()["record_type"] == "advertencia"
    assert record.json()["employee_name"] == "Funcionario Teste"

    records = client.get("/api/leadership/records", headers=leadership_headers)
    assert records.status_code == 200
    assert any(item["employee_name"] == "Funcionario Teste" for item in records.json())
