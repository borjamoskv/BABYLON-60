---
title: "Ten foundational questions for engineering AI agents"
description: "From CLI, IDE and MCP to effective authorization, evidence-bearing memory and reproducible execution."
date: "2026-10-31"
author: "Borja Fernández Angulo"
language: "en"
slug: "/en/blog/ten-foundational-questions-ai-agents/"
category: "Agent architecture"
tags: ["AI agents", "CLI", "IDE", "MCP", "authority", "security", "evidence"]
status: "editorial-ready-not-deployed"
translation_of: "/blog/10-preguntas-fundamentales-agentes-ia/"
---

# Ten foundational questions for engineering AI agents

**An interface is not an authority boundary. A protocol is not a permission. The ability to invoke a tool is not authorization to use it.**

“Should I work with agents in a CLI, an IDE or through MCP?” looks like a question about developer preferences. In fact, it exposes a deeper design problem: where does an agent acquire the ability to affect the world, and who controls those effects?

CLI and IDE describe interaction environments. Model Context Protocol (MCP) describes an interoperability mechanism. They can coexist. None, by itself, establishes effective authorization.

Once an agent can edit files, execute programs or change external services, response quality is no longer a sufficient metric. We must examine the legitimacy, containment and traceability of effects.

## Three surfaces, four distinct planes

| Element | Main role | What it does not establish |
| --- | --- | --- |
| CLI | Command-driven interaction and execution | That OS privileges are restricted or commands are authorized |
| IDE | Contextual editing, debugging and review | That changes are correct or every action is mediated |
| MCP | Standardized exchanges between hosts, clients and servers exposing tools, resources and prompts | That a discovered capability is authorized for every resource |

MCP distinguishes hosts, clients and servers. The host coordinates clients, while servers provide focused capabilities. The 2026-07-28 protocol revision introduced a stateless core with version and capabilities carried per request. Protocol interoperability and authorization at the resource boundary remain different problems.

A reliable design separates **interaction**, **runtime**, **integration** and **authority**. Changing an interface should not silently change the effective permissions of the agent.

## 1. What makes a model an agent?

Producing an answer is not the same as acting. Agentic behavior involves maintaining objectives, selecting actions, observing outcomes and incorporating observations into later decisions.

**Observe → decide → act → verify → observe again.**

Autonomy is not binary. A tool call alone does not prove persistent goals, planning quality or legitimate authority. An evaluation must specify what the system may decide independently and which effects require further approval.

## 2. What makes a goal verifiable?

“Improve this repository” lacks a success criterion. Improvement might mean lower latency, fewer dependencies, stronger boundaries or fewer regressions. These goals may conflict.

A verifiable assignment names the target artifacts, permitted operations, resource budget, failure conditions and acceptance tests. The model may propose the change; it should not be the only judge of the result.

Passing a test establishes evidence about the tested conditions, not universal correctness.

## 3. Where does an agent run, and how does it reach the outside world?

The CLI/IDE/MCP question becomes four explicit questions:

- **Interaction:** who instructs the agent and reviews the output?
- **Runtime:** which process performs the operation, under which credentials and isolation controls?
- **Integration:** which mechanism discovers and invokes tools?
- **Authority:** which principal authorizes this operation on this resource, and for how long?

The same effect might be attempted through a shell, an IDE extension or an MCP tool. If all three paths reach the same protected resource, equivalent controls are needed at that boundary.

Publishing a tool in MCP does not grant the agent unrestricted permission to use it.

## 4. Who is accountable for a delegated action?

An agentic workflow may involve a user, planner, executor, subagent, tool server and remote service. “The AI did it” does not identify an accountable principal.

A useful trace connects each effect to a requester, a delegation chain, the authorized scope and the observed outcome. An agent identifier without enforceable delegated privileges is not sufficient authorization evidence.

Responsibility does not vanish as an instruction crosses layers.

## 5. What should the system remember and forget?

A larger context window is not an operational memory. An agent must preserve sources, versions, validity periods and uncertainty.

An old hypothesis does not become true merely because it is retrieved repeatedly. A cryptographic digest can establish a byte-level relationship under stated assumptions; it does not validate meaning or independently establish publisher identity.

An auditable memory must distinguish **observations, inferences, decisions and evidence**.

## 6. What counts as a proof?

There are several separate evidence levels:

