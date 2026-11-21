from __future__ import annotations

from pathlib import Path

from cli.validator import CheckResult, ComplianceValidator, ValidationResult


def _failed(result: ValidationResult) -> set[str]:
    return {c.name for c in result.checks if not c.passed}


def test_generated_agent_passes_all_checks(generated: Path) -> None:
    result = ComplianceValidator().validate(generated)
    assert result.all_passed, _failed(result)
    assert result.pass_rate_pct == 100.0


def test_missing_harness_import_fails(generated: Path) -> None:
    (generated / "scenario" / "support.py").write_text("AGENT_ID = 'x'\n")
    assert "Harness import" in _failed(ComplianceValidator().validate(generated))


def test_secret_literal_fails(generated: Path) -> None:
    with (generated / "scenario" / "llm.py").open("a") as fh:
        fh.write('\nclient = AsyncOpenAI(api_key="sk-live-123")\n')
    assert "No secret literal" in _failed(ComplianceValidator().validate(generated))


def test_secret_value_in_env_example_fails(generated: Path) -> None:
    env = generated / ".env.example"
    env.write_text(env.read_text().replace("LLM_API_KEY=", "LLM_API_KEY=abc123"))
    assert "No secret literal" in _failed(ComplianceValidator().validate(generated))


def test_empty_cases_fail(generated: Path) -> None:
    (generated / "scenario" / "cases.json").write_text("[]")
    assert "Eval cases" in _failed(ComplianceValidator().validate(generated))


def test_empty_directory_fails_all(tmp_path: Path) -> None:
    result = ComplianceValidator().validate(tmp_path)
    assert not any(c.passed for c in result.checks)
    assert result.pass_rate_pct == 0.0


def test_pass_rate_is_share_of_checks() -> None:
    checks = [CheckResult(f"c{i}", i < 7, "") for i in range(8)]
    assert ValidationResult("x", checks).pass_rate_pct == 87.5
