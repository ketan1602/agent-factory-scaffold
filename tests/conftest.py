from __future__ import annotations

from pathlib import Path

import pytest

from cli.generator import AgentGenerator


@pytest.fixture
def generated(tmp_path: Path) -> Path:
    AgentGenerator(output_dir=tmp_path).generate("support-east")
    return tmp_path / "support-east"
