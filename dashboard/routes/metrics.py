from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from dashboard.charts import decisions_chart, time_comparison_chart

router = APIRouter()

_MEASUREMENTS = Path(__file__).parent.parent.parent / "measurements" / "factory_performance.json"


@router.get("/api/metrics")
async def metrics() -> JSONResponse:
    data = json.loads(_MEASUREMENTS.read_text())
    return JSONResponse(
        content={
            **data,
            "charts": {
                "time_comparison": time_comparison_chart(),
                "decisions": decisions_chart(),
            },
        }
    )
