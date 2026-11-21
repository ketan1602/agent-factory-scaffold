from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from cli.generator import AgentGenerator
from cli.validator import ComplianceValidator


def measure(agent_name: str, output_root: Path, report_path: Path) -> dict:
    """Generate the agent, run its live eval, and record what actually happened."""
    started = time.monotonic()
    AgentGenerator(output_dir=output_root).generate(agent_name)
    generated = time.monotonic()
    project = output_root / agent_name
    proc = subprocess.run([sys.executable, "scripts/run_eval.py"], cwd=project,
                          capture_output=True, text=True, check=False)
    finished = time.monotonic()
    results_file = project / "measurements" / "eval_results.json"
    if not results_file.exists():
        raise RuntimeError(f"eval wrote no results (exit {proc.returncode}): {proc.stderr[-400:]}")
    evaluated = json.loads(results_file.read_text())
    checks = ComplianceValidator().validate(project)
    rows = evaluated["results"]
    report = {
        "agent": agent_name,
        "model": evaluated["model"],
        "measured_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "generate_seconds": round(generated - started, 3),
        "eval_seconds": round(finished - generated, 3),
        "time_to_eval_minutes": round((finished - started) / 60, 2),
        "cases_total": evaluated["cases_total"],
        "cases_passed": evaluated["cases_passed"],
        "first_passing_eval": evaluated["cases_passed"] == evaluated["cases_total"],
        "total_tokens": sum(r["tokens"] for r in rows),
        "model_seconds": round(sum(r["model_seconds"] for r in rows), 3),
        "compliance_checks_passed": sum(c.passed for c in checks.checks),
        "compliance_checks_total": len(checks.checks),
        "compliance_pct": round(checks.pass_rate_pct, 1),
    }
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report
