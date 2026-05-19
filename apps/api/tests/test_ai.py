from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from apps.api.app.services.rag_service import RagService


def test_rag_retrieves_relevant_manual_context(client: TestClient, db_session: Session) -> None:
    response = client.get("/health")
    assert response.status_code == 200

    results = RagService(db_session).retrieve_context("temperatura do oleo para fritar salgados", limit=2)

    assert 0 < len(results) <= 2
    assert results[0].chunk.unit == "Lia Salgados"
    content = results[0].chunk.content.lower()
    assert "170" in content or "oleo" in content or "óleo" in content


def test_ai_offline_mode(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/ai/chat",
        headers=admin_headers,
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


def test_ai_logs_summarized_history(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/ai/chat",
        headers=admin_headers,
        json={
            "messages": [{"role": "user", "content": "Como conferir validade dos insumos?"}],
            "store": "Grupo Lia",
            "unit": "Lia Pizza",
        },
    )
    assert response.status_code == 200

    history = client.get("/api/ai/history", headers=admin_headers)
    assert history.status_code == 200
    items = history.json()
    assert items
    assert items[0]["session_id"] == response.json()["session_id"]
    assert items[0]["unit"] == "Lia Pizza"
    assert "validade" in items[0]["question"].lower()


def test_ai_accepts_response_modes_and_records_interaction(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/ai/chat",
        headers=admin_headers,
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

    interactions = client.get("/api/ai/interactions?response_mode=treinamento", headers=admin_headers)
    assert interactions.status_code == 200
    items = interactions.json()
    assert items
    assert items[0]["response_mode"] == "treinamento"
    assert items[0]["ai_mode"] in {"offline", "gemini", "error"}
    assert items[0]["sources"]
    assert items[0]["latency_ms"] >= 0


def test_ai_unknown_question_requires_manager_confirmation(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/ai/chat",
        headers=admin_headers,
        json={"messages": [{"role": "user", "content": "Como calibrar um foguete orbital?"}]},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["needs_manager_confirmation"] is True
    assert payload["sources"] == []


def test_ai_rejects_blank_question(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = client.post(
        "/api/ai/chat",
        headers=admin_headers,
        json={"messages": [{"role": "user", "content": "   "}]},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Pergunta da IA nao pode ser vazia"


def test_ai_requires_token(client: TestClient) -> None:
    response = client.post("/api/ai/chat", json={"messages": [{"role": "user", "content": "Oi"}]})
    assert response.status_code == 401
