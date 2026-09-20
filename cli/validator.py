from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str


@dataclass
class ValidationResult:
    agent_path: str
    checks: list[CheckResult]

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def pass_rate_pct(self) -> float:
        if not self.checks:
            return 0.0
        return sum(1 for c in self.checks if c.passed) / len(self.checks) * 100


def _check_harness_import(path: Path) -> CheckResult:
    files = list((path / "agent").glob("*.py")) if (path / "agent").exists() else []
    ok = any("harness_core" in f.read_text() for f in files)
    return CheckResult(
        "Harness import",
        ok,
        "harness_core imported" if ok else "harness_core not found",
    )


def _check_input_schema(path: Path) -> CheckResult:
    s = path / "agent" / "schemas.py"
    ok = s.exists() and "Input(BaseModel)" in s.read_text()
    return CheckResult(
        "Input schema",
        ok,
        "Input schema extends BaseModel" if ok else "Missing Input schema",
    )


def _check_output_schema(path: Path) -> CheckResult:
    s = path / "agent" / "schemas.py"
    ok = s.exists() and "Output(BaseModel)" in s.read_text()
    return CheckResult(
        "Output schema",
        ok,
        "Output schema extends BaseModel" if ok else "Missing Output schema",
    )


def _check_harness_instantiation(path: Path) -> CheckResult:
    a = path / "agent" / "agent.py"
    ok = a.exists() and "AgentHarness(" in a.read_text()
    return CheckResult(
        "AgentHarness instantiation",
        ok,
        "AgentHarness instantiated" if ok else "AgentHarness not found",
    )


def _check_logging(path: Path) -> CheckResult:
    files = list((path / "agent").glob("*.py")) if (path / "agent").exists() else []
    ok = any(
        ("get_logger" in f.read_text() or "structlog" in f.read_text()) for f in files
    )
    return CheckResult(
        "Structured logging",
        ok,
        "get_logger used" if ok else "No structured logging found",
    )


def _check_harness_yaml(path: Path) -> CheckResult:
    ok = (path / "config" / "harness.yaml").exists()
    return CheckResult(
        "harness.yaml",
        ok,
        "config/harness.yaml present" if ok else "Missing config/harness.yaml",
    )


def _check_env_example(path: Path) -> CheckResult:
    ok = (path / ".env.example").exists()
    return CheckResult(
        ".env.example",
        ok,
        ".env.example present" if ok else "Missing .env.example",
    )


def _check_pyproject_deps(path: Path) -> CheckResult:
    p = path / "pyproject.toml"
    ok = p.exists() and "agent-harness-core" in p.read_text()
    return CheckResult(
        "Harness dependency",
        ok,
        "agent-harness-core in pyproject.toml" if ok else "agent-harness-core missing from deps",
    )


_CHECKS: list[Callable[[Path], CheckResult]] = [
    _check_harness_import,
    _check_input_schema,
    _check_output_schema,
    _check_harness_instantiation,
    _check_logging,
    _check_harness_yaml,
    _check_env_example,
    _check_pyproject_deps,
]


class ComplianceValidator:
    def validate(self, agent_path: Path) -> ValidationResult:
        checks = [check(agent_path) for check in _CHECKS]
        return ValidationResult(agent_path=str(agent_path), checks=checks)
