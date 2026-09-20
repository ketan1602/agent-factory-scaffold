from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


@dataclass
class GeneratorResult:
    agent_name: str
    domain: str
    files_generated: list[str]
    duration_seconds: float
    output_path: str


class AgentGenerator:
    def __init__(
        self,
        templates_dir: Path | None = None,
        output_dir: Path | None = None,
    ) -> None:
        self._templates_dir = templates_dir or TEMPLATES_DIR
        self._output_dir = output_dir or Path("generated_agents")
        self._env = Environment(
            loader=FileSystemLoader(str(self._templates_dir / "base")),
            autoescape=select_autoescape(disabled_extensions=("j2",)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(self, agent_name: str, domain: str, dry_run: bool = False) -> GeneratorResult:
        """Render templates to output_dir / agent_name. dry_run skips disk writes."""
        start = time.monotonic()
        domain_config = self._load_domain_config(domain)
        context = self._build_context(agent_name, domain, domain_config)
        file_map = self._file_map(agent_name)
        generated: list[str] = []

        for template_name, rel_path in file_map.items():
            content = self._render(template_name, context)
            if not dry_run:
                target = self._output_dir / agent_name / rel_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
            generated.append(rel_path)

        return GeneratorResult(
            agent_name=agent_name,
            domain=domain,
            files_generated=generated,
            duration_seconds=time.monotonic() - start,
            output_path=str(self._output_dir / agent_name),
        )

    def available_domains(self) -> list[str]:
        domains_dir = self._templates_dir / "domains"
        return sorted(p.name for p in domains_dir.iterdir() if p.is_dir())

    def _load_domain_config(self, domain: str) -> dict:
        config_path = self._templates_dir / "domains" / domain / "config.yaml"
        if not config_path.exists():
            raise ValueError(
                f"Unknown domain: {domain!r}. Run list-templates to see available."
            )
        return yaml.safe_load(config_path.read_text())

    def _build_context(self, agent_name: str, domain: str, cfg: dict) -> dict:
        cls = "".join(w.capitalize() for w in agent_name.replace("-", "_").split("_"))
        return {
            "agent_name": agent_name,
            "agent_class_name": cls,
            "domain": domain,
            "domain_description": cfg.get("description", ""),
            "domain_instructions": cfg.get("instructions", ""),
            "default_model": cfg.get("default_model", "claude-sonnet-4-6"),
        }

    @staticmethod
    def _file_map(agent_name: str) -> dict[str, str]:  # noqa: ARG004
        return {
            "schemas.py.j2": "agent/schemas.py",
            "agent.py.j2": "agent/agent.py",
            "nodes.py.j2": "agent/nodes.py",
            "prompts.py.j2": "agent/prompts.py",
            "init.py.j2": "agent/__init__.py",
            "pyproject.toml.j2": "pyproject.toml",
            "harness.yaml.j2": "config/harness.yaml",
            "env_example.j2": ".env.example",
        }

    def _render(self, template_name: str, context: dict) -> str:
        return self._env.get_template(template_name).render(**context)
