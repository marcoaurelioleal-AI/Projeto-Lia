from __future__ import annotations

import os
from dataclasses import replace

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["LIA_ADMIN_USER"] = "admin"
os.environ["LIA_ADMIN_PASSWORD"] = "admin123"
os.environ["LIA_LEADERSHIP_USER"] = "lideranca"
os.environ["LIA_LEADERSHIP_PASSWORD"] = "lider123"
os.environ.pop("OPENAI_API_KEY", None)
os.environ["GEMINI_API_KEY"] = "sua_nova_chave_gemini"
os.environ["CHAVE_API"] = "sua_nova_chave_gemini"

from fastapi.testclient import TestClient  # noqa: E402

from apps.api.app.database import SessionLocal  # noqa: E402
from apps.api.app.config import settings, validate_production_settings  # noqa: E402
from apps.api.app.main import app  # noqa: E402
from apps.api.app.services.rag_service import RagService  # noqa: E402


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def leadership_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/api/leadership/login", json={"username": "lideranca", "password": "lider123"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_login_and_me() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["role"] == "admin"


def test_auth_cookie_session_and_logout() -> None:
    with TestClient(app) as client:
        login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        assert login.status_code == 200
        assert "httponly" in login.headers["set-cookie"].lower()

        me = client.get("/api/auth/me")
        assert me.status_code == 200
        assert me.json()["username"] == "admin"

        logout = client.post("/api/auth/logout")
        assert logout.status_code == 200

        expired = client.get("/api/auth/me")
        assert expired.status_code == 401


def test_leadership_cookie_session_and_logout() -> None:
    with TestClient(app) as client:
        login = client.post("/api/leadership/login", json={"username": "lideranca", "password": "lider123"})
        assert login.status_code == 200
        assert "httponly" in login.headers["set-cookie"].lower()

        me = client.get("/api/leadership/me")
        assert me.status_code == 200
        assert me.json()["area"] == "leadership"

        logout = client.post("/api/leadership/logout")
        assert logout.status_code == 200

        expired = client.get("/api/leadership/me")
        assert expired.status_code == 401


def test_production_settings_reject_sqlite_and_weak_secrets() -> None:
    unsafe = replace(
        settings,
        app_env="production",
        database_url="sqlite:///./lia.db",
        auto_create_tables=True,
        jwt_secret="lia-dev-secret-change-me",
        default_admin_password="admin123",
        leadership_password="lider123",
    )

    try:
        validate_production_settings(unsafe)
    except RuntimeError as exc:
        message = str(exc)
    else:
        raise AssertionError("production settings should reject unsafe configuration")

    assert "DATABASE_URL" in message
    assert "AUTO_CREATE_TABLES" in message
    assert "JWT_SECRET" in message
    assert "LIA_ADMIN_PASSWORD" in message
    assert "LIA_LEADERSHIP_PASSWORD" in message


def test_production_settings_accept_postgres_and_strong_secrets() -> None:
    safe = replace(
        settings,
        app_env="production",
        database_url="postgresql+psycopg://user:pass@host:5432/lia",
        auto_create_tables=False,
        jwt_secret="JwtSecretForteParaProducao123456789",
        default_admin_password="AdminSenhaForte123",
        leadership_password="LiderSenhaForte123",
        session_cookie_secure=True,
        storage_provider="supabase",
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="ServiceRoleForte123",
        supabase_storage_bucket="lia-evidences",
    )

    validate_production_settings(safe)


def test_manuals_and_checklists() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)
        manuals = client.get("/api/manuals", headers=headers)
        assert manuals.status_code == 200
        assert {manual["unit"] for manual in manuals.json()} == {"Lia Burguer", "Lia Pizza", "Lia Salgados"}

        checklists = client.get("/api/checklists", headers=headers)
        assert checklists.status_code == 200
        runs = checklists.json()
        assert len(runs) == 3
        first_item = runs[0]["items"][0]
        updated = client.patch(
            f"/api/checklists/{runs[0]['id']}/items",
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
            "/api/ai/chat",
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
            "/api/ai/chat",
            headers=headers,
            json={
                "messages": [{"role": "user", "content": "Como conferir validade dos insumos?"}],
                "store": "Grupo Lia",
                "unit": "Lia Pizza",
            },
        )
        assert response.status_code == 200

        history = client.get("/api/ai/history", headers=headers)
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
            "/api/ai/chat",
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

        interactions = client.get("/api/ai/interactions?response_mode=treinamento", headers=headers)
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
            "/api/ai/chat",
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
            "/api/ai/chat",
            headers=headers,
            json={"messages": [{"role": "user", "content": "   "}]},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Pergunta da IA nao pode ser vazia"


