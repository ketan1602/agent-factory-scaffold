from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from cli.manifest import load_manifest, load_manifests

ROOT = Path(__file__).parent.parent
VALID = yaml.safe_load((ROOT / "manifests" / "ticket-triage.yaml").read_text())


def _write(tmp_path: Path, mutate) -> Path:
    data = yaml.safe_load(yaml.safe_dump(VALID))
    mutate(data)
    path = tmp_path / "m.yaml"
    path.write_text(yaml.safe_dump(data))
    return path


def test_all_committed_manifests_load() -> None:
    names = {m.metadata.name for m in load_manifests(ROOT / "manifests")}
    assert names == {"ticket-triage", "refund-desk", "case-notes", "support-agent"}


def test_unknown_tool_is_rejected(tmp_path: Path) -> None:
    path = _write(tmp_path, lambda d: d["spec"]["tools"].update(allow=["wire_money"]))
    with pytest.raises(ValueError, match="unknown tools"):
        load_manifest(path)


def test_bad_agent_name_is_rejected(tmp_path: Path) -> None:
    path = _write(tmp_path, lambda d: d["metadata"].update(name="Bad Name"))
    with pytest.raises(ValidationError):
        load_manifest(path)


def test_pass_rate_out_of_range_is_rejected(tmp_path: Path) -> None:
    path = _write(tmp_path, lambda d: d["spec"]["evaluation"].update(minimumPassRate=1.5))
    with pytest.raises(ValidationError):
        load_manifest(path)


def test_empty_tool_grant_is_rejected(tmp_path: Path) -> None:
    path = _write(tmp_path, lambda d: d["spec"]["tools"].update(allow=[]))
    with pytest.raises(ValidationError):
        load_manifest(path)
