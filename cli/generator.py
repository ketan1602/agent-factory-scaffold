from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from cli.manifest import Manifest

ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = ROOT / "templates"
CASES_DIR = ROOT / "cases"
RENDERED = {
    "pyproject.toml.j2": "pyproject.toml",
    "env_example.j2": ".env.example",
    "README.md.j2": "README.md",
    "config.py.j2": "scenario/config.py",
}


@dataclass
class GeneratorResult:
    agent_name: str
    files_generated: list[str]
    duration_seconds: float
    output_path: str


class AgentGenerator:
    def __init__(self, templates_dir: Path | None = None, output_dir: Path | None = None,
                 cases_dir: Path | None = None) -> None:
        self._templates_dir = templates_dir or TEMPLATES_DIR
        self._output_dir = output_dir or Path("generated_agents")
        self._cases_dir = cases_dir or CASES_DIR
        self._env = Environment(
            loader=FileSystemLoader(str(self._templates_dir / "base")),
            autoescape=select_autoescape(enabled_extensions=("html",)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(self, manifest: Manifest, dry_run: bool = False) -> GeneratorResult:
        """Stamp the agent described by a manifest. dry_run returns the file list only."""
        start = time.monotonic()
        name = manifest.metadata.name
        files = {**self._spine_files(), **self._cases_file(manifest),
                 **self._rendered_files(manifest)}
        if not dry_run:
            for rel, content in files.items():
                target = self._output_dir / name / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
        return GeneratorResult(
            agent_name=name,
            files_generated=sorted(files),
            duration_seconds=time.monotonic() - start,
            output_path=str(self._output_dir / name),
        )

    def _spine_files(self) -> dict[str, str]:
        spine = self._templates_dir / "spine"
        return {src.relative_to(spine).as_posix(): src.read_text()
                for src in sorted(p for p in spine.rglob("*") if p.is_file())}

    def _cases_file(self, manifest: Manifest) -> dict[str, str]:
        text = (self._cases_dir / manifest.spec.evaluation.cases).read_text()
        if not isinstance(json.loads(text), list):
            raise ValueError(f"{manifest.spec.evaluation.cases} must hold a JSON list of cases")
        return {"scenario/cases.json": text}

    def _rendered_files(self, manifest: Manifest) -> dict[str, str]:
        context = _context(manifest)
        return {rel: self._env.get_template(tpl).render(**context)
                for tpl, rel in RENDERED.items()}


def _context(manifest: Manifest) -> dict:
    spec = manifest.spec
    approvers = ", ".join(f'"{a}"' for a in spec.approval.approvers)
    return {
        "name": manifest.metadata.name,
        "owner": manifest.metadata.owner,
        "version": manifest.metadata.version,
        "scope": spec.scope,
        "runtime": spec.runtime,
        "tools": spec.tools.allow,
        "max_tokens": spec.budget.maxTokens,
        "max_cost_usd": float(spec.budget.maxCostUsd),
        "refund_limit": float(spec.approval.refundAboveAmount),
        "approvers": "{" + approvers + "}",
    }
