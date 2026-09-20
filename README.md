# Agent Factory Scaffold — Repo 07

**Beyond the Model** article series | Repo 07

A CLI factory that generates production-ready LangGraph agents in under 30 minutes, with 100% compliance out of the box.

---

## Key Finding

> Factory-generated agents are production-ready in **28 minutes**. Handcrafted: **3 days**.
> Only **3 engineering decisions** instead of 35. **100% compliance** on all 8 checks from the first run.

---

## Why This Exists

Building a new agent from scratch forces every engineer to make the same 35 decisions: which retry strategy, which logging format, what the I/O contract looks like, how lifecycle states are tracked, where config lives, what the audit trail captures. Most of these decisions have one right answer — yet each engineer makes them again, inconsistently.

The factory encodes those decisions once. Engineers supply only the three things that are genuinely different per agent: the agent name, the domain, and the business logic inside the nodes.

---

## Framework Architecture

### Stack

| Layer | Technology | Role |
|---|---|---|
| Graph orchestration | LangGraph `StateGraph` | Defines the DAG of nodes and edges |
| LLM backend | AI Refinery SDK (`air.AsyncAIRefinery`) | Makes all LLM calls via OpenAI-compatible API |
| Operational wrapper | `agent-harness-core` `AgentHarness` | Retry, lifecycle, I/O validation, audit, cost tracking |
| I/O contracts | Pydantic v2 `BaseModel` | Input and output schema enforcement |
| Config | YAML + env-var interpolation | 12-factor; no hardcoded values |
| Logging | structlog (`harness_core.get_logger`) | Structured JSON in production |
| CLI | Click | `generate`, `validate`, `list-templates` |
| Template engine | Jinja2 | Renders all agent files from `.j2` templates |
| Dashboard | FastAPI + vanilla JS | Overview, Demo, Metrics, Eval pages |

### The Three-Layer Agent Model

Every generated agent follows a strict three-layer separation:

```
agent/
├── schemas.py    # Layer 1 — I/O contracts (Pydantic BaseModel subclasses)
├── prompts.py    # Layer 2 — LLM instructions (SYSTEM_PROMPT + ANALYSIS_PROMPT)
├── nodes.py      # Layer 2 — Business logic (async LangGraph node functions)
└── agent.py      # Layer 3 — Wiring (LangGraph graph + AgentHarness instantiation)
```

Engineers only touch layers 1 and 2. The operational layer (retry, lifecycle, audit, cost) is inherited from `agent-harness-core` with zero extra code.

### LLM Call Pattern

All agents use a consistent pattern for LLM calls — no framework-specific abstractions, no LangChain message types. The AI Refinery SDK speaks the OpenAI chat completions API:

```python
from air import AsyncAIRefinery

async def analyze(state: dict) -> dict:
    client = AsyncAIRefinery(api_key=os.environ["AIREFINERY_API_KEY"])
    response = await client.chat.completions.create(
        model=os.environ.get("AIR_MODEL", "openai/gpt-oss-120b"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": ANALYSIS_PROMPT.format(**state)},
        ],
        temperature=0.1,
    )
    return json.loads(_strip_markdown(response.choices[0].message.content))
```

The LLM client is imported inside the function body so tests can patch `air.AsyncAIRefinery` at the module level without import-time side effects.

### Graph Structure

All generated agents use a single-node graph as a starting point. This is intentional — it compiles and is immediately testable. Engineers add nodes as the use case demands:

```python
def _build_graph():
    g = StateGraph(dict)
    g.add_node("analyze", analyze)   # add more nodes here
    g.set_entry_point("analyze")
    g.add_edge("analyze", END)
    return g.compile()
```

The compiled graph is wrapped in `AgentHarness`, which adds retry, lifecycle management, contract validation, audit logging, and token cost tracking automatically — no extra code in the node functions.

### Generator Logic

`AgentGenerator` renders 8 Jinja2 templates per agent using a two-step context build:

1. **Domain config load** — reads `templates/domains/{domain}/config.yaml` for domain description, LLM instructions, and default model
2. **Context build** — converts kebab-case agent name to PascalCase class name (e.g. `pricing-monitor` → `PricingMonitor`), merges with domain config
3. **Template render** — Jinja2 renders each `.j2` template with the merged context
4. **File write** — target paths under `generated_agents/{agent_name}/`; `dry_run=True` skips disk writes for dashboard previews

