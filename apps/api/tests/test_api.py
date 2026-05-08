from __future__ import annotations

import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["LIA_ADMIN_USER"] = "admin"
os.environ["LIA_ADMIN_PASSWORD"] = "admin123"
os.environ.pop("OPENAI_API_KEY", None)
os.environ["GEMINI_API_KEY"] = "sua_nova_chave_gemini"
os.environ["CHAVE_API"] = "sua_nova_chave_gemini"

from fastapi.testclient import TestClient  # noqa: E402

from apps.api.app.main import app  # noqa: E402


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_login_and_me() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["role"] == "admin"


def test_manuals_and_checklists() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        manuals = client.get("/manuals", headers=headers)
        assert manuals.status_code == 200
        assert {manual["unit"] for manual in manuals.json()} == {"Lia Burguer", "Lia Pizza", "Lia Salgados"}

        checklists = client.get("/checklists", headers=headers)
        assert checklists.status_code == 200
        runs = checklists.json()
        assert len(runs) == 3
        first_item = runs[0]["items"][0]
        updated = client.patch(
            f"/checklists/{runs[0]['id']}/items",
            headers=headers,
            json={"item_id": first_item["id"], "done": True},
        )
        assert updated.status_code == 200
        assert updated.json()["completed"] == 1


def test_ai_offline_mode() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        response = client.post(
            "/ai/chat",
            headers=headers,
            json={"messages": [{"role": "user", "content": "Qual temperatura da chapa?"}]},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["mode"] in {"offline", "error"}
        assert payload["session_id"]
        assert payload["sources"]
        assert payload["sources"][0]["unit"] in {"Lia Burguer", "Lia Pizza", "Lia Salgados"}


def test_ai_logs_summarized_history() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        response = client.post(
            "/ai/chat",
            headers=headers,
            json={
                "messages": [{"role": "user", "content": "Como conferir validade dos insumos?"}],
                "store": "Grupo Lia",
                "unit": "Lia Pizza",
            },
        )
        assert response.status_code == 200

        history = client.get("/ai/history", headers=headers)
        assert history.status_code == 200
        items = history.json()
        assert items
        assert items[0]["session_id"] == response.json()["session_id"]
        assert items[0]["unit"] == "Lia Pizza"
        assert "validade" in items[0]["question"].lower()


def test_ai_unknown_question_requires_manager_confirmation() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        response = client.post(
            "/ai/chat",
            headers=headers,
            json={"messages": [{"role": "user", "content": "Como calibrar um foguete orbital?"}]},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["needs_manager_confirmation"] is True
        assert payload["sources"] == []


def test_ai_requires_token() -> None:
    with TestClient(app) as client:
        response = client.post("/ai/chat", json={"messages": [{"role": "user", "content": "Oi"}]})
        assert response.status_code == 401
