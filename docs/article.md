# Agent Factories: Industrialising Agent Delivery

*Building an agent is becoming easy. Deciding whether it may ship, and who answers for it afterwards, is not.*

**Platform Engineering Series | ENG-10 | Enterprise Agentic AI**

---

In one release, a customer asked for a refund of $180. The agent replied with a note. The run completed. The customer got no refund, and nothing in the system called that a failure.

That is the problem this article is about. Building an agent is now cheap enough that most enterprises can do it in a week. Knowing whether the agent should act, on whose authority, and at what cost is still slow, and most of the delay sits in places nobody measures. I built a small factory to make those places visible, and ran it on four agents and two models. The results are modest. The argument is not.

## The next bottleneck is not building agents

Cloud computing made a virtual machine easy to create. The hard work was provisioning standards, identity, network controls, deployment pipelines, cost management and operational ownership. Kubernetes followed the same path. Deploying a container was simple. Letting hundreds of teams deploy consistently was an engineering problem of a different kind.

Agents are heading the same way, and they are harder. An application runs logic its developers wrote. An agent interprets a goal, chooses tools, and can take different paths for similar requests. Its behaviour depends on the model, the instructions, the retrieved knowledge, the tool responses, the policies and the context at the moment of the call. Traditional engineering practice remains necessary. It is not enough, because a passing test shows that code runs, not that the agent chose well.

So the platform question changes. It is no longer how to build one agent. It is how to deliver agents across an enterprise so that each one is generated from a shared contract, tested on realistic cases, gated on evidence and costed the same way every time. I call the system that does this an **Agent Factory**.

## What an Agent Factory is

I define it as a platform capability that standardises the creation, validation, release and operation of agents through shared contracts, common controls and measurable release gates.

The word "factory" can mislead. I am not proposing identical agents. A support triage agent and a refund approver should behave differently, carry different authority and face different risk. The factory standardises how agents are engineered, tested, released and costed. It does not force them to solve the same problem the same way.

The factory also does not replace the runtime harness. The harness governs an agent while it runs: which tools it may call, how much it may spend, when a human must approve. The factory governs how the agent came to exist and whether it is fit to run. A factory without a runtime harness produces agents quickly and leaves each team to write its own controls. A harness without a factory makes individual agents safer and does nothing about the hundreds that follow.

*[Figure 1: `docs/images/figure-factory-flow.png`. One manifest drives one generated agent, one harness run, one eval and one gate.]*

*Figure 1. Measured and assumed inputs are kept apart in the release report. Assumptions have no defaults.*

## The manifest is the contract

Most agent projects keep their operating boundaries in code, scattered across prompts, wrappers and config. The factory puts them in one file per agent. This is the manifest for the ticket-triage agent, as it runs in the repository:

```yaml
apiVersion: agents.enterprise/v1
kind: Agent
metadata:
  name: ticket-triage
  version: 1.0.0
  owner: customer-operations
spec:
  runtime: agent-harness-core 1.5.1 (CapabilityHarness)
  scope: support
  tools:
    allow: [create_ticket, add_note]
  budget:
    maxTokens: 5000
    maxCostUsd: 0.25
  approval:
    refundAboveAmount: 100
    approvers: [supervisor-1]
  evaluation:
    cases: ticket-triage.json
    minimumPassRate: 0.98
    criticalViolationsAllowed: 0
```

Every field here is enforced by something. The tool list becomes the runtime's grant table, so a call to `issue_refund` from this agent is blocked by the platform, whatever the model decides. The budget is a runtime limit. The approval rule routes large refunds to a named approver. The thresholds feed the release gate.

I left out fields that nothing enforces. An early draft had identity mode, memory settings and a deny list. Those would have read as controls and would not have been controls, so they came out. A manifest that claims more than the platform enforces gives the reader false confidence, which is the failure this series is about.

The manifest also names an owner. `customer-operations` owns the outcome the agent delivers. The platform team owns the generator and the gate. Neither one decides what the agent is allowed to do on the business's behalf.

## Where the factory's failures come from

