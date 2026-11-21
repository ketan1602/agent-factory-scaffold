from __future__ import annotations

from cli.gate import evaluate_gate


def _rows(passed: int, total: int, violated: int = 0) -> list[dict]:
    return [{"passed": i < passed, "violated": i < violated} for i in range(total)]


def test_meets_thresholds_is_released(manifest) -> None:
    gate = evaluate_gate(manifest, _rows(20, 20))
    assert not gate.blocked and gate.reasons == []


def test_pass_rate_below_minimum_blocks(manifest) -> None:
    gate = evaluate_gate(manifest, _rows(13, 16))
    assert gate.blocked
    assert gate.pass_rate == 0.8125
    assert "pass rate 0.812 is below 0.98" in gate.reasons[0]


def test_any_critical_violation_blocks_when_none_allowed(manifest) -> None:
    gate = evaluate_gate(manifest, _rows(20, 20, violated=1))
    assert gate.blocked
    assert gate.critical_violations == 1
    assert any("critical" in r for r in gate.reasons)


def test_empty_results_block(manifest) -> None:
    assert evaluate_gate(manifest, []).blocked
