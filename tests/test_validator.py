from __future__ import annotations

from pathlib import Path

import pytest

from cli.validator import ComplianceValidator


@pytest.fixture
def validator() -> ComplianceValidator:
    return ComplianceValidator()


def test_valid_agent_passes_all_checks(
    validator: ComplianceValidator,
    pricing_monitor_path: Path,
) -> None:
    result = validator.validate(pricing_monitor_path)
    failed = [c for c in result.checks if not c.passed]
    assert not failed, f"Failed checks: {[c.name for c in failed]}"
    assert result.all_passed is True


def test_all_generated_agents_pass(
    validator: ComplianceValidator,
    generated_agents_dir: Path,
) -> None:
    agent_dirs = sorted(p for p in generated_agents_dir.iterdir() if p.is_dir())
    assert len(agent_dirs) == 8, f"Expected 8 agents, found {len(agent_dirs)}"
    for agent_dir in agent_dirs:
        result = validator.validate(agent_dir)
        failed = [c for c in result.checks if not c.passed]
        assert not failed, f"{agent_dir.name} failed: {[c.name for c in failed]}"


def test_missing_harness_import_fails(
    validator: ComplianceValidator,
    tmp_path: Path,
) -> None:
    agent_dir = tmp_path / "bad-agent"
    (agent_dir / "agent").mkdir(parents=True)
    (agent_dir / "agent" / "nodes.py").write_text("# no harness import\n")
    (agent_dir / "config").mkdir()
    (agent_dir / "config" / "harness.yaml").write_text("harness: {}")
    (agent_dir / ".env.example").write_text("AIREFINERY_API_KEY=\n")
    (agent_dir / "pyproject.toml").write_text(
        '[project]\nname="bad"\ndependencies=["agent-harness-core"]\n'
    )
    result = validator.validate(agent_dir)
    harness_check = next(c for c in result.checks if c.name == "Harness import")
    assert harness_check.passed is False


def test_pass_rate_pct_correct(validator: ComplianceValidator, tmp_path: Path) -> None:
    agent_dir = tmp_path / "partial-agent"
    (agent_dir / "agent").mkdir(parents=True)
    schemas = (
        "from pydantic import BaseModel\n"
        "class XInput(BaseModel): pass\n"
        "class XOutput(BaseModel): pass\n"
    )
    (agent_dir / "agent" / "schemas.py").write_text(schemas)
    nodes = "from harness_core import get_logger\nlogger = get_logger(__name__)\n"
    (agent_dir / "agent" / "nodes.py").write_text(nodes)
    agent_py = "from harness_core import AgentHarness\nharness = AgentHarness()\n"
    (agent_dir / "agent" / "agent.py").write_text(agent_py)
    (agent_dir / "config").mkdir()
    (agent_dir / "config" / "harness.yaml").write_text("harness: {}")
    (agent_dir / ".env.example").write_text("AIREFINERY_API_KEY=\n")
    (agent_dir / "pyproject.toml").write_text(
        '[project]\nname="x"\ndependencies=["agent-harness-core"]\n'
    )
    result = validator.validate(agent_dir)
    assert result.pass_rate_pct == pytest.approx(100.0)


def test_empty_directory_fails_all(validator: ComplianceValidator, tmp_path: Path) -> None:
    result = validator.validate(tmp_path)
    assert result.all_passed is False
    assert result.pass_rate_pct == pytest.approx(0.0)
    assert len(result.checks) == 8