def test_ai_requires_token() -> None:
    with TestClient(app) as client:
        response = client.post("/api/ai/chat", json={"messages": [{"role": "user", "content": "Oi"}]})
        assert response.status_code == 401


def test_leadership_area_requires_dedicated_login_and_records_employee_feedback() -> None:
    with TestClient(app) as client:
        no_token = client.get("/api/leadership/employees")
        assert no_token.status_code == 401

        invalid_login = client.post("/api/leadership/login", json={"username": "admin", "password": "admin123"})
        assert invalid_login.status_code == 401

        headers = leadership_headers(client)
        me = client.get("/api/leadership/me", headers=headers)
        assert me.status_code == 200
        assert me.json()["area"] == "leadership"

        employee = client.post(
            "/api/leadership/employees",
            headers=headers,
            json={"name": "Funcionario Teste", "store": "Lia Burguer", "position": "Atendente"},
        )
        assert employee.status_code == 200
        employee_payload = employee.json()
        assert employee_payload["name"] == "Funcionario Teste"
        assert employee_payload["record_count"] == 0

        record = client.post(
            f"/api/leadership/employees/{employee_payload['id']}/records",
            headers=headers,
            json={
                "record_type": "advertencia",
                "description": "Advertencia aplicada por quebra de procedimento.",
                "applied_at": "2026-05-16",
            },
        )
        assert record.status_code == 200
        assert record.json()["record_type"] == "advertencia"
        assert record.json()["employee_name"] == "Funcionario Teste"

        records = client.get("/api/leadership/records", headers=headers)
        assert records.status_code == 200
        assert any(item["employee_name"] == "Funcionario Teste" for item in records.json())


