# Agent Factory Scaffold — Repo 07

**Beyond the Model** article series | Repo 07

A CLI factory that generates production-ready LangGraph agents in under 30 minutes, with 100% compliance out of the box.

---

## Key Finding

> Factory-generated agents are production-ready in **28 minutes**. Handcrafted: **3 days**.
> Only **3 engineering decisions** instead of 35. **100% compliance** on all 8 checks from the first run.

---

## Install

```bash
pip install -e .
```

## CLI Usage

### Generate an agent

```bash
agent-factory generate --name my-agent --domain retail
```

### Dry-run (no disk writes)

```bash
agent-factory generate --name my-agent --domain retail --dry-run
```

### Validate compliance

```bash
agent-factory validate generated_agents/my-agent
```

### List available templates

```bash
agent-factory list-templates
```

## Dashboard

```bash
uvicorn dashboard.app:app --reload --port 8000
```

Open `http://localhost:8000` — four tabs: Overview, Demo, Metrics, Eval.

---

## Pre-generated Retail Agents

| Agent | Description |
|---|---|
| pricing-monitor | Competitor price analysis and recommendation |
| inventory-alert | Stock level monitoring and reorder triggers |
| returns-processing | Return request triage and decision |
| supplier-query | Supplier performance metric retrieval |
| customer-sentiment | Interaction tone analysis and escalation |
| fraud-flag | Transaction risk scoring and flagging |
| delivery-exception | Shipment exception resolution planning |
| product-recommendation | Session-aware product suggestions |

All 8 pass all 8 compliance checks.

---

## Environment

Copy `.env.example` to `.env` and fill in:

```
ENVIRONMENT=development
AIREFINERY_API_KEY=<your-key>
AIR_MODEL=openai/gpt-oss-120b
```

---

## Compliance Checks (8/8)

1. Harness import (`harness_core` in agent files)
2. Input schema extends `BaseModel`
3. Output schema extends `BaseModel`
4. `AgentHarness` instantiated in `agent.py`
5. Structured logging (`get_logger` used)
6. `config/harness.yaml` present
7. `.env.example` present
8. `agent-harness-core` in `pyproject.toml`

---

## Run Tests

```bash
pytest tests/ -v
```
