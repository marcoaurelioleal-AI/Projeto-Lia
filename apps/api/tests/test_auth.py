from __future__ import annotations

from dataclasses import replace

from fastapi.testclient import TestClient

from apps.api.app.config import settings, validate_production_settings


def test_login_and_me(client: TestClient, admin_headers: dict[str, str]) -> None:
    response = client.get("/api/auth/me", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_auth_cookie_session_and_logout(client: TestClient) -> None:
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


def test_leadership_cookie_session_and_logout(client: TestClient) -> None:
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
