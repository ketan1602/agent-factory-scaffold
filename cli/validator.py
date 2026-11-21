from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

_LITERAL_KEY = re.compile(r"""api_key\s*=\s*["'][^"']+["']""")
_ENV_KEYS = ("LLM_API_KEY=", "LLM_BASE_URL=", "LLM_MODEL=")


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


def _text(path: Path, rel: str) -> str:
    target = path / rel
    return target.read_text() if target.is_file() else ""


def _result(name: str, ok: bool, good: str, bad: str) -> CheckResult:
    return CheckResult(name, ok, good if ok else bad)


def _check_harness_import(path: Path) -> CheckResult:
    return _result("Harness import", "from harness_core" in _text(path, "scenario/support.py"),
                   "harness_core imported", "scenario/support.py does not import harness_core")


def _check_capability_harness(path: Path) -> CheckResult:
    return _result("Capability harness", "CapabilityHarness(" in _text(path, "scenario/support.py"),
                   "CapabilityHarness wired", "CapabilityHarness not constructed")


def _check_live_model(path: Path) -> CheckResult:
    return _result("OpenAI-style live model", "AsyncOpenAI(" in _text(path, "scenario/llm.py"),
                   "AsyncOpenAI client in scenario/llm.py", "no AsyncOpenAI client found")


def _check_eval_cases(path: Path) -> CheckResult:
    try:
        cases = json.loads(_text(path, "scenario/cases.json") or "null")
    except json.JSONDecodeError:
        cases = None
    ok = isinstance(cases, list) and len(cases) == 16 and all(
        {"id", "utterance", "expected"} <= set(c) for c in cases)
    return _result("Eval cases", ok, "16 support cases",
                   "scenario/cases.json is not 16 valid cases")


def _check_env_example(path: Path) -> CheckResult:
    text = _text(path, ".env.example")
    ok = all(any(line.startswith(k) for line in text.splitlines()) for k in _ENV_KEYS)
    return _result("Env example", ok, ".env.example lists LLM_* variables",
                   ".env.example is missing an LLM_* variable")


def _check_no_secret_literal(path: Path) -> CheckResult:
    env_key = next((line for line in _text(path, ".env.example").splitlines()
                    if line.startswith("LLM_API_KEY=")), "LLM_API_KEY=x")
    literal = any(_LITERAL_KEY.search(_text(path, f"scenario/{f}"))
                  for f in ("support.py", "llm.py", "cases.py"))
    ok = env_key == "LLM_API_KEY=" and not literal
    return _result("No secret literal", ok, "no key values in code or .env.example",
                   "a secret value is written into code or .env.example")


def _check_harness_dependency(path: Path) -> CheckResult:
    return _result("Harness dependency", "agent-harness-core" in _text(path, "pyproject.toml"),
                   "agent-harness-core in pyproject.toml", "agent-harness-core missing from deps")


def _check_eval_runner(path: Path) -> CheckResult:
    return _result("Eval runner", "run_harnessed" in _text(path, "scripts/run_eval.py"),
                   "scripts/run_eval.py runs every case",
                   "scripts/run_eval.py missing or incomplete")


_CHECKS: list[Callable[[Path], CheckResult]] = [
    _check_harness_import,
    _check_capability_harness,
    _check_live_model,
    _check_eval_cases,
    _check_env_example,
    _check_no_secret_literal,
    _check_harness_dependency,
    _check_eval_runner,
]


class ComplianceValidator:
    def validate(self, agent_path: Path) -> ValidationResult:
        checks = [check(agent_path) for check in _CHECKS]
        return ValidationResult(agent_path=str(agent_path), checks=checks)
