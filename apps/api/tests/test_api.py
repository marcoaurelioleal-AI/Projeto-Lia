from __future__ import annotations

import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["LIA_ADMIN_USER"] = "admin"
os.environ["LIA_ADMIN_PASSWORD"] = "admin123"
os.environ.pop("OPENAI_API_KEY", None)
os.environ["GEMINI_API_KEY"] = "sua_nova_chave_gemini"
os.environ["CHAVE_API"] = "sua_nova_chave_gemini"

from fastapi.testclient import TestClient  # noqa: E402

from apps.api.app.database import SessionLocal  # noqa: E402
from apps.api.app.main import app  # noqa: E402
from apps.api.app.services.rag_service import RagService  # noqa: E402


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


def test_rag_retrieves_relevant_manual_context() -> None:
    with TestClient(app):
        db = SessionLocal()
        try:
            results = RagService(db).retrieve_context("temperatura do oleo para fritar salgados", limit=2)
        finally:
            db.close()

    assert 0 < len(results) <= 2
    assert results[0].chunk.unit == "Lia Salgados"
    assert "170" in results[0].chunk.content or "oleo" in results[0].chunk.content.lower()


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
        assert payload["response_mode"] == "rapido"
        assert payload["session_id"]
        assert payload["sources"]
        assert payload["sources"][0]["source_type"] == "manual"
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


def test_ai_accepts_response_modes_and_records_interaction() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        response = client.post(
            "/ai/chat",
            headers=headers,
            json={
                "messages": [{"role": "user", "content": "Como treinar alguem para fritar salgados?"}],
                "unit": "Lia Salgados",
                "response_mode": "treinamento",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["response_mode"] == "treinamento"
        assert payload["sources"]

        interactions = client.get("/ai/interactions?response_mode=treinamento", headers=headers)
        assert interactions.status_code == 200
        items = interactions.json()
        assert items
        assert items[0]["response_mode"] == "treinamento"
        assert items[0]["ai_mode"] in {"offline", "gemini", "error"}
        assert items[0]["sources"]
        assert items[0]["latency_ms"] >= 0


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


def test_ai_rejects_blank_question() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        response = client.post(
            "/ai/chat",
            headers=headers,
            json={"messages": [{"role": "user", "content": "   "}]},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Pergunta da IA nao pode ser vazia"


def test_ai_requires_token() -> None:
    with TestClient(app) as client:
        response = client.post("/ai/chat", json={"messages": [{"role": "user", "content": "Oi"}]})
        assert response.status_code == 401


def test_admin_can_manage_users_and_stores() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)

        created_user = client.post(
            "/admin/users",
            headers=headers,
            json={"username": "operador_teste", "name": "Operador Teste", "role": "operacao", "password": "senha123"},
        )
        assert created_user.status_code == 200
        user_id = created_user.json()["id"]

        promoted = client.patch(f"/admin/users/{user_id}", headers=headers, json={"role": "admin"})
        assert promoted.status_code == 200
        assert promoted.json()["role"] == "admin"

        disabled_user = client.delete(f"/admin/users/{user_id}", headers=headers)
        assert disabled_user.status_code == 200
        assert disabled_user.json()["active"] is False

        created_store = client.post("/admin/stores", headers=headers, json={"name": "Lia Teste"})
        assert created_store.status_code == 200
        store_id = created_store.json()["id"]

        renamed = client.patch(f"/admin/stores/{store_id}", headers=headers, json={"name": "Lia Teste 2"})
        assert renamed.status_code == 200
        assert renamed.json()["name"] == "Lia Teste 2"

        disabled_store = client.delete(f"/admin/stores/{store_id}", headers=headers)
        assert disabled_store.status_code == 200
        assert disabled_store.json()["active"] is False


def test_admin_can_manage_checklist_templates() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)

        created = client.post(
            "/admin/checklist-templates",
            headers=headers,
            json={"title": "Checklist Teste", "category": "teste", "store": "Grupo Lia"},
        )
        assert created.status_code == 200
        template_id = created.json()["id"]

        with_item = client.post(
            f"/admin/checklist-templates/{template_id}/items",
            headers=headers,
            json={"section": "Abertura", "text": "Conferir item de teste"},
        )
        assert with_item.status_code == 200
        item = with_item.json()["items"][0]
        assert item["active"] is True

        disabled_item = client.delete(f"/admin/checklist-template-items/{item['id']}", headers=headers)
        assert disabled_item.status_code == 200
        assert disabled_item.json()["items"][0]["active"] is False

        disabled_template = client.delete(f"/admin/checklist-templates/{template_id}", headers=headers)
        assert disabled_template.status_code == 200
        assert disabled_template.json()["active"] is False


def test_admin_can_manage_manuals() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)

        created = client.post(
            "/admin/manuals",
            headers=headers,
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

        updated = client.patch(f"/admin/manuals/{manual_id}", headers=headers, json={"temperature": "190C"})
        assert updated.status_code == 200
        assert updated.json()["temperature"] == "190C"

        with_section = client.post(f"/admin/manuals/{manual_id}/sections", headers=headers, json={"title": "Abertura"})
        assert with_section.status_code == 200
        section = with_section.json()["sections"][0]

        with_step = client.post(
            f"/admin/manual-sections/{section['id']}/steps",
            headers=headers,
            json={"text": "Conferir bancada antes de iniciar."},
        )
        assert with_step.status_code == 200
        step = with_step.json()["sections"][0]["steps"][0]

        disabled_step = client.delete(f"/admin/manual-steps/{step['id']}", headers=headers)
        assert disabled_step.status_code == 200
        assert disabled_step.json()["sections"][0]["steps"][0]["active"] is False

        disabled_manual = client.delete(f"/admin/manuals/{manual_id}", headers=headers)
        assert disabled_manual.status_code == 200
        assert disabled_manual.json()["active"] is False