The first release of the factory blocked three of four agents. The cause was not the model or the business logic. The scenario's prompt listed every tool the scenario knew about, not the tools each agent was granted. The `case-notes` agent, which may only add notes, was offered `create_ticket`. When the model chose it, the runtime refused, and the run failed.

The defect was in generation, not in execution. The factory stamped out the prompt the same way for every agent, so the mistake was copied into every agent at once. That is the core risk of industrialisation. A flaw in a template reaches every agent generated from it, and it does so quietly.

The fix was to build the prompt from the manifest. The second release passed `case-notes` five of five. The lesson for platform teams is that the generator is production code. It needs the same evidence as the agents it produces, and the release gate is the place to catch what it gets wrong.

## Capability is what gets measured, process is what gets judged

A successful pilot proves that a tool works. It does not prove that a firm can use it. The management series makes this point at firm level: pilots measure capability, and production depends on process. The factory makes the same distinction at agent level, and the distinction is what gives the release gate its meaning.

The eval measures capability. For each case, it checks whether the agent chose the expected action and reached the expected status. The release gate judges process. It asks whether the boundaries held, whether critical violations occurred, and whether the pass rate met the threshold the manifest sets.

These are different questions, and the difference matters. In the first guarded release, `refund-desk` was blocked at five of eight cases. The harness held every boundary in those runs. The agent still did not do the job. The gate blocked it for the capability gap, and the boundary result showed the process was intact. A release process that conflates the two will ship agents that are safe and useless, or useful and unsafe, without anyone noticing which.

## The guard: a control that can disagree with the model

A harness can stop an agent from doing what it may not do. It cannot make the agent do what it should. The refund case showed the gap. The grant allowed `add_note`, so the runtime let the note through, and the run completed. The boundary held. The customer was still owed a refund.

The management series argues that a control that cannot disagree with the system it governs is not a control. The completion guard is the factory's attempt to meet that standard. It checks each refund request against the outcome. If the request names an amount and the run ends neither refunded nor held for approval, the guard escalates the request to a person.

The guard does not make the model choose correctly. It makes the wrong choice visible and routes it to a human. In our runs, the escalations are where the economics of the factory become real, which is the next point.

## Intent is context, not a new model

Two changes moved the refund cases. The first was the manifest-scoped prompt. The second was an intent note attached to each refund request: the amount, the refund limit, and whether the agent holds `issue_refund`. Above the limit, the note says to call `issue_refund`, and not to open a ticket for a human instead.

The model still chooses the tool. The note only states what the request requires, which is information the model was previously left to infer. `refund-desk` went from five of eight to eight of eight. `support-agent` went from thirteen of sixteen to fifteen of sixteen. The approval path ran live for the first time. Approved refunds executed, rejected ones ended as rejected, and the wrong-approver case stayed pending.

I want to be precise about what this is. The amount is parsed from the request text by a rule in the scenario, so part of the decision now sits in code and not in the model. That is a design choice with a cost. It makes the agent more predictable on this class of request and less of a general reasoner. A platform team deciding how far to push this should treat it as a policy about where judgement lives, not as a tuning trick.

*[Exhibit 1: `docs/images/exhibit-1-progression.png`. Intent context moved refund-desk from 5 of 8 to 8 of 8.]*

*Exhibit 1. Cases passed per agent across five releases on gpt-oss-120b. Run 5 changes one expected action by owner decision. Assumptions: none.*

## The cost is in the review queue

The factory reports cost per successful outcome, defined as total cost divided by the cases that passed with no critical violation. A failed case adds cost and adds nothing to the denominator. The definition is in `cli/economics.py`, and it is the only place the figure is computed.

Token cost was $0.12 across all four agents. That is the number most teams would report, and it is almost irrelevant. Eleven of 36 cases needed a human, which is 31 percent. Human review at the assumed rate of five minutes an escalation, at $85 an hour, came to $77.92. Cost per successful outcome was $2.17, and nearly all of it is review time.

This is the constraint moving. Agent throughput was never the limit in these runs. The limit was review capacity. The management series calls this the Throughput Inversion: once agents make execution cheap, the bottleneck sits in judgement. Our data is one instance of it, not its origin, and four agents on one scenario cannot establish how often it happens in a real firm.

