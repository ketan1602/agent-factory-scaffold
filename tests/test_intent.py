from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from cli.generator import AgentGenerator


def _note(project: Path, utterance: str) -> str:
    code = f"from scenario.intent import intent_note; print(intent_note({utterance!r}), end='')"
    result = subprocess.run([sys.executable, "-c", code],  # noqa: S603 - fixed argv, test only
                            cwd=project, capture_output=True, text=True, check=True)
    return result.stdout


def test_refund_above_limit_tells_model_to_call_refund(tmp_path: Path) -> None:
    from cli.manifest import load_manifest
    project = tmp_path / "refund-desk"
    AgentGenerator(output_dir=tmp_path).generate(load_manifest(
        Path(__file__).parent.parent / "manifests" / "refund-desk.yaml"))
    note = _note(project, "Customer requests a refund of 180 for order O-34.")
    assert "above the refund limit of 100" in note and "Call issue_refund" in note


def test_agent_without_refund_grant_is_told_not_to_refund(generated: Path) -> None:
    note = _note(generated, "Customer requests a refund of 180 for order O-34.")
    assert "no refund tool" in note


def test_non_refund_request_has_no_note(generated: Path) -> None:
    assert _note(generated, "Order O-21 has not been delivered.") == ""
