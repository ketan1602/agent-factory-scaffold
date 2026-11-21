from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from cli.generator import AgentGenerator
from cli.manifest import load_manifest
from cli.validator import ComplianceValidator

router = APIRouter()

_ROOT = Path(__file__).parent.parent.parent
_GENERATED = _ROOT / "generated_agents"
_NAME = re.compile(r"^[a-z][a-z0-9-]{1,62}$")


class PreviewRequest(BaseModel):
    manifest: str


def _build_file_tree(files: list[str]) -> dict:
    tree: dict = {}
    for f in files:
        parts = f.split("/")
        node = tree
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = None
    return tree


def _compliance(name: str) -> list[dict]:
    project = _GENERATED / name
    if not project.exists():
        return [{"name": "Generated project", "passed": False,
                 "message": f"generated_agents/{name} not found; run agent-factory release"}]
    return [{"name": c.name, "passed": c.passed, "message": c.message}
            for c in ComplianceValidator().validate(project).checks]


@router.post("/api/generate")
async def preview_agent(req: PreviewRequest) -> JSONResponse:
    if not _NAME.match(req.manifest):
        return JSONResponse(status_code=400, content={"detail": "invalid manifest name"})
    path = _ROOT / "manifests" / f"{req.manifest}.yaml"
    if not path.exists():
        return JSONResponse(status_code=404, content={"detail": f"no manifest {req.manifest}"})
    result = AgentGenerator().generate(load_manifest(path), dry_run=True)
    return JSONResponse(content={
        "files": result.files_generated,
        "duration_seconds": round(result.duration_seconds, 4),
        "file_tree": _build_file_tree(result.files_generated),
        "compliance_source": f"generated_agents/{req.manifest}",
        "compliance": _compliance(req.manifest),
    })
