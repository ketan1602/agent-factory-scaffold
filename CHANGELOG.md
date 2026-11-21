## [0.2.0] - 2026-11-21

### Changed
- The factory now generates the harness-foundations support agent (16 cases, 14 categories) instead of retail domain agents.
- Live model calls use the OpenAI-compatible client (`AsyncOpenAI`) configured by `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`.
- The harness is `agent-harness-core` 1.5.1 (`CapabilityHarness`), replacing the 1.0.0 `AgentHarness` wrapper.
- `measurements/factory_performance.json` now holds only measured values from a live run. The hardcoded 28-minute, 3-day and 3-vs-35-decision figures were removed.
- Dashboard Metrics and Eval read measured files; nothing is hardcoded.

### Added
- `agent-factory measure --name NAME`: generates the agent, runs the 16 cases against the live model, and records timings, tokens and pass counts.
- `scripts/run_eval.py` in every generated agent, writing `measurements/eval_results.json`.
- Compliance checks rewritten for the spine layout (harness wiring, live model, eval cases, env completeness, no secret literals, runner present).

### Removed
- Domain templates (retail, finance, healthcare, hr), `list-templates`, and the 8 pre-generated retail agents (recoverable from git history at 3675c65).

## [0.1.0] - 2026-09-20

### Added
- agent-factory CLI with generate, validate, list-templates subcommands
- Jinja2 template engine with 4 domain configs (retail, finance, healthcare, hr)
- ComplianceValidator with 8 checks against golden path standard
- 8 pre-generated retail agents demonstrating factory output
- Dashboard with Overview, Demo, Metrics, and Eval pages
