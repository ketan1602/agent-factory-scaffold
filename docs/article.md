# Agent Factories: Industrialising Agent Delivery

*Why enterprises need to move from building individual AI agents to engineering a repeatable system for delivering, governing and operating them.*

Harness Engineering series | ENG-10 | Enterprise Agentic AI

Companion repository: `agent-factory-scaffold`. Every measured figure below comes from `measurements/release.json` and the per-agent eval files in that repository.

---

## The next bottleneck is not building agents

Generating an agent took between 0.008 and 0.020 seconds in our release. Running its eval took 8 to 26 seconds. The release itself took longer, because the question was never whether the agent could be produced. The question was whether it could ship.

That is the pattern this article is about. The technology required to build an AI agent is now easy to reach: capable models, mature orchestration frameworks, standard tool interfaces, managed services. The engineering required to make an agent reliable, governable and operable is still hard. The distance between a convincing demonstration and an agent an enterprise can run unsupervised is where the work sits.

Earlier waves of enterprise technology showed the same shape. Creating a virtual machine was easy; provisioning standards, identity, network controls, deployment pipelines and cost management were the real work. Containers followed the same path. Deploying one was simple. Letting hundreds of teams deploy consistently required a platform.

Agents are harder, because their behaviour depends on more than code. An agent interprets a goal, chooses tools, and can take different paths for similar requests. Its behaviour depends on the model, the instructions, retrieved knowledge, tool responses and the context at runtime. A change to any of these can alter the agent without a code change.

So the platform question changes. It is no longer "how do we build an agent?" It is:

> How do we industrialise the delivery of agents across an enterprise, so that each one is generated from a shared contract, tested on realistic cases, gated on evidence and costed in the same way?

I call the system that answers this an **Agent Factory**. This article describes one, what it does in our repository, what it did in its first release, and what it does not yet do.

---

## 1. Why agent development becomes an industrialisation problem

A typical enterprise agent starts with a use case, a framework choice and a small team. The first demonstration is often impressive. The problems appear when the agent moves toward production.

Security wants to know which identity the agent uses and which actions it can take. Platform teams want resource limits, observability and lifecycle management. Business owners want evidence that the agent refuses what it should refuse. Operations wants to know how failures are detected and recovered.

Each team answers these questions for its own agent. One builds its own tracing, another its own approval step, a third its own evaluation harness. The result is familiar: local velocity creates enterprise-wide complexity. Five agents can tolerate that. Hundreds across customer operations, finance and internal services cannot. At that scale, maintaining different control implementations costs more than building the agents.

The fix is not to route every agent through one engineering team, which would create a new bottleneck. It is to centralise the engineering capabilities needed to deliver agents, and to keep business behaviour with the domain teams.

---

## 2. What the factory is, and what this repository implements

The working definition I use is:

> A platform engineering capability that standardises and automates the creation, validation, release and operation of enterprise agents through shared engineering contracts, common controls and measurable release gates.

The word "factory" can mislead. Agents are not identical products. A customer-support triage agent and a refund approver should differ in behaviour, grants and risk. What the factory standardises is how they are engineered, tested, gated and costed.

Figure 1 shows what the repository does with four agents. Each agent is described by a manifest. The factory generates the agent from that manifest, runs its eval against a live model, applies the manifest's release gate, and records cost.

| Stage | Implemented here | How |
|---|---|---|
| Define | Yes | Manifest: owner, tool grants, budget, approval rule, eval file, thresholds |
| Assemble | Yes | Generator renders the agent from the manifest and a vendored scenario |
| Validate | Yes | Live eval of each agent's cases through the harness |
| Certify | Yes, as a gate | Release blocked when pass rate or critical violations miss the manifest |
| Deploy | No | CI workflow runs the release; there is no deployment target |
| Learn | No | Evidence files exist; nothing turns them into tests or templates yet |

Figure 1. What the repository implements for each of the six stages. Two stages are not built.

---

## 3. The manifest is the contract

The most useful engineering decision in the repository is that the agent's operating boundaries live in a file, not in code scattered across the agent. The manifest for the ticket-triage agent is:

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

Every field here is enforced somewhere. The tool list becomes the harness's grant table, so a call to `issue_refund` by this agent is blocked by the runtime, not by a sentence in the prompt. The budget becomes the harness's limit. The approval limit and approvers feed the orchestration rule. The thresholds feed the release gate.

