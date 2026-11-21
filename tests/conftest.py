from __future__ import annotations

from pathlib import Path

import pytest

from cli.generator import AgentGenerator
from cli.manifest import load_manifest

ROOT = Path(__file__).parent.parent


@pytest.fixture
def manifest():
    return load_manifest(ROOT / "manifests" / "ticket-triage.yaml")


@pytest.fixture
def generated(tmp_path: Path, manifest) -> Path:
    AgentGenerator(output_dir=tmp_path).generate(manifest)
    return tmp_path / manifest.metadata.name
