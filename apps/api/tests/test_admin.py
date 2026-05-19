from __future__ import annotations

from fastapi.testclient import TestClient


def test_admin_can_manage_users_and_stores(client: TestClient, admin_headers: dict[str, str]) -> None:
    created_store = client.post("/api/admin/stores", headers=admin_headers, json={"name": "Lia Teste"})
    assert created_store.status_code == 200
    store_id = created_store.json()["id"]

    created_user = client.post(
        "/api/admin/users",
        headers=admin_headers,
        json={
            "username": "operador_teste",
            "name": "Operador Teste",
            "role": "operacao",
            "store_id": store_id,
            "password": "senha123",
        },
    )
    assert created_user.status_code == 200
    user_id = created_user.json()["id"]
    assert created_user.json()["store_id"] == store_id

    promoted = client.patch(f"/api/admin/users/{user_id}", headers=admin_headers, json={"role": "admin"})
    assert promoted.status_code == 200
    assert promoted.json()["role"] == "admin"

    disabled_user = client.delete(f"/api/admin/users/{user_id}", headers=admin_headers)
    assert disabled_user.status_code == 200
    assert disabled_user.json()["active"] is False

    renamed = client.patch(f"/api/admin/stores/{store_id}", headers=admin_headers, json={"name": "Lia Teste 2"})
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Lia Teste 2"

    disabled_store = client.delete(f"/api/admin/stores/{store_id}", headers=admin_headers)
    assert disabled_store.status_code == 200
    assert disabled_store.json()["active"] is False


def test_admin_can_manage_checklist_templates(client: TestClient, admin_headers: dict[str, str]) -> None:
    created = client.post(
        "/api/admin/checklist-templates",
        headers=admin_headers,
        json={"title": "Checklist Teste", "category": "teste", "store": "Grupo Lia"},
    )
    assert created.status_code == 200
    template_id = created.json()["id"]

    with_item = client.post(
        f"/api/admin/checklist-templates/{template_id}/items",
        headers=admin_headers,
        json={"section": "Abertura", "text": "Conferir item de teste"},
    )
    assert with_item.status_code == 200
    item = with_item.json()["items"][0]
    assert item["active"] is True

    disabled_item = client.delete(f"/api/admin/checklist-template-items/{item['id']}", headers=admin_headers)
    assert disabled_item.status_code == 200
    assert disabled_item.json()["items"][0]["active"] is False

    disabled_template = client.delete(f"/api/admin/checklist-templates/{template_id}", headers=admin_headers)
    assert disabled_template.status_code == 200
    assert disabled_template.json()["active"] is False


def test_admin_can_manage_manuals(client: TestClient, admin_headers: dict[str, str]) -> None:
    created = client.post(
        "/api/admin/manuals",
        headers=admin_headers,
        json={
            "unit": "Lia Manual Teste",
            "title": "Manual Teste",
            "temperature": "180C",
            "time_standard": "5 min",
            "critical_point": "Conferir padrao",
            "tip": "Registrar ajuste",
        },
    )
    assert created.status_code == 200
    manual_id = created.json()["id"]

    updated = client.patch(f"/api/admin/manuals/{manual_id}", headers=admin_headers, json={"temperature": "190C"})
    assert updated.status_code == 200
    assert updated.json()["temperature"] == "190C"

    with_section = client.post(f"/api/admin/manuals/{manual_id}/sections", headers=admin_headers, json={"title": "Abertura"})
    assert with_section.status_code == 200
    section = with_section.json()["sections"][0]

    with_step = client.post(
        f"/api/admin/manual-sections/{section['id']}/steps",
        headers=admin_headers,
        json={"text": "Conferir bancada antes de iniciar."},
    )
    assert with_step.status_code == 200
    step = with_step.json()["sections"][0]["steps"][0]

    disabled_step = client.delete(f"/api/admin/manual-steps/{step['id']}", headers=admin_headers)
    assert disabled_step.status_code == 200
    assert disabled_step.json()["sections"][0]["steps"][0]["active"] is False

    disabled_manual = client.delete(f"/api/admin/manuals/{manual_id}", headers=admin_headers)
    assert disabled_manual.status_code == 200
    assert disabled_manual.json()["active"] is False
