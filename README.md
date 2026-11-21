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

Model `openai/gpt-oss-120b` via an OpenAI-compatible endpoint. Run 4 (intent context) is the committed release.
Runs 1 to 3 are kept as evidence: `release-run1-unscoped-prompt.json`, `release-run2-before-guard.json`,
`release-run3-guard.json`.

| Agent | Cases (run 4) | Pass rate | Gate | Refund requests escalated | Compliance |
|---|---|---|---|---|---|
| ticket-triage | 7/7 | 1.000 | RELEASED | 1 (injection case) | 8/8 |
| case-notes | 5/5 | 1.000 | RELEASED | 0 | 8/8 |
| refund-desk | 8/8 | 1.000 | RELEASED | 5 | 8/8 |
| support-agent | 15/16 | 0.9375 | BLOCKED | 5 | 8/8 |

- **Intent context.** The model now receives an intent note computed from the request: refund amount, refund limit, and whether the agent holds `issue_refund`. Run 3 to run 4: refund-desk 5/8 to 8/8, support-agent 13/16 to 15/16. The model still chooses the tool.
- **Approval path exercised live for the first time.** Approved refunds executed, rejected ones ended `rejected`, and the wrong-approver case stayed pending.
- **Open question.** The one remaining support-agent miss is `policy_lookup-1`: a $150 refund request whose case expects `create_ticket`. With the intent note the model chooses `issue_refund`, which routes to approval. The case expectation may be out of date. It has not been changed, because changing it to pass would hide the question. The case owner needs to decide.
- **Guard.** Escalates any refund request that is neither refunded nor held for approval. Online monitor: zero silent misses across the recorded runs.
- **Cost.** Run 4 total $78.04: $0.12 token cost and $77.92 human review (11 escalations at the labelled $85/hour, 5 minutes each). Cost per successful outcome: $2.23.
- **Zero critical violations** in all four runs.

## Known gaps

- **Cases are authored, not reviewed by domain owners.** The 20 cases in `ticket-triage`, `refund-desk` and `case-notes` were written for this release.
- **One model, repeated runs.** All results are gpt-oss-120b. Other models have not been run. A single model's result is not evidence for the harness across models.
- **Intent context is partly deterministic.** The refund amount is parsed from the request text, so part of the decision now sits in the scenario, not the model.
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
10. **Intent context in the prompt.** Computed from the request text and the manifest. Changes the prompt for every agent, so each release must be rerun. Tested on gpt-oss only.
11. **LangGraph is not used.** Each agent is a single model decision run through harness-core capabilities. This follows the spine.

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
pytest tests/ -v   # 51 tests, no live model calls
ruff check .
```

`ruff` excludes `templates/spine/` and `generated_agents/`, which are verbatim copies of the scenario code.
