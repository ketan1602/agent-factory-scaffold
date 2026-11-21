"""Completion guard: a refund request that was neither refunded nor held for approval goes to a human."""
from __future__ import annotations

import re

REFUND_AMOUNT = re.compile(r"refund of (\d+(?:\.\d+)?)", re.IGNORECASE)
HELD = frozenset({"awaiting_approval", "rejected", "escalated"})


def refund_amount(utterance: str) -> float | None:
    match = REFUND_AMOUNT.search(utterance)
    return float(match.group(1)) if match else None


def apply_guard(utterance: str, outcome: dict) -> dict:
    amount = refund_amount(utterance)
    if amount is None or outcome["status"] in HELD or outcome["last_tool"] == "issue_refund":
        return outcome
    return {**outcome, "status": "escalated",
            "interventions": {**outcome["interventions"], "escalated_to_human": True},
            "guard": {"rule": "refund_intent_not_actioned", "amount": amount,
                      "last_tool": outcome["last_tool"], "original_status": outcome["status"]}}


async def guarded_run(case: dict, model_name: str | None = None) -> dict:
    from scenario.cases import run_harnessed

    outcome = await run_harnessed(case, model_name=model_name)
    return apply_guard(case["utterance"], outcome)


def monitor(rows: list[dict]) -> dict:
    """Over recorded runs: refund intents, guard escalations, and silent misses the guard should have caught."""
    intents = [r for r in rows if refund_amount(r["utterance"]) is not None]
    escalated = [r for r in intents if r["guard"]]
    silent = [r for r in intents if not r["guard"] and r["status"] not in HELD
              and r["last_tool"] != "issue_refund"]
    return {"runs": len(rows), "refund_intents": len(intents), "guard_escalations": len(escalated),
            "silent_misses": len(silent), "silent_miss_cases": [r["case"] for r in silent]}