def test_admin_can_manage_users_and_stores() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)

        created_store = client.post("/api/admin/stores", headers=headers, json={"name": "Lia Teste"})
        assert created_store.status_code == 200
        store_id = created_store.json()["id"]

        created_user = client.post(
            "/api/admin/users",
            headers=headers,
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

        promoted = client.patch(f"/api/admin/users/{user_id}", headers=headers, json={"role": "admin"})
        assert promoted.status_code == 200
        assert promoted.json()["role"] == "admin"

        disabled_user = client.delete(f"/api/admin/users/{user_id}", headers=headers)
        assert disabled_user.status_code == 200
        assert disabled_user.json()["active"] is False

        renamed = client.patch(f"/api/admin/stores/{store_id}", headers=headers, json={"name": "Lia Teste 2"})
        assert renamed.status_code == 200
        assert renamed.json()["name"] == "Lia Teste 2"

        disabled_store = client.delete(f"/api/admin/stores/{store_id}", headers=headers)
        assert disabled_store.status_code == 200
        assert disabled_store.json()["active"] is False


def test_rbac_and_store_scope_for_operational_user() -> None:
    with TestClient(app) as client:
        admin = auth_headers(client)
        store = client.post("/api/admin/stores", headers=admin, json={"name": "Lia RBAC"}).json()
        created_user = client.post(
            "/api/admin/users",
            headers=admin,
            json={
                "username": "operador_rbac",
                "name": "Operador RBAC",
                "role": "operacao",
                "store_id": store["id"],
                "password": "senha123",
            },
        )
        assert created_user.status_code == 200

        login = client.post("/api/auth/login", json={"username": "operador_rbac", "password": "senha123"})
        assert login.status_code == 200
        token = login.json()["access_token"]
        operator = {"Authorization": f"Bearer {token}"}

        admin_denied = client.get("/api/admin/users", headers=operator)
        assert admin_denied.status_code == 403

        own_store = client.get(f"/api/checklists?store={store['name']}", headers=operator)
        assert own_store.status_code == 200

        other_store = client.get("/api/checklists?store=Lia Pizza", headers=operator)
        assert other_store.status_code == 403


def test_auditor_can_view_reports_and_audit_but_not_create_user() -> None:
    with TestClient(app) as client:
        admin = auth_headers(client)
        created = client.post(
            "/api/admin/users",
            headers=admin,
            json={
                "username": "auditor_teste",
                "name": "Auditor Teste",
                "role": "auditor",
                "password": "senha123",
            },
        )
        assert created.status_code == 200

        login = client.post("/api/auth/login", json={"username": "auditor_teste", "password": "senha123"})
        assert login.status_code == 200
        auditor = {"Authorization": f"Bearer {login.json()['access_token']}"}

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


def test_evidences_are_restricted_by_user_store() -> None:
    with TestClient(app) as client:
        admin = auth_headers(client)
        store_a = client.post("/api/admin/stores", headers=admin, json={"name": "Lia Evid A"}).json()
        store_b = client.post("/api/admin/stores", headers=admin, json={"name": "Lia Evid B"}).json()

        user_b = client.post(
            "/api/admin/users",
            headers=admin,
            json={
                "username": "operador_evid_b",
                "name": "Operador Evid B",
                "role": "operacao",
                "store_id": store_b["id"],
                "password": "senha123",
            },
        )
        assert user_b.status_code == 200

        runs = client.get(f"/api/checklists?store={store_a['name']}", headers=admin).json()
        item_id = runs[0]["items"][0]["id"]
        uploaded = client.post(
            f"/api/checklists/items/{item_id}/evidences",
            headers=admin,
            files={"file": ("evidencia.png", b"fake-image", "image/png")},
        )
        assert uploaded.status_code == 200
        evidence_id = uploaded.json()["id"]

        login_b = client.post("/api/auth/login", json={"username": "operador_evid_b", "password": "senha123"})
        operator_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

        denied_list = client.get(f"/api/checklists/items/{item_id}/evidences", headers=operator_b)
        assert denied_list.status_code == 403

        denied_file = client.get(f"/api/evidences/{evidence_id}/file", headers=operator_b, follow_redirects=False)
        assert denied_file.status_code == 403

        admin_file = client.get(f"/api/evidences/{evidence_id}/file", headers=admin)
        assert admin_file.status_code == 200


def test_admin_can_manage_checklist_templates() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)

        created = client.post(
            "/api/admin/checklist-templates",
            headers=headers,
            json={"title": "Checklist Teste", "category": "teste", "store": "Grupo Lia"},
        )
        assert created.status_code == 200
        template_id = created.json()["id"]

        with_item = client.post(
            f"/api/admin/checklist-templates/{template_id}/items",
            headers=headers,
            json={"section": "Abertura", "text": "Conferir item de teste"},
        )
        assert with_item.status_code == 200
        item = with_item.json()["items"][0]
        assert item["active"] is True

        disabled_item = client.delete(f"/api/admin/checklist-template-items/{item['id']}", headers=headers)
        assert disabled_item.status_code == 200
        assert disabled_item.json()["items"][0]["active"] is False

        disabled_template = client.delete(f"/api/admin/checklist-templates/{template_id}", headers=headers)
        assert disabled_template.status_code == 200
        assert disabled_template.json()["active"] is False


def test_admin_can_manage_manuals() -> None:
    with TestClient(app) as client:
        headers = auth_headers(client)

        created = client.post(
            "/api/admin/manuals",
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

        updated = client.patch(f"/api/admin/manuals/{manual_id}", headers=headers, json={"temperature": "190C"})
        assert updated.status_code == 200
        assert updated.json()["temperature"] == "190C"

        with_section = client.post(f"/api/admin/manuals/{manual_id}/sections", headers=headers, json={"title": "Abertura"})
        assert with_section.status_code == 200
        section = with_section.json()["sections"][0]

        with_step = client.post(
            f"/api/admin/manual-sections/{section['id']}/steps",
            headers=headers,
            json={"text": "Conferir bancada antes de iniciar."},
        )
        assert with_step.status_code == 200
        step = with_step.json()["sections"][0]["steps"][0]

        disabled_step = client.delete(f"/api/admin/manual-steps/{step['id']}", headers=headers)
        assert disabled_step.status_code == 200
        assert disabled_step.json()["sections"][0]["steps"][0]["active"] is False

        disabled_manual = client.delete(f"/api/admin/manuals/{manual_id}", headers=headers)
        assert disabled_manual.status_code == 200
        assert disabled_manual.json()["active"] is False