```python
context = {
    "agent_name":          "pricing-monitor",
    "agent_class_name":    "PricingMonitor",
    "domain":              "retail",
    "domain_description":  "retail operations and commerce automation",
    "domain_instructions": "Focus on business impact: pricing, margins ...",
    "default_model":       "openai/gpt-oss-120b",
}
```

### Compliance Validation Logic

`ComplianceValidator` runs 8 pure check functions via a dispatch list. Each check reads files on disk and returns a `CheckResult(name, passed, message)`. The dispatch pattern makes adding new checks a one-line change with no branching:

```python
_CHECKS: list[Callable[[Path], CheckResult]] = [
    _check_harness_import,      # harness_core in agent/*.py
    _check_input_schema,        # Input(BaseModel) in schemas.py
    _check_output_schema,       # Output(BaseModel) in schemas.py
    _check_harness_instantiation,  # AgentHarness( in agent.py
    _check_logging,             # get_logger or structlog in agent/*.py
    _check_harness_yaml,        # config/harness.yaml exists
    _check_env_example,         # .env.example exists
    _check_pyproject_deps,      # agent-harness-core in pyproject.toml
]
```

A generated agent passes all 8 checks on the first run because the factory encodes compliance into the templates, not as a post-hoc audit.

### Template System

Templates live in `templates/base/` as `.j2` files. Domain-specific context is in `templates/domains/{domain}/config.yaml`. Adding a new domain requires one YAML file — no code changes.

```
templates/
├── base/
│   ├── schemas.py.j2      # Input/Output Pydantic models with domain context
│   ├── agent.py.j2        # AgentHarness wiring
│   ├── nodes.py.j2        # AI Refinery LLM call pattern
│   ├── prompts.py.j2      # SYSTEM_PROMPT + ANALYSIS_PROMPT
│   ├── init.py.j2         # re-exports harness
│   ├── pyproject.toml.j2  # deps including agent-harness-core
│   ├── harness.yaml.j2    # operational config
│   └── env_example.j2     # AIREFINERY_API_KEY, AIR_MODEL
└── domains/
    ├── retail/config.yaml
    ├── finance/config.yaml
    ├── healthcare/config.yaml
    └── hr/config.yaml
```

---

## Pre-Generated Scenarios — 8 Retail Agents

All 8 agents were generated using `agent-factory generate --domain retail` and are committed to this repo as reference output. Each demonstrates a distinct retail use case while sharing identical operational structure.

### 1. pricing-monitor

**Scenario:** Monitor competitor pricing in real time and recommend whether to hold, raise, or lower a product's price.

**Input:** `product_id`, `current_price`, `competitor_prices` (list), `category`

**Output:** `product_id`, `recommendation` (hold/raise/lower), `suggested_price`, `price_change_pct`, `reasoning`

**Agent logic:** Passes current and competitor prices to the LLM as structured JSON. Parses the recommendation back as JSON. Falls back to "maintain" if the LLM response is unparseable.

---

### 2. inventory-alert

**Scenario:** Detect when stock is trending toward stockout, compute days until stockout, and recommend a reorder quantity.

**Input:** `sku`, `current_stock`, `reorder_point`, `lead_days`, `avg_daily_sales`

**Output:** `sku`, `alert_level` (none/low/critical), `recommended_order_qty`, `days_until_stockout`, `message`

**Agent logic:** Computes stockout risk from sales velocity. The LLM interprets edge cases (e.g. seasonal demand, lead time uncertainty) and produces a natural-language recommendation message alongside the structured fields.

---

### 3. returns-processing

**Scenario:** Triage a return request: approve, escalate to human review, or flag for fraud investigation.

**Input:** `order_id`, `customer_id`, `item_count`, `total_value`, `reason`

**Output:** `order_id`, `decision` (approve/escalate/investigate), `refund_amount`, `processing_days`, `instructions`

**Agent logic:** The LLM evaluates the return reason against policy. High-value returns or suspicious patterns route to escalation. The harness contract validates that `refund_amount` is always present, preventing silent failures.

---

### 4. supplier-query

**Scenario:** Answer a structured question about a supplier's performance metrics for a given period.

**Input:** `supplier_id`, `query_type` (on-time-rate/defect-rate/lead-time), `period`, `metric`

**Output:** `supplier_id`, `response`, `metric_value`, `trend` (improving/stable/declining), `follow_up_needed`

**Agent logic:** Formats the query as a prompt with explicit field names. The LLM synthesises the metric assessment and determines whether a follow-up action is warranted. Structured output ensures downstream systems can act on `follow_up_needed` without parsing prose.

