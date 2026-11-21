# Agent Factory Scaffold — Repo 07

**Harness Engineering** article series | ENG-10 *Agent Factories: Industrialising Agent Delivery*

A factory that stamps out the support agent from the harness-foundations article, wired to
`agent-harness-core` 1.5.1, with a live OpenAI-compatible model, an eval runner and compliance
checks. Every number below is measured from a live run in `measurements/factory_performance.json`.

---

## Measured result (one live run)

| Measure | Value | Source |
|---|---|---|
| Model | `openai/gpt-oss-120b` via an OpenAI-compatible endpoint | `measurements/factory_performance.json` |
| Generate, then live eval, end to end | 0.44 min (generate 0.01 s, eval 26.2 s) | same |
| Eval cases passed | **13 / 16** | `generated_agents/support-agent/measurements/eval_results.json` |
| First passing eval | **no** (see the three misses below) | same |
| Tokens reported by the model API | 11,599 across 16 runs | same |
| Compliance checks | 8 / 8 | `agent-factory validate` |

**Three misses, one pattern.** `refund_approved-1`, `refund_rejected-1` and `refund_bad_approver-1`
each expect `issue_refund`. The model chose `create_ticket` in all three. It is one run, so this is a
single sample. The spine's recorded runs for other models chose `issue_refund` on these cases, but
this model has no recorded results in the spine to compare against.

Not measured: a handcrafted baseline. Earlier drafts quoted "3 days" and "35 decisions" without
measuring either. Those figures are removed. Any baseline in the article needs its own labelled
assumption.

---

## Install and run

```bash
pip install "agent-harness-core @ git+https://github.com/ketan1602/agent-harness-core.git@v1.5.1"   # harness-core 1.5.1 from the GitHub tag
pip install -e .
cp .env.example .env          # fill LLM_API_KEY and LLM_BASE_URL (never commit .env)

agent-factory generate --name support-east           # writes generated_agents/support-east
agent-factory validate generated_agents/support-east # 8 compliance checks
agent-factory measure --name support-east            # generate + live eval + measured report
python generated_agents/support-east/scripts/run_eval.py   # re-run the eval alone
uvicorn dashboard.app:app --reload --port 8000             # Overview, Demo, Metrics, Eval
```

`measure` runs the generated agent in the same interpreter, so the factory environment needs
`agent-harness-core` and `openai` installed. A failing eval still writes the report; it is recorded,
not hidden. The exit code is 1 when any case fails.

---

## How the factory works

```
templates/spine/   vendored from the harness-foundations scenario (scenario/, scripts/run_eval.py)
templates/base/    pyproject.toml.j2, env_example.j2, README.md.j2
        │
        ▼  AgentGenerator.generate(name)
generated_agents/<name>/
  scenario/support.py   CapabilityHarness wired to ten capabilities (AGENT_ID stamped with <name>)
  scenario/llm.py       AsyncOpenAI client, configured by LLM_API_KEY / LLM_BASE_URL / LLM_MODEL
  scenario/cases.py     runs a case through the harness
  scenario/cases.json   the 16 support cases
  scripts/run_eval.py   runs every case, writes measurements/eval_results.json
        │
        ▼  ComplianceValidator (8 checks) and measure() (timings, tokens, pass counts)
```

- **Only `AGENT_ID` changes per agent.** The scenario is the spine's, unmodified, so the factory's
  output is the same agent under a different name. That is the point of the factory, not a bug.
- **Model calls.** `live_model` sends one chat completion per case, parses the JSON tool decision,
  and records the API's `usage` tokens. A case's declared `estimated_tokens` overrides measured usage,
  as in the spine.
- **Harness.** `harness_core.capabilities.CapabilityHarness` enforces tool grants, budget, context
  filtering, approval routing and retries. The eval reads each run's verdict from the Evaluation
  capability.
- **Compliance checks** test the layout: the harness import and construction, the OpenAI-style
  client, 16 valid cases, the `LLM_*` variables in `.env.example`, no secret literals in code or the
  example file, the harness dependency, and the eval runner. They confirm wiring, not behaviour.
  Behaviour is the eval.

---

## Decisions made in this build

Each entry is a decision taken during the rebuild, with its reason.

1. **Scenario = the harness-foundations support agent.** The series spine. The retail domains were
   replaced because they had no shared cases and could not be compared across articles.
2. **Vendor the scenario, do not depend on it.** The spine is not a published package. Copying it
   into `templates/spine/` keeps generated agents self-contained. The cost is drift: the copy is
   checked by eye against its source, not by a test.
3. **Stamp only `AGENT_ID`.** Any other per-agent variation would fork the scenario.
4. **Use `agent-harness-core` 1.5.1, not the 1.0.0 tag.** The spine and the ENG-06 brief both use the
   `CapabilityHarness` API. The 1.0.0 `AgentHarness` wrapper does not match it.
5. **OpenAI-style client on an AI Refinery endpoint.** `AsyncOpenAI` with `LLM_*` variables. The
   endpoint is set by `LLM_BASE_URL`, not by code. No vendor name is in the code.
6. **Measure the first eval run, and keep the failures.** No re-runs were used to replace the first
   sample.
7. **Remove the hardcoded timings and the eight retail agents.** They were not measured, and
   recoverable from git history at `3675c65`.
8. **Ruff excludes `templates/spine/`.** It is verbatim from its source repo, which is linted there.

---

## Open items

- **LangGraph.** The series rule is LangGraph for agent graphs. The spine's support agent is a single
  model decision run through `harness_core` capabilities, with no LangGraph graph. This build follows
  the spine. Confirm before the article calls it a LangGraph agent.
- **One model, one sample.** The live result is one run of one model. Repeats and a second model are
  needed before any claim about stability.

---

## Tests

```bash
pytest tests/ -v     # 26 tests, zero live calls
ruff check .
```

The measure test replaces the live subprocess with a fake that writes a results file.
