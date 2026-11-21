from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
SPINE_AGENT_LINE = 'AGENT_ID = "support-agent"'
RENDERED = {
    "pyproject.toml.j2": "pyproject.toml",
    "env_example.j2": ".env.example",
    "README.md.j2": "README.md",
}
_NAME = re.compile(r"^[a-z][a-z0-9-]{1,62}$")


@dataclass
class GeneratorResult:
    agent_name: str
    files_generated: list[str]
    duration_seconds: float
    output_path: str


class AgentGenerator:
    def __init__(self, templates_dir: Path | None = None, output_dir: Path | None = None) -> None:
        self._templates_dir = templates_dir or TEMPLATES_DIR
        self._output_dir = output_dir or Path("generated_agents")
        self._env = Environment(
            loader=FileSystemLoader(str(self._templates_dir / "base")),
            autoescape=select_autoescape(enabled_extensions=("html",)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(self, agent_name: str, dry_run: bool = False) -> GeneratorResult:
        """Stamp the support agent under output_dir/agent_name. dry_run lists files only."""
        if not _NAME.match(agent_name):
            raise ValueError(
                f"Invalid agent name {agent_name!r}: use lowercase letters, digits, hyphens.")
        start = time.monotonic()
        files = {**self._spine_files(agent_name), **self._rendered_files(agent_name)}
        if not dry_run:
            for rel, content in files.items():
                target = self._output_dir / agent_name / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
        return GeneratorResult(
            agent_name=agent_name,
            files_generated=sorted(files),
            duration_seconds=time.monotonic() - start,
            output_path=str(self._output_dir / agent_name),
        )

    def _spine_files(self, agent_name: str) -> dict[str, str]:
        spine = self._templates_dir / "spine"
        files: dict[str, str] = {}
        for src in sorted(p for p in spine.rglob("*") if p.is_file()):
            rel = src.relative_to(spine).as_posix()
            text = src.read_text()
            if rel == "scenario/support.py":
                text = text.replace(SPINE_AGENT_LINE, f'AGENT_ID = "{agent_name}"')
            files[rel] = text
        return files

    def _rendered_files(self, agent_name: str) -> dict[str, str]:
        return {rel: self._env.get_template(tpl).render(agent_name=agent_name)
                for tpl, rel in RENDERED.items()}
