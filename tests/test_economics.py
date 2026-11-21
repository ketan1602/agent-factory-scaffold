from __future__ import annotations

import pytest

from cli.economics import ASSUMPTIONS, cost_summary, load_assumptions

ENV = {"LLM_COST_PER_1K_TOKENS": "0.002", "HUMAN_APPROVAL_MINUTES": "10",
       "HUMAN_REVIEW_RATE_PER_HOUR": "60", "VIOLATION_REMEDIATION_COST_USD": "5"}


def test_missing_assumption_refuses_to_run() -> None:
    env = {k: v for k, v in ENV.items() if k != "HUMAN_REVIEW_RATE_PER_HOUR"}
    with pytest.raises(OSError, match="HUMAN_REVIEW_RATE_PER_HOUR must be set"):
        load_assumptions(env)


def test_blank_assumption_refuses_to_run() -> None:
    with pytest.raises(OSError):
        load_assumptions({**ENV, "LLM_COST_PER_1K_TOKENS": "  "})


def test_all_assumptions_are_named() -> None:
    assert set(ASSUMPTIONS) == set(ENV)


def test_cost_counts_tokens_reviews_and_remediation() -> None:
    rows = [
        {"tokens": 1000, "escalated": True, "violated": False, "passed": True},
        {"tokens": 1000, "escalated": False, "violated": True, "passed": False},
        {"tokens": 1000, "escalated": False, "violated": False, "passed": True},
    ]
    summary = cost_summary(rows, load_assumptions(ENV))
    assert summary["tokens"] == 3000
    assert summary["token_cost_usd"] == 0.006
    assert summary["review_cost_usd"] == 10.0          # one escalation: 10 min at 60 an hour
    assert summary["remediation_cost_usd"] == 5.0      # one violation
    assert summary["successful_outcomes"] == 2
    assert summary["cost_per_successful_outcome_usd"] == 7.503


def test_no_successes_means_no_cost_per_outcome() -> None:
    rows = [{"tokens": 10, "escalated": False, "violated": True, "passed": False}]
    assert cost_summary(rows, load_assumptions(ENV))["cost_per_successful_outcome_usd"] is None
