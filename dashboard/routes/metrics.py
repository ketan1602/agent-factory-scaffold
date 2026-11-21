from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from dashboard.charts import pass_chart

router = APIRouter()

_REPORT = Path(__file__).parent.parent.parent / "measurements" / "release.json"


@router.get("/api/metrics")
async def metrics() -> JSONResponse:
    if not _REPORT.exists():
        return JSONResponse(content={"available": False,
                                     "message": "No release run yet. Run agent-factory release."})
    report = json.loads(_REPORT.read_text())
    summary = report["summary"]
    return JSONResponse(content={
        "available": True,
        "measured_at": report["measured_at"],
        "model": report["model"],
        "summary": summary,
        "agents": [{k: a[k] for k in ("agent", "version", "owner", "cases_passed", "cases_total",
                                      "gate", "economics", "generate_seconds", "eval_seconds",
                                      "compliance_checks_passed", "compliance_checks_total")}
                   for a in report["agents"]],
        "charts": {"cases_passed": pass_chart(summary["cases_passed"], summary["cases_total"])},
    })
