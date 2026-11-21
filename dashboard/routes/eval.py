from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

_ROOT = Path(__file__).parent.parent.parent
_REPORT = _ROOT / "measurements" / "release.json"


@router.get("/api/eval")
async def eval_results() -> JSONResponse:
    if not _REPORT.exists():
        return JSONResponse(content={"available": False,
                                     "message": "No release run yet. Run agent-factory release."})
    report = json.loads(_REPORT.read_text())
    agents = []
    for agent in report["agents"]:
        results_file = _ROOT / "generated_agents" / agent["agent"] / "measurements" / \
            "eval_results.json"
        rows = json.loads(results_file.read_text())["results"] if results_file.exists() else []
        agents.append({**agent, "results": rows})
    return JSONResponse(content={"available": True, "agents": agents})
