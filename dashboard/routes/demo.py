from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from cli.generator import AgentGenerator
from cli.validator import ComplianceValidator

router = APIRouter()

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_REFERENCE_AGENT = _PROJECT_ROOT / "generated_agents" / "support-agent"


class GenerateRequest(BaseModel):
    name: str


def _build_file_tree(files: list[str]) -> dict:
    tree: dict = {}
    for f in files:
        parts = f.split("/")
        node = tree
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = None
    return tree


def _compliance() -> list[dict]:
    if not _REFERENCE_AGENT.exists():
        return [{"name": "Reference agent", "passed": False,
                 "message": "generated_agents/support-agent not found"}]
    validation = ComplianceValidator().validate(_REFERENCE_AGENT)
    return [{"name": c.name, "passed": c.passed, "message": c.message} for c in validation.checks]


@router.post("/api/generate")
async def generate_agent(req: GenerateRequest) -> JSONResponse:
    try:
        result = AgentGenerator().generate(req.name, dry_run=True)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"detail": str(exc)})
    return JSONResponse(content={
        "files": result.files_generated,
        "duration_seconds": round(result.duration_seconds, 4),
        "file_tree": _build_file_tree(result.files_generated),
        "compliance_source": "generated_agents/support-agent",
        "compliance": _compliance(),
    })
