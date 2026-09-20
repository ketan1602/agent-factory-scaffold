from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from cli.generator import AgentGenerator
from cli.validator import ComplianceValidator

router = APIRouter()

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_PROXY_AGENT = _PROJECT_ROOT / "generated_agents" / "pricing-monitor"


class GenerateRequest(BaseModel):
    name: str
    domain: str


def _build_file_tree(files: list[str]) -> dict:
    tree: dict = {}
    for f in files:
        parts = f.split("/")
        node = tree
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = None
    return tree


@router.post("/api/generate")
async def generate_agent(req: GenerateRequest) -> JSONResponse:
    gen = AgentGenerator()
    try:
        result = gen.generate(req.name, req.domain, dry_run=True)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    validator = ComplianceValidator()
    if _PROXY_AGENT.exists():
        validation = validator.validate(_PROXY_AGENT)
        compliance = [
            {"name": c.name, "passed": c.passed, "message": c.message}
            for c in validation.checks
        ]
    else:
        compliance = [
            {"name": f"Check {i}", "passed": False, "message": "Proxy agent not found"}
            for i in range(1, 9)
        ]

    return JSONResponse(
        content={
            "files": result.files_generated,
            "duration_seconds": round(result.duration_seconds, 4),
            "file_tree": _build_file_tree(result.files_generated),
            "compliance": compliance,
        }
    )
