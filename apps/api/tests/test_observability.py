from __future__ import annotations

from fastapi.testclient import TestClient


def test_observability_status_requires_audit_permission(client: TestClient) -> None:
    response = client.get("/api/observability/status")
    assert response.status_code == 401
    assert response.headers["X-Request-ID"]


def test_observability_status_exposes_safe_runtime_snapshot(
    client: TestClient,
    admin_headers: dict[str, str],
) -> None:
    response = client.get("/api/observability/status", headers=admin_headers)

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "Projeto LIA API"
    assert payload["environment"] == "development"
    assert payload["database"] == "sqlite"
    assert payload["storage_provider"] == "local"
    assert payload["request_metrics"]["total_requests"] >= 1
    assert "/api/auth/login" in payload["request_metrics"]["by_path"]