The manifest deliberately omits fields that nothing enforces. An early draft included identity mode, memory configuration and a deny list. Those would have been documentation, not contract, so they were removed until the runtime can act on them. A manifest that claims more than the platform enforces is worse than a shorter one.

The manifest also makes ownership explicit: `owner: customer-operations`. The platform team owns the generator and the gate. The owner of the business outcome owns the manifest and its cases.

---

## 4. Multiple agents, one factory

A single agent can show that a template works. It cannot show that a factory works. The repository therefore generates four agents from four manifests:

| Agent | Tool grants | Approval rule | Cases |
|---|---|---|---|
| support-agent | create_ticket, add_note, issue_refund | refunds above 100 need approval | 16 (the harness-foundations support scenario) |
| ticket-triage | create_ticket, add_note | none (no refund tool) | 7 (new) |
| refund-desk | issue_refund, add_note | refunds above 100 need approval | 8 (new) |
| case-notes | add_note only | none | 5 (new) |

The 16 support-agent cases come from the harness-foundations article unchanged. The 20 new cases were written for this release. They reuse the same violation categories, so the same checks apply. They have not yet been reviewed by the domain owners. That review is a prerequisite for treating the release decisions as final, and it is the first item in the limitations at the end.

The four agents share one generator, one scenario, one harness version and one set of compliance checks. They differ only in manifest and cases. That is the factory claim in its simplest form: the variation between agents is the declared contract, not the plumbing.

---

## 5. The first release blocked three of four agents, and that was useful

We ran the first release on all four agents. Three were blocked, and the blocks were not what the design predicted.

| Agent | Run 1 | Run 2 (committed) | Gate (run 2) |
|---|---|---|---|
| ticket-triage | 7/7 | 7/7 | RELEASED |
| case-notes | 3/5 | 5/5 | RELEASED |
| refund-desk | 5/8 | 5/8 | BLOCKED |
| support-agent | 13/16 | 13/16 | BLOCKED |

The run 1 failures in `case-notes` were not model errors. The model chose `create_ticket` for two cases that asked for a note. The agent isn't granted `create_ticket`, so the harness blocked both runs. The cause was in the factory. The spine's prompt listed every tool the scenario knows about, not the tools the agent was granted. The model was offered an action the runtime would refuse.

The fix was to build the prompt's tool list from the manifest. That is a change to the vendored scenario, so it is documented in the repository, not hidden. After the fix, `case-notes` passed 5 of 5 and was released. The harness had been correct all along; the factory had been generating prompts that disagreed with the contract.

This is the argument for generating from a contract. A template that copies code cannot know which tools an agent should see. A generator that reads the manifest can. The release evidence exposed the disagreement, and the generator now enforces it.

The first run also showed something the design had not predicted: the failures were in the factory's generated behaviour, not in the business logic. A factory that only tests the agent's business logic would have missed it.

---

## 6. What the gates caught, and what changed the result

The manifest sets `minimumPassRate: 0.98`. With 5 to 16 cases per agent, every case must pass. We kept the threshold as written.

The first guarded run blocked `refund-desk` at 5 of 8 and `support-agent` at 13 of 16. The misses were the approval-path cases. For each, the model chose `add_note` or `create_ticket` for a refund request and completed the run, so no approval was requested. The guard escalated those requests, but the eval still failed them: a refund that becomes a note is still wrong.

We then changed one thing. The model now receives an intent note computed from the request: the refund amount, the refund limit, and whether the agent holds `issue_refund`. Above the limit, the note says to call `issue_refund`, and not to open a ticket. The model still chooses the tool. The note only states what the request requires.

Result: `refund-desk` went from 5 of 8 to 8 of 8 and was released. `support-agent` went from 13 of 16 to 15 of 16 and is still blocked. The approval path was exercised live for the first time: approved refunds executed, rejected ones ended as rejected, and the wrong-approver case stayed pending.

The one remaining `support-agent` miss is `policy_lookup`, a $150 refund request whose case expects `create_ticket`. With the intent note, the model chooses `issue_refund`, which routes to approval. The case expectation may be out of date. We did not change it, because changing it to pass would hide the question. The case owner needs to decide.

Two honest limits apply. The intent note is a change to the scenario, so the article discloses it. And it is part of the decision computed from request text, so the model's job is smaller than before. All of these results are one model, gpt-oss-120b.

