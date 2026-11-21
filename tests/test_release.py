from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from cli import release as release_module
from cli.manifest import load_manifest

ROOT = Path(__file__).parent.parent
ENV = {"LLM_COST_PER_1K_TOKENS": "0.002", "HUMAN_APPROVAL_MINUTES": "10",
       "HUMAN_REVIEW_RATE_PER_HOUR": "60", "VIOLATION_REMEDIATION_COST_USD": "5"}


def _fake_eval(passed_by_agent: dict[str, int]):
    def run(args, cwd, env, capture_output, text, check):  # noqa: ARG001 - mirrors subprocess.run
        agent = Path(cwd).name
        total = 4
        passed = passed_by_agent[agent]
        rows = [{"case": f"c{i}", "category": "x", "passed": i < passed, "violated": False,
                 "escalated": False, "status": "completed", "reason": None, "tool": "add_note",
                 "tokens": 100, "model_seconds": 0.1, "seconds": 0.2} for i in range(total)]
        out = Path(cwd) / "measurements"
        out.mkdir(exist_ok=True)
        (out / "eval_results.json").write_text(json.dumps(
            {"model": "test-model", "cases_total": total, "cases_passed": passed, "results": rows}))
        return subprocess.CompletedProcess(args, 0, "", "")
    return run


def _manifests(*names: str):
    return [load_manifest(ROOT / "manifests" / f"{n}.yaml") for n in names]


def test_release_applies_each_gate_and_summarises(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(release_module.subprocess, "run",
                        _fake_eval({"ticket-triage": 4, "refund-desk": 3}))
    report = release_module.release(_manifests("ticket-triage", "refund-desk"), tmp_path / "g",
                                    tmp_path / "r.json", ENV)
    by_name = {a["agent"]: a for a in report["agents"]}
    assert not by_name["ticket-triage"]["gate"]["blocked"]
    assert by_name["refund-desk"]["gate"]["blocked"]
    assert report["summary"]["agents_blocked"] == ["refund-desk"]
    assert report["summary"]["cases_passed"] == 7
    assert json.loads((tmp_path / "r.json").read_text())["model"] == "test-model"


def test_missing_assumption_stops_before_any_live_call(tmp_path: Path, monkeypatch) -> None:
    def must_not_run(*args, **kwargs):
        raise AssertionError("eval started without cost assumptions")
    monkeypatch.setattr(release_module.subprocess, "run", must_not_run)
    with pytest.raises(OSError, match="must be set"):
        release_module.release(_manifests("ticket-triage"), tmp_path / "g", tmp_path / "r.json", {})


def test_eval_that_writes_nothing_is_an_error(tmp_path: Path, monkeypatch) -> None:
    def no_output(args, cwd, env, capture_output, text, check):  # noqa: ARG001
        return subprocess.CompletedProcess(args, 1, "", "ModuleNotFoundError: harness_core")
    monkeypatch.setattr(release_module.subprocess, "run", no_output)
    with pytest.raises(RuntimeError, match="ticket-triage: eval wrote no results"):
        release_module.release(_manifests("ticket-triage"), tmp_path / "g", tmp_path / "r.json",
                               ENV)
