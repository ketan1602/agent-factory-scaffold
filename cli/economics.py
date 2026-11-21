from __future__ import annotations

from collections.abc import Mapping

ASSUMPTIONS = (
    "LLM_COST_PER_1K_TOKENS",
    "HUMAN_APPROVAL_MINUTES",
    "HUMAN_REVIEW_RATE_PER_HOUR",
    "VIOLATION_REMEDIATION_COST_USD",
)


def load_assumptions(env: Mapping[str, str]) -> dict[str, float]:
    """Cost assumptions are labelled inputs. None has a default; a missing one stops the release."""
    missing = [k for k in ASSUMPTIONS if not env.get(k, "").strip()]
    if missing:
        raise OSError(
            f"{', '.join(missing)} must be set (see .env.example); no default is assumed")
    return {k: float(env[k]) for k in ASSUMPTIONS}


def cost_summary(results: list[dict], assumptions: Mapping[str, float]) -> dict:
    """Token cost is measured. Review and remediation are assumptions applied to counted events."""
    tokens = sum(r["tokens"] for r in results)
    escalations = sum(1 for r in results if r["escalated"])
    violations = sum(1 for r in results if r["violated"])
    successes = sum(1 for r in results if r["passed"] and not r["violated"])
    token_cost = tokens / 1000 * assumptions["LLM_COST_PER_1K_TOKENS"]
    review_cost = (escalations * assumptions["HUMAN_APPROVAL_MINUTES"] / 60
                   * assumptions["HUMAN_REVIEW_RATE_PER_HOUR"])
    remediation_cost = violations * assumptions["VIOLATION_REMEDIATION_COST_USD"]
    total = token_cost + review_cost + remediation_cost
    return {
        "tokens": tokens,
        "escalations": escalations,
        "violations": violations,
        "successful_outcomes": successes,
        "token_cost_usd": round(token_cost, 6),
        "review_cost_usd": round(review_cost, 6),
        "remediation_cost_usd": round(remediation_cost, 6),
        "total_cost_usd": round(total, 6),
        "cost_per_successful_outcome_usd": round(total / successes, 6) if successes else None,
    }