## 7. The harness is the runtime foundation

In ENG-05, I proposed a harness with Runtime, Control and Assurance planes. The factory depends on that model: it provisions every agent into the same harness, and the harness enforces the manifest during execution.

The separation matters. The eval shows that an agent behaved correctly on a set of cases. It cannot show that every future execution will. Runtime enforcement does not depend on the model choosing correctly. A tool outside the grant is blocked whatever the model decides.

In this release, the harness held the boundary in every case. Across both runs and all 36 cases, there were zero critical violations: no tool outside the grant was executed, no budget was exceeded without termination, no suspended agent acted, and no secret field was passed through. The refund limit held too: the approval rule did not allow a refund above the limit to execute without a decision.

What the harness does not do is judge intent. A note in place of a refund is allowed by the grant, so the runtime lets it complete. Closing that gap needed a second mechanism, the completion guard in section 6, and the online monitor that checks the guard runs.

We did not run the direct, ungoverned path in this release. The earlier article reports a direct-versus-harnessed comparison on the spine scenario. I have not re-measured it in this repository, so this article does not repeat its figures.

---

## 8. The economics: the guard moved the cost to people

Before the guard, the release reported $0.004 per successful outcome. That number was not a low cost. It counted tokens and ignored every refund the agent failed to complete. The guard turns those failures into escalations, and an escalation has a cost.

Token cost is measured. Each run reports the tokens from the model API's usage field. Review and remediation are assumptions, applied to events the release counts. The release refuses to run without all four assumptions set, so no figure comes from a default. The values come from the TCO repository's labelled assumptions: $0.005 per thousand tokens, 5 minutes of human review at $85 an hour, and $970 of remediation per violation.

| Agent | Tokens | Token cost | Escalations | Review cost | Successful outcomes | Cost per successful outcome |
|---|---|---|---|---|---|---|
| ticket-triage | 2,521 | $0.0126 | 1 | $7.08 | 7 | $1.01 |
| case-notes | 1,681 | $0.0084 | 0 | $0.00 | 5 | $0.00 |
| refund-desk | 8,402 | $0.0420 | 5 | $35.42 | 8 | $4.43 |
| support-agent | 12,196 | $0.0610 | 5 | $35.42 | 15 | $2.37 |
| **All four** | **24,800** | **$0.1240** | **11** | **$77.92** | **35** | **$2.23** |

Table 2. Run 4, with the guard and the intent note. Escalations are measured; the $7.08 per escalation is an assumption.

Two points follow. First, the escalation count is measured, but its cost is not: the $7.08 per escalation is five minutes at an assumed $85 an hour. The $77.92 is therefore mostly a function of an assumption, and a different review time changes the figure directly. Second, the trade is now visible. A failed refund in production is invisible and costs the customer. A guarded refund costs a human reviewer's time, which the factory can price. The repository cannot say whether that trade is worth it, because the real review time and the real refund rate are not known. It can show that the trade exists and what it costs at the assumed rates.

Remediation is zero. No violation occurred in any run, so the remediation assumption did not enter the figure.

## 9. The operating model matters as much as the architecture

Shared engineering does not create shared accountability. The repository shows the division I would use in an enterprise.

The platform team owns the generator, the templates, the gate, the validator, the economics and the CI workflow. Its responsibility is to make the supported path reliable. It does not own the business behaviour of any agent.

The domain owners own the manifest and the cases. The manifests name `customer-operations` and `customer-platform` as owners. The cases are where business judgement lives. In this repository, the cases were written by the factory author, not by the owners, which is why the release decisions should be treated as provisional until review.

Security and risk define the policies the manifest expresses: tool grants, approval limits and approvers. The release gate enforces thresholds that the risk owner sets, rather than the platform team choosing them.

Each manifest has an owner, and that owner is accountable for the outcome the agent delivers. Platform support does not transfer that accountability.

---

## 10. What the factory does not do yet

The earlier draft of this article proposed a six-stage pipeline and a maturity roadmap. The repository covers four of the six stages in part. Here is what is built and what is not.

**Built:** a manifest contract the harness enforces; a generator that renders from it; a live eval of each agent's cases; a completion guard that escalates refund requests not actioned; a release gate applied from the manifest; cost per successful outcome with labelled assumptions; an online monitor that checks the guard over recorded runs; compliance checks; and a CI workflow with offline tests, dry-run generation and a manual live release.

