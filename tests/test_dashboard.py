from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from dashboard.app import app
from dashboard.routes import eval as eval_route
from dashboard.routes import metrics as metrics_route


@pytest.fixture
def client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def test_health(client: httpx.AsyncClient) -> None:
    async with client as c:
        resp = await c.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_generate_dry_run_lists_files(client: httpx.AsyncClient) -> None:
    async with client as c:
        resp = await c.post("/api/generate", json={"name": "support-east"})
    assert resp.status_code == 200
    assert "scenario/support.py" in resp.json()["files"]


async def test_generate_rejects_invalid_name(client: httpx.AsyncClient) -> None:
    async with client as c:
        resp = await c.post("/api/generate", json={"name": "Bad Name"})
    assert resp.status_code == 400
    assert "Invalid agent name" in resp.json()["detail"]


async def test_metrics_reports_unavailable_without_file(client: httpx.AsyncClient,
                                                        monkeypatch: pytest.MonkeyPatch,
                                                        tmp_path: Path) -> None:
    monkeypatch.setattr(metrics_route, "_MEASUREMENTS", tmp_path / "missing.json")
    async with client as c:
        resp = await c.get("/api/metrics")
    assert resp.json()["available"] is False


async def test_metrics_serves_measured_values(client: httpx.AsyncClient,
                                              monkeypatch: pytest.MonkeyPatch,
                                              tmp_path: Path) -> None:
    path = tmp_path / "m.json"
    path.write_text(json.dumps({"time_to_eval_minutes": 2.5, "cases_passed": 15,
                                "cases_total": 16, "total_tokens": 100}))
    monkeypatch.setattr(metrics_route, "_MEASUREMENTS", path)
    async with client as c:
        data = (await c.get("/api/metrics")).json()
    assert data["available"] is True
    assert data["time_to_eval_minutes"] == 2.5
    assert data["charts"]["cases_passed"].startswith("<svg")


async def test_eval_reports_unavailable_without_results(client: httpx.AsyncClient,
                                                        monkeypatch: pytest.MonkeyPatch,
                                                        tmp_path: Path) -> None:
    monkeypatch.setattr(eval_route, "_RESULTS", tmp_path / "missing.json")
    async with client as c:
        assert (await c.get("/api/eval")).json()["available"] is False