*[Exhibit 2: `docs/images/exhibit-2-economics.png`. Human review, not tokens, sets the cost per successful outcome.]*

*Exhibit 2. Tokens and escalations are measured. Review minutes, hourly rate, token price and remediation are assumptions.*

Two numbers in that table are assumptions, and the article's conclusion depends on one of them. The five minutes per review is a placeholder. A measured figure would change the headline directly. The same is true of what a wrong refund costs the business, which the factory cannot see at all. Until someone in operations supplies both, the cost-per-outcome figure is a framework for the decision, not the decision.

## A second model made the same decisions

The factory was run on a second model, `qwen/qwen3-32b`, with the same 36 cases. It passed the same four gates. On every case it chose the same tool and reached the same final status as gpt-oss-120b. It used about 7 percent more tokens.

Exhibit 3 shows the comparison. I would not generalise from it. Each model ran once, and two models agreeing on 36 cases is a sample. The result is still worth recording, because it is what a platform team needs to see before it trusts the gate across a change of model: the gate reported the same outcome, and the cost depended on the escalations, not on which model made them.

*[Exhibit 3: `docs/images/exhibit-3-models.png`. Two models made the same decision on all 36 cases.]*

*Exhibit 3. Same decision means same tool and same final status. One run per model. Token counts are from each API's usage field.*

## Golden paths are manifests, not documents

Platform teams have adopted golden paths: supported patterns that make the recommended approach the easy one. The factory's version is a manifest. Each of our four agents is a different golden path, distinguished by what it may do.

`case-notes` may only add notes. It is the lowest-authority pattern, and it passed every case with no approval needed. `ticket-triage` may open tickets and add notes, and it has no refund authority at all. `refund-desk` may issue refunds, but only under an approval rule. `support-agent` combines the three. Each path carries its own budget, approval rule and release threshold, and they share one generator, one harness and one gate.

The useful property is that a golden path is enforceable. A team that needs a pattern outside the set can write a new manifest, and the gate treats it the same way. What the factory should not do is publish guidance that teams interpret. Interpretation is where the first release's prompt defect came from.

## Who answers for the agent

Shared engineering does not create shared accountability. The manifest makes accountability explicit, and the release shows where it has to be exercised.

The platform team owns the generator, the templates, the gate and the cost assumptions. Its responsibility is that the supported path behaves as declared. It is not responsible for whether a given refund should be approved.

The domain owner owns the manifest's business content: the tool grants, the approval limit, and the expected action for every case. One case in this release expected `create_ticket` for a $150 refund. The owner decided that such a refund goes to a named approver, and the expectation changed. That decision moved a release from blocked to passing, and it was the owner's to make, not the platform team's.

Risk and governance set the thresholds and the review assumptions before a release. Those two inputs decide what "released" means and what an escalation costs. If they are set after the results are in, the gate becomes a way of explaining the results.

## Risks of industrialising too early

A factory that works on four agents can fail on forty. The failure would not be dramatic. Agents would be generated from templates that embed the same flaw, the gate would pass on cases written by the same people who wrote the template, and the release report would look orderly.

Errors in agents do not behave like errors in independent samples. One flawed policy or one bad data feed can repeat the same mistake across many runs. Sampling a slice of output to audit it therefore says less than it seems. Where a mistake cannot be undone, the sample is not enough, and the gate has to test every case that touches the consequential action.

There is a quieter risk in the factory's own evidence. We overwrote per-case results from earlier releases, so some claims about those runs can now be checked only at summary level. A factory that cannot reproduce its own history cannot defend its own release decisions. Archiving every run is cheap. Losing the record is expensive, and it is the first thing I would fix in a production factory.

## The factory as a learning system

The most valuable thing the factory did was change itself. The first release exposed the prompt defect. The fix was made in the generator, from the manifest, and the next release confirmed it. A defect found in one agent's evidence became a change inherited by every agent generated afterward.

