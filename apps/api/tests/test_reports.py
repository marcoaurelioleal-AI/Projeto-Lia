from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient


def test_report_summary_returns_operational_indicators(client: TestClient, admin_headers: dict[str, str]) -> None:
    today = date.today().isoformat()

    response = client.get(
        f"/api/reports/summary?start_date={today}&end_date={today}",
        headers=admin_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_checklists"] >= 0
    assert payload["total_items"] >= payload["completed_items"]
    assert "aberta" in payload["incidents_by_status"] or payload["total_incidents"] == 0
