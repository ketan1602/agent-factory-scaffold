from __future__ import annotations

import json
import subprocess
import sys
import time
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

from cli.economics import cost_summary, load_assumptions
from cli.gate import evaluate_gate
from cli.generator import AgentGenerator
from cli.manifest import Manifest
from cli.validator import ComplianceValidator


def release_agent(manifest: Manifest, output_root: Path, assumptions: Mapping[str, float],
                  env: Mapping[str, str]) -> dict:
    name = manifest.metadata.name
    started = time.monotonic()
    AgentGenerator(output_dir=output_root).generate(manifest)
    generated = time.monotonic()
    project = output_root / name
    proc = subprocess.run([sys.executable, "scripts/run_eval.py"], cwd=project, env=dict(env),
                          capture_output=True, text=True, check=False)
    finished = time.monotonic()
    results_file = project / "measurements" / "eval_results.json"
    if not results_file.exists():
        raise RuntimeError(f"{name}: eval wrote no results (exit {proc.returncode}): "
                           f"{proc.stderr[-400:]}")
    evaluated = json.loads(results_file.read_text())
    rows = evaluated["results"]
    checks = ComplianceValidator().validate(project)
    return {
        "agent": name,
        "version": manifest.metadata.version,
        "owner": manifest.metadata.owner,
        "model": evaluated["model"],
        "generate_seconds": round(generated - started, 3),
        "eval_seconds": round(finished - generated, 3),
        "cases_total": len(rows),
        "cases_passed": sum(r["passed"] for r in rows),
        "gate": evaluate_gate(manifest, rows).as_dict(),
        "economics": cost_summary(rows, assumptions),
        "compliance_checks_passed": sum(c.passed for c in checks.checks),
        "compliance_checks_total": len(checks.checks),
    }


def release(manifests: list[Manifest], output_root: Path, report_path: Path,
            env: Mapping[str, str]) -> dict:
    """Release every manifest. Cost assumptions are checked before any live call is made."""
    assumptions = load_assumptions(env)
    agents = [release_agent(m, output_root, assumptions, env) for m in manifests]
    blocked = [a["agent"] for a in agents if a["gate"]["blocked"]]
    total_cost = round(sum(a["economics"]["total_cost_usd"] for a in agents), 6)
    successes = sum(a["economics"]["successful_outcomes"] for a in agents)
    report = {
        "measured_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "model": agents[0]["model"] if agents else None,
        "agents": agents,
        "summary": {
            "agents_total": len(agents),
            "agents_released": len(agents) - len(blocked),
            "agents_blocked": blocked,
            "cases_total": sum(a["cases_total"] for a in agents),
            "cases_passed": sum(a["cases_passed"] for a in agents),
            "total_cost_usd": total_cost,
            "cost_per_successful_outcome_usd": (round(total_cost / successes, 6)
                                                if successes else None),
        },
    }
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report
