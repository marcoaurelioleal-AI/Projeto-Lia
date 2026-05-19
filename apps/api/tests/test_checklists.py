from __future__ import annotations

from collections.abc import Callable

from fastapi.testclient import TestClient


def test_manuals_and_checklists(client: TestClient, admin_headers: dict[str, str]) -> None:
    manuals = client.get("/api/manuals", headers=admin_headers)
    assert manuals.status_code == 200
    assert {manual["unit"] for manual in manuals.json()} == {"Lia Burguer", "Lia Pizza", "Lia Salgados"}

    checklists = client.get("/api/checklists", headers=admin_headers)
    assert checklists.status_code == 200
    runs = checklists.json()
    assert len(runs) == 3
    first_item = runs[0]["items"][0]
    updated = client.patch(
        f"/api/checklists/{runs[0]['id']}/items",
        headers=admin_headers,
        json={"item_id": first_item["id"], "done": True},
    )
    assert updated.status_code == 200
    assert updated.json()["completed"] == 1


def test_rbac_and_store_scope_for_operational_user(
    client: TestClient,
    admin_headers: dict[str, str],
    login_headers: Callable[[str, str], dict[str, str]],
) -> None:
    store = client.post("/api/admin/stores", headers=admin_headers, json={"name": "Lia RBAC"}).json()
    created_user = client.post(
        "/api/admin/users",
        headers=admin_headers,
        json={
            "username": "operador_rbac",
            "name": "Operador RBAC",
            "role": "operacao",
            "store_id": store["id"],
            "password": "senha123",
        },
    )
    assert created_user.status_code == 200

    operator = login_headers("operador_rbac", "senha123")

    admin_denied = client.get("/api/admin/users", headers=operator)
    assert admin_denied.status_code == 403

    own_store = client.get(f"/api/checklists?store={store['name']}", headers=operator)
    assert own_store.status_code == 200

    other_store = client.get("/api/checklists?store=Lia Pizza", headers=operator)
    assert other_store.status_code == 403
