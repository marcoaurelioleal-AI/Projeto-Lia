from __future__ import annotations

import os
from collections.abc import Callable, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["LIA_ADMIN_USER"] = "admin"
os.environ["LIA_ADMIN_PASSWORD"] = "admin123"
os.environ["LIA_LEADERSHIP_USER"] = "lideranca"
os.environ["LIA_LEADERSHIP_PASSWORD"] = "lider123"
os.environ.pop("OPENAI_API_KEY", None)
os.environ["GEMINI_API_KEY"] = "sua_nova_chave_gemini"
os.environ["CHAVE_API"] = "sua_nova_chave_gemini"

from apps.api.app.database import SessionLocal  # noqa: E402
from apps.api.app.main import app  # noqa: E402


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def login_headers(client: TestClient) -> Callable[[str, str], dict[str, str]]:
    def _login(username: str, password: str) -> dict[str, str]:
        response = client.post("/api/auth/login", json={"username": username, "password": password})
        assert response.status_code == 200
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _login


@pytest.fixture()
def admin_headers(login_headers: Callable[[str, str], dict[str, str]]) -> dict[str, str]:
    return login_headers("admin", "admin123")


@pytest.fixture()
def leadership_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/api/leadership/login", json={"username": "lideranca", "password": "lider123"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