**Partly built:** online monitoring. It replays recorded eval runs. The approval path now runs live in the eval, but not on production traffic. It does not watch live traffic, so it can show the guard works on the runs we have, not on production.

**Not built:** deployment and rollback, a registry, live production monitoring, the learning loop from production evidence back into cases and templates, identity and memory in the manifest, and the review of the new cases by domain owners.

**Not yet exercised live:** repeat runs across several models, a real review time for the escalation cost, and any comparison against a handcrafted baseline. The repository deliberately has no baseline figure. The earlier draft's "three days" and "35 decisions" were not measured, and they are not in the release.

Three steps would close the most important gaps, in this order:

1. Have the domain owners review the 20 new cases, and correct any expectation they disagree with.
2. Measure the real review time for escalations, and replace the assumed five minutes. This is the figure that drives the cost result.
3. Connect the release report and the guard to a live queue, so an escalation reaches a reviewer and a blocked gate prevents deployment rather than only failing a job.

---

## 11. The risks of industrialising too early

There is a serious counterargument. Agent technology is changing quickly. Standardising too early can freeze decisions that the industry has not settled, such as the framework, the model or the memory architecture.

The repository tries to respond by standardising the contract rather than the implementation. The manifest declares tools, budget, approval and thresholds. It does not declare the framework, the planning method or the memory design. The release gate works on evidence, so it does not depend on which framework produced the decision. This is also why the repository does not use LangGraph: the spine's agent is a single decision run through the harness, and forcing a graph would change the implementation without changing the contract.

A second risk is that a passing eval is taken as proof of correctness. The gate in this repository is only as good as its cases. Twenty new cases, unreviewed, cannot establish that the agents are right. They establish that the agents match the cases the factory author wrote. The factory should make that boundary visible, and it does so in the README and the report.

A third risk is that industrialisation makes it easy to create more agents than anyone can manage. The factory should support retirement and ownership transfer as first-class capabilities. The repository has no retirement path yet. That is a gap, and it grows with each agent added.

A good factory should make it easier to decline an unnecessary agent, not only to create another one.

---

## 12. From release evidence to engineering change

The most useful thing the repository did was change its own generator. The first release showed that the factory was offering agents actions their contracts forbade. The fix was made in the generator, from the manifest, and the second release confirmed it.

That is a small learning loop, and it is the pattern I would scale. Production or release evidence identifies a recurring failure. The failure becomes a change to a template, a case, a manifest or a policy. The next release tests whether the change worked. The change is traceable because the evidence was kept: `measurements/release-run1-unscoped-prompt.json` is still in the repository, next to the run that followed.

This is different from agents that modify themselves. The loop here is governed. A human changes the generator, the change is reviewed and versioned, and the next release tests it. The benefit compounds across agents: a fix to the prompt builder applies to every agent generated from it.

I expect that loop to be the factory's real long-term value. It converts observations from individual agents into engineering that all agents inherit. It requires evidence to be kept, the gate to be honest, and someone to act on what the evidence says.

---

## Conclusion: the factory is the product

Building an individual agent will keep getting easier. Models will improve, frameworks will mature, and tooling will automate more of the implementation. Those advances reduce the cost of producing an agent. They do not remove the enterprise work of deciding whether an agent may act, proving that it behaves, and keeping the evidence.

In our release, generating four agents took under a tenth of a second each, and running their evals took between 8 and 26 seconds. Three of the four agents were released by the gate. The one blocked agent fails a single case that may carry a stale expectation, and that question belongs to its owner. The first release exposed a defect in the factory's own prompt, which a later release corrected. The guard escalated the refund requests that would otherwise have completed silently, and the intent note gave the model what it needed to choose the refund tool.

That is the argument for an Agent Factory. Its value is not that it produces agents quickly. Its value is that it makes the decision to release an agent evidence-based, repeatable and visible, and that it turns each failure into a change every future agent inherits.

The competitive advantage will not come from how many agents an enterprise can build. It will come from how reliably it can deliver, govern, operate and improve them.

---

*This article builds on the Beyond the Model series, the Enterprise Agentic Harness Model (ENG-05), the Agent Control Plane (ENG-08) and Harness Engineering (ENG-09). The repository is `agent-factory-scaffold`; the harness is `agent-harness-core` 1.5.1.*
