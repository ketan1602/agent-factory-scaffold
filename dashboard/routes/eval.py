from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

_RESULTS = (Path(__file__).parent.parent.parent / "generated_agents" / "support-agent"
            / "measurements" / "eval_results.json")


@router.get("/api/eval")
async def eval_results() -> JSONResponse:
    if not _RESULTS.exists():
        return JSONResponse(content={"available": False,
                                     "message": "No eval run yet. Run scripts/run_eval.py."})
    return JSONResponse(content={"available": True, **json.loads(_RESULTS.read_text())})
