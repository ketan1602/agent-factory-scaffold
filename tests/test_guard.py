from __future__ import annotations

import importlib.util
from pathlib import Path

from cli.generator import TEMPLATES_DIR

_SPEC = importlib.util.spec_from_file_location("spine_guard",
                                               TEMPLATES_DIR / "spine" / "scenario" / "guard.py")
guard = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(guard)

REFUND = "Customer requests a refund of 180 for order O-34."


def _outcome(status: str, last_tool: str | None) -> dict:
    return {"status": status, "last_tool": last_tool,
            "interventions": {"escalated_to_human": False}}


def test_parses_refund_amounts() -> None:
    assert guard.refund_amount(REFUND) == 180.0
    assert guard.refund_amount("Order O-1 not delivered") is None
    assert guard.refund_amount("Customer requests a refund of 99.50") == 99.5


def test_completed_without_refund_is_escalated() -> None:
    out = guard.apply_guard(REFUND, _outcome("completed", "add_note"))
    assert out["status"] == "escalated"
    assert out["interventions"]["escalated_to_human"] is True
    assert out["guard"] == {"rule": "refund_intent_not_actioned", "amount": 180.0,
                            "last_tool": "add_note", "original_status": "completed"}


def test_blocked_refund_attempt_is_escalated() -> None:
    assert guard.apply_guard(REFUND, _outcome("blocked", None))["status"] == "escalated"


def test_completed_refund_passes_through() -> None:
    out = _outcome("completed", "issue_refund")
    assert guard.apply_guard(REFUND, out) is out


def test_refund_held_for_approval_passes_through() -> None:
    for status in ("awaiting_approval", "rejected"):
        out = _outcome(status, None)
        assert guard.apply_guard(REFUND, out) is out


def test_non_refund_requests_pass_through() -> None:
    out = _outcome("completed", "add_note")
    assert guard.apply_guard("Order O-1 not delivered", out) is out


def test_monitor_counts_silent_misses_only() -> None:
    rows = [
        {"case": "a", "utterance": REFUND, "status": "escalated", "last_tool": "add_note",
         "guard": {"rule": "x"}},
        {"case": "b", "utterance": REFUND, "status": "completed", "last_tool": "issue_refund",
         "guard": None},
        {"case": "c", "utterance": REFUND, "status": "completed", "last_tool": "add_note",
         "guard": None},
        {"case": "d", "utterance": "Order O-1", "status": "completed", "last_tool": "add_note",
         "guard": None},
    ]
    report = guard.monitor(rows)
    assert report == {"runs": 4, "refund_intents": 3, "guard_escalations": 1,
                      "silent_misses": 1, "silent_miss_cases": ["c"]}


def test_scenario_guard_is_vendored_identically() -> None:
    assert Path(_SPEC.origin).read_text().startswith('"""Completion guard')
