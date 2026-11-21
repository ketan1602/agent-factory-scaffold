from __future__ import annotations

import json
from pathlib import Path

from cli.online import online_report

REFUND = "Customer requests a refund of 180 for order O-34."


def _write_run(root: Path, agent: str, rows: list[dict]) -> None:
    target = root / agent / "measurements"
    target.mkdir(parents=True)
    (target / "eval_results.json").write_text(json.dumps({"results": rows}))


def test_clean_runs_raise_no_alert(tmp_path: Path) -> None:
    _write_run(tmp_path, "refund-desk", [
        {"case": "r1", "utterance": REFUND, "status": "escalated", "last_tool": "add_note",
         "guard": {"rule": "refund_intent_not_actioned"}},
    ])
    report = online_report(tmp_path, tmp_path / "online.json")
    assert report["summary"] == {"silent_misses": 0, "alert": False, "guard_escalations": 1}


def test_silent_miss_raises_alert(tmp_path: Path) -> None:
    _write_run(tmp_path, "refund-desk", [
        {"case": "r2", "utterance": REFUND, "status": "completed", "last_tool": "add_note",
         "guard": None},
    ])
    report = online_report(tmp_path, tmp_path / "online.json")
    assert report["summary"]["alert"] is True
    assert report["agents"]["refund-desk"]["silent_miss_cases"] == ["r2"]
    assert json.loads((tmp_path / "online.json").read_text())["summary"]["silent_misses"] == 1
