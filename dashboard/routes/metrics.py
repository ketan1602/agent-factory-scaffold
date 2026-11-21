from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from dashboard.charts import pass_chart, time_chart

router = APIRouter()

_MEASUREMENTS = Path(__file__).parent.parent.parent / "measurements" / "factory_performance.json"


@router.get("/api/metrics")
async def metrics() -> JSONResponse:
    if not _MEASUREMENTS.exists():
        return JSONResponse(content={"available": False,
                                     "message": "No measurement yet. Run agent-factory measure."})
    data = json.loads(_MEASUREMENTS.read_text())
    return JSONResponse(content={
        "available": True,
        **data,
        "charts": {
            "time_to_eval": time_chart(data["time_to_eval_minutes"]),
            "cases_passed": pass_chart(data["cases_passed"], data["cases_total"]),
        },
    })
