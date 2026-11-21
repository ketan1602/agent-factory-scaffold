from __future__ import annotations

from pathlib import Path

import pytest

from cli.generator import AgentGenerator

REQUIRED = {"scenario/support.py", "scenario/llm.py", "scenario/cases.py", "scenario/cases.json",
            "scripts/run_eval.py", "pyproject.toml", ".env.example", "README.md", ".gitignore"}


def test_dry_run_lists_files_and_writes_nothing(tmp_path: Path) -> None:
    result = AgentGenerator(output_dir=tmp_path).generate("support-east", dry_run=True)
    assert REQUIRED <= set(result.files_generated)
    assert list(tmp_path.iterdir()) == []


def test_generate_writes_every_listed_file(tmp_path: Path) -> None:
    result = AgentGenerator(output_dir=tmp_path).generate("support-east")
    for rel in result.files_generated:
        assert (tmp_path / "support-east" / rel).is_file()


def test_agent_id_is_stamped_into_scenario(generated: Path) -> None:
    support = (generated / "scenario" / "support.py").read_text()
    assert 'AGENT_ID = "support-east"' in support
    assert 'AGENT_ID = "support-agent"' not in support


def test_env_example_lists_llm_variables(generated: Path) -> None:
    text = (generated / ".env.example").read_text()
    for key in ("LLM_API_KEY=", "LLM_BASE_URL=", "LLM_MODEL="):
        assert key in text


def test_pyproject_names_the_agent(generated: Path) -> None:
    assert 'name = "support-east"' in (generated / "pyproject.toml").read_text()


@pytest.mark.parametrize("bad", ["Support_East", "1agent", "a", "has space", "../escape"])
def test_rejects_invalid_names(tmp_path: Path, bad: str) -> None:
    with pytest.raises(ValueError, match="Invalid agent name"):
        AgentGenerator(output_dir=tmp_path).generate(bad, dry_run=True)
