from __future__ import annotations

import json
from pathlib import Path

from cli.generator import AgentGenerator
from cli.manifest import load_manifest

ROOT = Path(__file__).parent.parent
REQUIRED = {"scenario/support.py", "scenario/llm.py", "scenario/cases.py", "scenario/config.py",
            "scenario/cases.json", "scripts/run_eval.py", "pyproject.toml", ".env.example",
            "README.md", ".gitignore"}


def test_dry_run_lists_files_and_writes_nothing(tmp_path: Path, manifest) -> None:
    result = AgentGenerator(output_dir=tmp_path).generate(manifest, dry_run=True)
    assert REQUIRED <= set(result.files_generated)
    assert list(tmp_path.iterdir()) == []


def test_generate_writes_every_listed_file(generated: Path, manifest) -> None:
    result = AgentGenerator(output_dir=generated.parent).generate(manifest)
    for rel in result.files_generated:
        assert (generated / rel).is_file()


def test_config_carries_the_manifest_grants_and_limits(generated: Path) -> None:
    config = (generated / "scenario" / "config.py").read_text()
    assert 'AGENT_ID = "ticket-triage"' in config
    assert 'ALLOWED_TOOLS = ("create_ticket", "add_note", )' in config
    assert "MAX_TOKENS = 5000" in config
    assert "MAX_COST_USD = 0.25" in config
    assert 'APPROVERS = {"supervisor-1"}' in config


def test_scenario_reads_identity_from_config(generated: Path) -> None:
    support = (generated / "scenario" / "support.py").read_text()
    assert "from scenario.config import" in support
    assert 'AGENT_ID = "support-agent"' not in support


def test_cases_come_from_the_manifest(generated: Path) -> None:
    cases = json.loads((generated / "scenario" / "cases.json").read_text())
    expected = json.loads((ROOT / "cases" / "ticket-triage.json").read_text())
    assert cases == expected


def test_each_committed_manifest_generates(tmp_path: Path) -> None:
    for path in sorted((ROOT / "manifests").glob("*.yaml")):
        manifest = load_manifest(path)
        AgentGenerator(output_dir=tmp_path).generate(manifest)
        assert (tmp_path / manifest.metadata.name / "scenario" / "config.py").is_file()


def test_env_example_lists_llm_variables(generated: Path) -> None:
    text = (generated / ".env.example").read_text()
    for key in ("LLM_API_KEY=", "LLM_BASE_URL=", "LLM_MODEL="):
        assert key in text