This is a governed loop, not an autonomous one. A person reviews the change, the change is versioned, and the next release tests it. Nothing in the factory rewrites an agent's behaviour in production. What the factory provides is a route from evidence to engineering change that every later agent inherits.

I expect this loop to be the factory's real long-term return, more than the speed of generation. It converts the observations from one agent into improvements for all of them. It only works if the evidence is kept, the gate is honest, and someone acts on what the evidence says.

## What this does not show

- **One run per model.** Two models, one run each. That is a sample, not a measure of variance.
- **Authored cases.** The author wrote and reviewed all 36 cases. In a real release, the owners of the business outcome review them.
- **Assumed review cost.** The $77.92 is five minutes per escalation at an assumed rate.
- **No direct comparison in this release.** These runs used the harnessed path only. The ungoverned path was not re-measured here.
- **No handcrafted baseline.** The factory was not timed against a team building the same agents by hand. Any productivity claim is outside what was measured.
- **Simulated approvals.** Each approval was a case field, not a person. The approval logic was exercised, not a reviewer's workflow.
- **A partly lost record.** Per-case results from earlier releases were overwritten. Some earlier claims are summary-level only.

## Implications for platform teams

- **Generate agents from the manifest, and scope the prompt from the same grants.** The first release's defect came from building the prompt separately from the grants.
- **Archive every run's per-case results.** Without them, claims about earlier releases cannot be checked.
- **Build controls that can disagree with the model.** A boundary stops what an agent may not do. A guard checks whether it did what it should.
- **Ask which layer a release changed.** The Agentic OS from the management series names five layers: the Kernel for decision rights, Memory, the Scheduler, Execution and Observability. This release changed two, the Kernel through grants and approval and Observability through the release report. Scheduler and Memory are not built, and a platform team should know that before it claims an agentic capability.

## For risk and business owners

- **Set the gate thresholds and the review assumptions before the release.** Those two inputs decide what "released" means and what a refund that goes to review costs.
- **Own the expected action for each case, including approval holds.** A case expectation is a business decision, and it should be recorded as one.
- **Supply the cost of a wrong decision.** The factory can price a review. It cannot price the customer who was owed a refund and did not get one. Until that figure exists, the cost-per-outcome number is incomplete.

## Close

The factory is the product. What a platform team delivers is not a set of agents. It is a way to decide, repeatably and with evidence, which agents may act, and to see what the decision cost.

Run the same manifests on a third model. If the decisions differ, the gate should block the affected agent and name the case. Then measure a real review time. The cost per successful outcome will move, and that figure is the one to take to a budget meeting.

---

## Engineering Companion

- **Repository:** `agent-factory-scaffold`, commit `05d17e5`. Tag `v0.2.0` at publication.
- **Harness:** `agent-harness-core` 1.5.1, `git+https://github.com/ketan1602/agent-harness-core.git@v1.5.1`.
- **Manifests:** `manifests/ticket-triage.yaml`, `refund-desk.yaml`, `case-notes.yaml`, `support-agent.yaml`.
- **Cases:** `cases/*.json`. `support-agent.json` is the 16-case harness-foundations scenario.
- **Scenario code:** `templates/spine/scenario/` (`support.py`, `llm.py`, `intent.py`, `guard.py`). `config.py` is generated from the manifest.
- **Results:** `measurements/release.json` (gpt-oss-120b, committed release); `runs/qwen3-32b/release.json`; earlier summaries in `measurements/release-run*.json`.
- **Regenerate:** `agent-factory release` (live; needs `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` and the four cost assumptions). `agent-factory generate --manifest <file> --dry-run` needs no model.
- **Changeable without new model calls:** cost assumptions, gate thresholds, and the release report's economics.
- **Exhibits:** `docs/images/render_exhibits.py` renders the PNGs from values copied out of the release reports.
- **Tests:** `pytest tests/` (51 tests, no model calls); `ruff check .`.
- **Series references:** *The Pilot Trap*, *The Engine Room: Operating the Agentic Firm* and *The Firm Runs on Five Assumptions* (LinkedIn, Oct to Nov 2026). Cited for concepts only. No figure in this article comes from them.
