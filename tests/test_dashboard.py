from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from dashboard.app import app
from dashboard.routes import eval as eval_route
from dashboard.routes import metrics as metrics_route

REPORT = {
    "measured_at": "2026-11-21T00:00:00+00:00", "model": "m",
    "agents": [{"agent": "ticket-triage", "version": "1.0.0", "owner": "o", "cases_passed": 7,
                "cases_total": 7, "generate_seconds": 0.1, "eval_seconds": 2.0,
                "compliance_checks_passed": 8, "compliance_checks_total": 8,
                "gate": {"pass_rate": 1.0, "blocked": False, "critical_violations": 0,
                         "minimum_pass_rate": 0.98, "critical_violations_allowed": 0,
                         "reasons": []},
                "economics": {"cost_per_successful_outcome_usd": 0.01}}],
    "summary": {"agents_total": 1, "agents_released": 1, "agents_blocked": [],
                "cases_total": 7, "cases_passed": 7, "total_cost_usd": 0.07,
                "cost_per_successful_outcome_usd": 0.01},
}


@pytest.fixture
def client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def test_health(client: httpx.AsyncClient) -> None:
    async with client as c:
        resp = await c.get("/health")
    assert resp.json()["status"] == "ok"


async def test_preview_lists_files_for_a_manifest(client: httpx.AsyncClient) -> None:
    async with client as c:
        resp = await c.post("/api/generate", json={"manifest": "refund-desk"})
    assert resp.status_code == 200
    assert "scenario/config.py" in resp.json()["files"]


async def test_preview_rejects_bad_names(client: httpx.AsyncClient) -> None:
    async with client as c:
        resp = await c.post("/api/generate", json={"manifest": "../etc"})
    assert resp.status_code == 400


async def test_preview_unknown_manifest_is_404(client: httpx.AsyncClient) -> None:
    async with client as c:
        resp = await c.post("/api/generate", json={"manifest": "no-such-agent"})
    assert resp.status_code == 404


async def test_metrics_unavailable_without_report(client: httpx.AsyncClient,
                                                  monkeypatch: pytest.MonkeyPatch,
                                                  tmp_path: Path) -> None:
    monkeypatch.setattr(metrics_route, "_REPORT", tmp_path / "missing.json")
    async with client as c:
        assert (await c.get("/api/metrics")).json()["available"] is False


async def test_metrics_serves_the_release_report(client: httpx.AsyncClient,
                                                 monkeypatch: pytest.MonkeyPatch,
                                                 tmp_path: Path) -> None:
    path = tmp_path / "release.json"
    path.write_text(json.dumps(REPORT))
    monkeypatch.setattr(metrics_route, "_REPORT", path)
    async with client as c:
        data = (await c.get("/api/metrics")).json()
    assert data["summary"]["cases_passed"] == 7
    assert data["agents"][0]["gate"]["blocked"] is False
    assert data["charts"]["cases_passed"].startswith("<svg")


async def test_eval_unavailable_without_report(client: httpx.AsyncClient,
                                               monkeypatch: pytest.MonkeyPatch,
                                               tmp_path: Path) -> None:
    monkeypatch.setattr(eval_route, "_REPORT", tmp_path / "missing.json")
    async with client as c:
        assert (await c.get("/api/eval")).json()["available"] is False
