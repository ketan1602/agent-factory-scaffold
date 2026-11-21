from __future__ import annotations

from dataclasses import asdict, dataclass

from cli.manifest import Manifest


@dataclass(frozen=True)
class GateResult:
    pass_rate: float
    minimum_pass_rate: float
    critical_violations: int
    critical_violations_allowed: int
    blocked: bool
    reasons: list[str]

    def as_dict(self) -> dict:
        return asdict(self)


def evaluate_gate(manifest: Manifest, results: list[dict]) -> GateResult:
    """Apply the manifest's own release thresholds to one agent's eval results."""
    evaluation = manifest.spec.evaluation
    total = len(results)
    pass_rate = sum(r["passed"] for r in results) / total if total else 0.0
    critical = sum(1 for r in results if r["violated"])
    reasons = []
    if pass_rate < evaluation.minimumPassRate:
        reasons.append(f"pass rate {pass_rate:.3f} is below {evaluation.minimumPassRate}")
    if critical > evaluation.criticalViolationsAllowed:
        allowed = evaluation.criticalViolationsAllowed
        reasons.append(f"{critical} critical violation(s), {allowed} allowed")
    return GateResult(
        pass_rate=round(pass_rate, 4),
        minimum_pass_rate=evaluation.minimumPassRate,
        critical_violations=critical,
        critical_violations_allowed=evaluation.criticalViolationsAllowed,
        blocked=bool(reasons),
        reasons=reasons,
    )
