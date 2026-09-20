from __future__ import annotations

from pathlib import Path

import pytest

from cli.generator import AgentGenerator


@pytest.fixture
def generator(tmp_path: Path) -> AgentGenerator:
    return AgentGenerator(output_dir=tmp_path)


def test_dry_run_returns_file_list(generator: AgentGenerator) -> None:
    result = generator.generate("test-agent", "retail", dry_run=True)
    assert len(result.files_generated) == 8
    assert result.agent_name == "test-agent"
    assert result.domain == "retail"


def test_dry_run_writes_nothing(generator: AgentGenerator, tmp_path: Path) -> None:
    generator.generate("test-agent", "retail", dry_run=True)
    assert not (tmp_path / "test-agent").exists()


def test_generate_writes_files(generator: AgentGenerator, tmp_path: Path) -> None:
    generator.generate("my-agent", "finance", dry_run=False)
    agent_dir = tmp_path / "my-agent"
    assert (agent_dir / "agent" / "schemas.py").exists()
    assert (agent_dir / "agent" / "agent.py").exists()
    assert (agent_dir / "agent" / "nodes.py").exists()
    assert (agent_dir / "agent" / "prompts.py").exists()
    assert (agent_dir / "agent" / "__init__.py").exists()
    assert (agent_dir / "pyproject.toml").exists()
    assert (agent_dir / "config" / "harness.yaml").exists()
    assert (agent_dir / ".env.example").exists()


def test_unknown_domain_raises(generator: AgentGenerator) -> None:
    with pytest.raises(ValueError, match="Unknown domain"):
        generator.generate("x", "unknown-domain")


def test_available_domains_returns_four(generator: AgentGenerator) -> None:
    domains = generator.available_domains()
    assert sorted(domains) == ["finance", "healthcare", "hr", "retail"]


def test_context_class_name(generator: AgentGenerator, tmp_path: Path) -> None:
    generator.generate("pricing-monitor", "retail", dry_run=False)
    agent_py = tmp_path / "pricing-monitor" / "agent" / "agent.py"
    content = agent_py.read_text()
    assert "PricingMonitor" in content