---

### 5. customer-sentiment

**Scenario:** Score the sentiment of a customer service interaction and recommend the next action.

**Input:** `customer_id`, `interaction_text`, `channel` (email/chat/call), `touchpoint`

**Output:** `customer_id`, `sentiment` (positive/neutral/negative/critical), `score` (0–1), `action_recommended`, `priority` (low/medium/high/urgent)

**Agent logic:** Channel context shapes the system prompt — a chat message is scored differently from a formal complaint email. The LLM returns a `score` plus a human-readable `action_recommended`. Priority is derived from score and channel.

---

### 6. fraud-flag

**Scenario:** Score a transaction for fraud risk and decide whether to approve, flag for review, or decline.

**Input:** `transaction_id`, `amount`, `merchant_category`, `is_online`, `customer_history_score`

**Output:** `transaction_id`, `risk_level` (low/medium/high/critical), `risk_score` (0–1), `flags` (list of signal names), `action` (approve/review/decline)

**Agent logic:** The LLM is prompted to identify specific fraud signals (velocity, category mismatch, online-vs-card-present anomaly) and return them as a list. The harness validates that `flags` is always a list, preventing type errors downstream.

---

### 7. delivery-exception

**Scenario:** Resolve a shipment exception — compute a revised ETA, draft a customer notification, and decide whether to escalate.

**Input:** `shipment_id`, `exception_type` (weather/customs/carrier/address), `current_location`, `original_eta`, `delay_hours`

**Output:** `shipment_id`, `resolution`, `revised_eta`, `customer_notification`, `escalate` (bool)

**Agent logic:** Exception type drives the system prompt. A customs hold has different resolution steps than a weather delay. The LLM produces a plain-English `customer_notification` ready to send, plus a structured `escalate` flag for the logistics system to act on.

---

### 8. product-recommendation

**Scenario:** Recommend products to a customer based on their browsing history and current cart.

**Input:** `customer_id`, `session_id`, `viewed_categories` (list), `cart_value`

**Output:** `customer_id`, `recommendations` (list of product names), `confidence_scores` (list of floats), `reasoning`

**Agent logic:** Browsing category list and cart value together give the LLM context about intent and price sensitivity. The LLM returns a ranked list. The harness output contract validates that `recommendations` and `confidence_scores` are both lists of equal length before returning to the caller.

---

## Install

```bash
pip install -e .
```

## CLI Usage

```bash
# Generate a new agent
agent-factory generate --name price-optimizer --domain retail

# Dry-run — preview file list without writing
agent-factory generate --name price-optimizer --domain retail --dry-run

# Validate compliance of any agent directory
agent-factory validate generated_agents/pricing-monitor

# List available domain templates
agent-factory list-templates
```

## Dashboard

```bash
uvicorn dashboard.app:app --reload --port 8000
```

Four pages at `http://localhost:8000`:

| Page | What it shows |
|---|---|
| Overview | Key finding, stats (28 min / 8 agents / 100%) |
| Demo | Live generate form — enter name + domain, see file tree + compliance |
| Metrics | Time comparison chart, decisions eliminated, 8-item checklist |
| Eval | Eval results for all 8 pre-generated agents |

## Environment

```
ENVIRONMENT=development
AIREFINERY_API_KEY=<your-key>
AIR_MODEL=openai/gpt-oss-120b
```

## Compliance Checks (8/8)

| # | Check | What it verifies |
|---|---|---|
| 1 | Harness import | `harness_core` imported in `agent/*.py` |
| 2 | Input schema | `Input(BaseModel)` defined in `schemas.py` |
| 3 | Output schema | `Output(BaseModel)` defined in `schemas.py` |
| 4 | AgentHarness | `AgentHarness(` instantiated in `agent.py` |
| 5 | Structured logging | `get_logger` or `structlog` used in `agent/*.py` |
| 6 | harness.yaml | `config/harness.yaml` present |
| 7 | .env.example | `.env.example` present |
| 8 | Harness dependency | `agent-harness-core` in `pyproject.toml` |

## Run Tests

```bash
pytest tests/ -v
```

16 tests — all pass with zero API calls (AI Refinery is mocked via `unittest.mock`).

## Foundation

Installs `agent-harness-core` from:
```
git+https://github.com/ketan1602/agent-harness-core.git@v1.0.0
```

All operational concerns (retry, lifecycle, audit, cost tracking) live in that package. This repo contains only the factory, the templates, and the generated agents.
