# Agent Factory Scaffold — Repo 07

Companion repo for **ENG-10 Agent Factories: Industrialising Agent Delivery** (Harness Engineering series).
The article is in [docs/article.md](docs/article.md). Every number in it comes from
[measurements/release.json](measurements/release.json), [measurements/online.json](measurements/online.json)
or the per-agent eval files.

The factory takes a manifest per agent, generates the agent on `agent-harness-core` 1.5.1, runs its
eval against a live OpenAI-compatible model, applies a completion guard, applies the manifest's release
gate, and records cost. An online monitor checks the guard over recorded runs.

## What is in the repo

| Path | Role |
|---|---|
| `manifests/*.yaml` | One contract per agent: owner, tool grants, budget, approval rule, eval file, release thresholds |
| `cases/*.json` | Eval cases per agent (`support-agent` is the harness-foundations spine, 16 cases) |
| `templates/spine/` | Scenario code vendored from harness-foundations; identity and grants come from `config.py` |
| `templates/spine/scenario/guard.py` | Completion guard and the online miss monitor |
| `templates/base/` | Jinja2 templates for `config.py`, `pyproject.toml`, `.env.example`, `README.md` |
| `cli/generator.py` | Renders an agent from its manifest |
| `cli/manifest.py` | Validates a manifest (pydantic) and rejects unknown tools |
| `cli/validator.py` | Eight structural compliance checks |
| `cli/gate.py` | Applies the manifest's `minimumPassRate` and `criticalViolationsAllowed` |
| `cli/economics.py` | Token cost is measured; review and remediation are labelled assumptions |
| `cli/release.py` | Generates, evaluates, gates and costs every manifest; writes `measurements/release.json` |
| `cli/online.py` | Checks recorded runs for silent refund misses; writes `measurements/online.json` |
| `dashboard/` | FastAPI + static UI reading the release and online reports |
| `.github/workflows/` | `ci.yml` (lint, offline tests, dry-run generation) and `live-release.yml` (manual, live model) |

## Results from the committed release

Model `openai/gpt-oss-120b` via an OpenAI-compatible endpoint. Run 3 (with the guard) is the committed release.
Run 2 (before the guard) and run 1 (unscoped prompt) are kept as evidence.

| Agent | Cases (run 3) | Pass rate | Gate | Refund requests escalated by guard | Compliance |
|---|---|---|---|---|---|
| ticket-triage | 7/7 | 1.000 | RELEASED | 1 (injection case) | 8/8 |
| case-notes | 5/5 | 1.000 | RELEASED | 0 | 8/8 |
| refund-desk | 5/8 | 0.625 | BLOCKED | 5 | 8/8 |
| support-agent | 13/16 | 0.8125 | BLOCKED | 5 | 8/8 |

- **Guard.** Before the guard, 11 refund requests ended without a refund or an approval hold: 10 completed with a note or ticket, and one was terminated by the budget. With the guard, all 11 escalate, and the online monitor finds zero silent misses.
- **The guard does not change pass rates.** The eval still fails the same cases, because a refund that becomes a note is still wrong. The guard changes what happens to the customer.
- **Cost.** Run 3 total $78.04: $0.12 token cost and $77.92 human review (escalations at the labelled $85/hour, 5 minutes each). Cost per successful outcome: $2.60. Before the guard the same release reported $0.004, because escalations were never counted.
- **Zero critical violations** in all three runs.

## Known gaps

- **Approval resume not exercised live.** The guard escalates a refund before any approval is granted, so no run was approved through the harness's resume path. That path is covered by unit tests only.
- **Cases are authored, not reviewed by domain owners.** The 20 cases in `ticket-triage`, `refund-desk` and `case-notes` were written for this release.
- **One model, repeated runs.** The same `support-agent` cases miss in every run. That is a repeat, not an independent sample.
- **Online monitoring replays recorded eval runs.** It is not live production traffic.
- **Not built:** deployment, rollback, a registry, live production monitoring, and a learning loop from production evidence.

## Decisions taken in this build

1. **Scenario: the harness-foundations support agent, plus three role agents.** Role agents reuse the spine's tools and violation categories.
2. **Manifest fields are only those the harness enforces.** Tool allow-list, budget, approval limit, approvers, eval file and gate thresholds. Identity, memory and a deny list are not in the manifest, because nothing enforces them.
3. **Prompt lists only granted tools.** Found in run 1 when `case-notes` was blocked. The spine's prompt listed every tool; the vendored `llm.py` now builds its list from the manifest.
4. **Escalation is counted from the approval path and the guard, not an event name.** The spine checked for `run.awaiting_approval`, which harness-core 1.5.1 does not emit.
5. **Completion guard lives in the scenario, not in harness-core.** A refund request that is neither refunded nor held for approval or rejected escalates to a human. The shared harness library is unchanged; the guard is in `templates/spine/scenario/guard.py`. Moving it into harness-core is a separate decision.
6. **Passed is judged before the guard.** The guard does not turn a failed case into a pass. `status` is `escalated` for guarded runs.
7. **Cost assumptions must be set, with no defaults.** `LLM_COST_PER_1K_TOKENS`, `HUMAN_APPROVAL_MINUTES`, `HUMAN_REVIEW_RATE_PER_HOUR` and `VIOLATION_REMEDIATION_COST_USD`. The release refuses to run without them, before any live call.
8. **Gate thresholds from the manifest.** `minimumPassRate: 0.98` and `criticalViolationsAllowed: 0`. With 5 to 16 cases per agent, 0.98 means every case must pass.
9. **Harness-core is pinned to the GitHub tag `v1.5.1`.** No local path is used.
10. **LangGraph is not used.** Each agent is a single model decision run through harness-core capabilities. This follows the spine.

## Install and run

```bash
pip install "agent-harness-core @ git+https://github.com/ketan1602/agent-harness-core.git@v1.5.1"
pip install -e .
cp .env.example .env   # fill LLM_API_KEY, LLM_BASE_URL, plus the four cost assumptions

agent-factory generate --manifest manifests/ticket-triage.yaml --dry-run
agent-factory validate generated_agents/ticket-triage
agent-factory release            # all manifests, live model; exit 1 if any gate blocks
agent-factory online             # guard monitor over recorded runs; exit 1 on a silent miss
uvicorn dashboard.app:app --reload --port 8000
```

`release` runs each generated agent in the same interpreter, so the factory environment needs
`agent-harness-core` and `openai`. A failing eval is still recorded; it is never hidden.

## Tests

```bash
pytest tests/ -v   # 48 tests, no live model calls
ruff check .
```

`ruff` excludes `templates/spine/` and `generated_agents/`, which are verbatim copies of the scenario code.
