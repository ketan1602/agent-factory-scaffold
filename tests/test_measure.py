from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from cli import measure as measure_module


def _fake_eval(passed: int, total: int = 16):
    def run(args, cwd, capture_output, text, check):  # noqa: ARG001 - mirrors subprocess.run
        results = [{"case": f"c{i}", "category": "x", "passed": i < passed, "status": "completed",
                    "reason": None, "tool": "create_ticket", "tokens": 10,
                    "model_seconds": 0.5, "seconds": 0.6} for i in range(total)]
        out = Path(cwd) / "measurements"
        out.mkdir(exist_ok=True)
        (out / "eval_results.json").write_text(json.dumps({
            "model": "test-model", "cases_total": total, "cases_passed": passed,
            "results": results}))
        return subprocess.CompletedProcess(args, 0 if passed == total else 1, "", "")
    return run


def test_measure_records_a_passing_eval(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(measure_module.subprocess, "run", _fake_eval(16))
    report = measure_module.measure("support-east", tmp_path / "gen", tmp_path / "m.json")
    assert report["first_passing_eval"] is True
    assert report["cases_passed"] == 16 and report["cases_total"] == 16
    assert report["total_tokens"] == 160
    assert report["model"] == "test-model"
    assert json.loads((tmp_path / "m.json").read_text())["time_to_eval_minutes"] >= 0


def test_measure_records_a_failing_eval_honestly(tmp_path: Path,
                                                 monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(measure_module.subprocess, "run", _fake_eval(14))
    report = measure_module.measure("support-east", tmp_path / "gen", tmp_path / "m.json")
    assert report["first_passing_eval"] is False
    assert report["cases_passed"] == 14


def test_measure_fails_when_eval_writes_nothing(tmp_path: Path,
                                               monkeypatch: pytest.MonkeyPatch) -> None:
    def no_output(args, cwd, capture_output, text, check):  # noqa: ARG001
        return subprocess.CompletedProcess(args, 1, "", "ModuleNotFoundError: harness_core")
    monkeypatch.setattr(measure_module.subprocess, "run", no_output)
    with pytest.raises(RuntimeError, match="wrote no results"):
        measure_module.measure("support-east", tmp_path / "gen", tmp_path / "m.json")
