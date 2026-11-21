#!/usr/bin/env python3
"""Run every support case through the harness with the live model and record the results.

Needs LLM_API_KEY, LLM_BASE_URL and LLM_MODEL (see .env.example).
Writes measurements/eval_results.json.
"""
from __future__ import annotations

import asyncio
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scenario.cases import load_cases  # noqa: E402
from scenario.guard import guarded_run  # noqa: E402
from scenario.llm import config_error, model_id  # noqa: E402

OUT = ROOT / "measurements" / "eval_results.json"


async def evaluate() -> list[dict]:
    results = []
    for case in load_cases():
        started = time.perf_counter()
        outcome = await guarded_run(case)
        decision = outcome["decision"] or {}
        results.append({
            "case": case["id"],
            "category": case["category"],
            "passed": outcome["verdict"]["passed"],
            "violated": outcome["violated"],
            "escalated": outcome["interventions"]["escalated_to_human"]
            or outcome["status"] == "awaiting_approval" or outcome["human"] is not None,
            "utterance": case["utterance"],
            "last_tool": outcome["last_tool"],
            "guard": outcome.get("guard"),
            "status": outcome["status"],
            "reason": outcome["reason"],
            "tool": decision.get("tool"),
            "tokens": decision.get("tokens", 0),
            "model_seconds": round(outcome["model_seconds"], 3),
            "seconds": round(time.perf_counter() - started, 3),
        })
    return results


def main() -> int:
    load_dotenv()
    if error := config_error():
        print(error, file=sys.stderr)
        return 1
    results = asyncio.run(evaluate())
    passed = sum(r["passed"] for r in results)
    report = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "model": model_id(),
        "cases_total": len(results),
        "cases_passed": passed,
        "results": results,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(f"{passed}/{len(results)} cases passed; wrote {OUT.relative_to(ROOT)}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    import truststore

    truststore.inject_into_ssl()
    sys.exit(main())
