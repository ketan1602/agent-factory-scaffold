from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from dashboard.app import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "agent-factory-scaffold"


def test_generate_endpoint_dry_run(client: TestClient) -> None:
    response = client.post(
        "/api/generate",
        json={"name": "test-agent", "domain": "retail"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "files" in data
    assert len(data["files"]) == 8
    assert "duration_seconds" in data
    assert "file_tree" in data
    assert "compliance" in data
    assert len(data["compliance"]) == 8


def test_generate_endpoint_unknown_domain(client: TestClient) -> None:
    response = client.post(
        "/api/generate",
        json={"name": "test-agent", "domain": "unknown-domain"},
    )
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data


def test_metrics_endpoint(client: TestClient) -> None:
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "factory_time_to_first_agent_minutes" in data
    assert data["factory_time_to_first_agent_minutes"] == 28
    assert "charts" in data
    assert "time_comparison" in data["charts"]
    assert "decisions" in data["charts"]


def test_eval_endpoint(client: TestClient) -> None:
    response = client.get("/api/eval")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert len(data["agents"]) == 8
    assert all(a["passed"] for a in data["agents"])
    assert data["summary"]["compliance_pct"] == 100.0
