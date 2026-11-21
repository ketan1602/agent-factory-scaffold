from __future__ import annotations

import importlib.util
import json
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType

from cli.generator import TEMPLATES_DIR


def _guard_module() -> ModuleType:
    """The guard's monitor is the scenario's own code, loaded from the vendored template."""
    source = TEMPLATES_DIR / "spine" / "scenario" / "guard.py"
    spec = importlib.util.spec_from_file_location("spine_guard", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def online_report(generated_root: Path, report_path: Path) -> dict:
    """Monitor recorded runs of each generated agent: replayed eval runs, not live traffic."""
    monitor = _guard_module().monitor
    agents = {}
    for results in sorted(generated_root.glob("*/measurements/eval_results.json")):
        rows = json.loads(results.read_text())["results"]
        agents[results.parent.parent.name] = monitor(rows)
    silent = sum(a["silent_misses"] for a in agents.values())
    report = {
        "measured_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "source": "recorded eval runs (replayed traffic), not live production",
        "agents": agents,
        "summary": {"silent_misses": silent, "alert": silent > 0,
                    "guard_escalations": sum(a["guard_escalations"] for a in agents.values())},
    }
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report