1. **Formal model:** a property follows from specified definitions and assumptions.
2. **Implementation:** code and tests support a claim about the actual executor.
3. **Isolation:** operating-system controls prevent alternative access paths.
4. **Experimentation:** an adversarial campaign observes bounded behavior in a particular environment.

None automatically certifies the next. Compiling Lean does not certify an entire binary; a valid signature does not establish truth; killing a process does not simulate a power failure.

Evidence is useful only when its scope is explicit.

## 7. Who authorizes an effect?

This may be the central architectural question.

A model can propose an operation. Its own proposal must not be treated as a credential. Authorization must bind identity, operation, resource, conditions, validity and consumption state.

A broker can mediate sensitive actions. Yet the broker is not a complete boundary if the agent still has a privileged shell, inherited file descriptors or an alternative API capable of bypassing it.

**A security policy must survive an incorrect model decision.**

## 8. Can execution be reconstructed without repeating its damage?

A chat transcript is not a reproducible execution record. We need versions, inputs, decisions, tool calls, authorizations and observed outcomes.

More importantly, **trace replay** must be separated from **reapplying external effects**. Investigating a payment, publication or deletion must not accidentally repeat it.

If a process crashes after an effect but before its receipt is persisted, the outcome can be unknown. A safe protocol represents that ambiguity and reconciles state before retrying non-idempotent work.

## 9. When do two hundred agents outperform one?

Parallelism improves exploration of separable work. It can also multiply costs, contention, conflicts and correlated mistakes.

Two hundred agents relying on one false source are not two hundred independent verifiers. Coordination requires task partitioning, budgets, concurrency controls, independent review and conflict handling.

A better metric than worker count is **useful, verifiable work per unit of time, cost and risk**.

## 10. How can capabilities evolve without silently increasing authority?

Models, plugins and tools change. Adding an MCP server or updating an IDE extension should not widen permissions by accident.

That requires model-independent invariants: scoped resources, least privilege, mandatory mediation, expiration, accountable effects and defined failure behavior.

A more capable model may design better plans. It does not thereby gain a broader mandate.

## A falsifiable boundary experiment

A user authorizes bounded writes to **/project/report.md** for a limited period. The agent can reach tools from a CLI, an IDE and MCP.

From each route, the test attempts to:

1. Write to an unauthorized neighboring file.
2. Redirect an operation using a symlink or inherited descriptor.
3. Replay a consumed or expired authorization.
4. Substitute the resource after approval.
5. Retry a non-idempotent effect following an ambiguous interruption.

The observable requirement is **no effect outside the authorized scope**, within the environment and paths actually tested. A universal claim requires coverage of all relevant access paths, not just the broker's preferred API.

A policy specification is not proof of enforcement.

## BABYLON-60 and the boundary between intent and effect

BABYLON-60 investigates an authorization and mediated-execution boundary summarized as **Propose → Check → Mediate → Observe**.

Its public implementation describes Rust/Python user-space software, not an operating-system kernel. Comprehensive mediation requires confining the agent so it cannot reach protected resources or the ledger through other paths. The project separates formal, implementation, isolation and experimental evidence and declares their scope.

This is a design and validation program, **not a claim of universal security certification**.

The decisive test is not whether the broker rejects an invalid request. It is whether the environment prevents the agent from achieving the same unauthorized effect by another route.

## Conclusion

CLI, IDE and MCP are choices about interaction and interoperability. Agent engineering begins when they operate within enforceable and inspectable limits of authority.

The question connecting all ten is:

**How do we move from systems that produce plausible answers to systems whose effects can be authorized, observed, reconstructed and challenged?**

A smarter model may produce a better plan. Intelligence alone must not confer permission.

**More capability. The same authority.**

---

### Related BABYLON-60 technical notes

Browse the [engineering notes in Spanish](https://babylon60.com/blog/) and the [English technical archive](https://babylon60.com/en/blog/). Particularly relevant articles address authorization, evidence-bearing memory, Lean proofs, nonce replay, process isolation and the Verification Mirror.

### Technical sources

- [MCP architecture specification, 2026-07-28](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/architecture/index.mdx)
- [MCP 2026-07-28 release notes](https://blog.modelcontextprotocol.io/posts/2026-07-28/)
- [BABYLON-60, public source repository](https://github.com/borjamoskv/BABYLON-60)
- [BABYLON-60, evidence and limitations](https://babylon60.com/evidencia/)

*Technical essay and editorial proposal. Specific security properties require independent validation within the stated scope of each implementation.*
