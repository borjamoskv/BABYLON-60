# FL-APPROVAL-01: Independent Judgment Integrity

Status: **IMPLEMENTED / SOFTWARE_VERIFIED / HUMAN_TRIAL_NOT_RUN**.
The adapter is opt-in and is not enabled in the live MCP dispatcher.

## Scope and acceptance

This experiment adds a signed record of a reviewer's decision before exposure
to an agent recommendation. It preserves the distinction between review,
effective policy and authorization to execute an effect.

Implementation: [approval_integrity.py](../../01_KISH_ENGINE/babylon60/cortex/approval_integrity.py).
Trial preparation and descriptive analysis:
[approval_experiment.py](../../01_KISH_ENGINE/babylon60/cortex/approval_experiment.py).
Executable isolated campaign:
[fl_approval01_simulation.py](../../examples/fl_approval01_simulation.py).
No dependency or lockfile change is required.

Acceptance covers signed request/evidence binding, identity pinning, A/B order,
expiry, corruption, denial, replay after restart or abrupt termination,
concurrent consumption and separately observed effects. Tests use software keys
and temporary files; they do not attest Secure Enclave, human identity or
psychological independence.

## Local review protocol

`ApprovalJournal(path, reviewer_keys)` opens a dedicated SQLite WAL database
with `synchronous=FULL`. A trusted review service provisions the pinned Ed25519
public keys; the proposing agent must not own the reviewer signing key or have
raw access to the database. No default authority or generated production key
is provided.

1. `create_review` binds task ID, reviewer, complete task/evidence digests,
   condition, effective policy version, creation tick and expiry tick.
2. In B, `precommit_message` returns the exact bytes to sign externally.
   `record_precommit` verifies the detached signature and durably appends it.
3. `record_recommendation` records the recommendation and rationale digest.
   B rejects this operation before precommit. A starts at this step.
4. `final_message` / `record_final` bind the final decision and its evidence
   summary to the precommit and recommendation. A change of mind is permitted.
5. `verify` checks the complete history and bindings without consuming it.
   It is diagnostic and cannot authorize an effect.
6. The optional `execute_once` adapter checks review and effective policy,
   durably consumes the review, then delegates to the existing
   `VerificationGate.execute_once`. A failed dispatch or effect consumes the
   review; retry requires a new review and any authorization required by the gate.

Decisions use `APPROVE` / `REJECT`. Signatures cover a domain-separated canonical
local JSON envelope and a hash chain. New digests use BLAKE3, following the
repository contract, rather than the SHA3 field in the original proposal.
This is local audit storage, not a replacement for the existing on-wire
authorization protocol or hardware-backed approval of critical operations.

The signed timestamp is a monotonic logical tick supplied by the trusted service.
Ticks must advance at each event; expiry is exclusive. Wall-clock `recorded_at`
is unsigned audit metadata and does not enter causal hashes. Tick expiry does
not establish real-time expiration if the trusted clock is stalled or rewound.
The existing authorization gate retains its separate real-time expiry checks.

The caller must hold its policy/evidence lock through review validation,
authorization and effect. The adapter snapshots the task before checking policy
and forwards that snapshot to the gate. The effect must operate on that same
request and locked resources. No OS confinement is established by this API.

SQLite triggers reject ordinary updates/deletes. Signatures detect changes to
signed history, including recomputed unkeyed hashes. Protection against a
database owner restoring an old snapshot, truncating the entire tail, or
deleting a consumption record requires an external trusted checkpoint and
storage access control. This experiment does not implement that checkpoint.

The order proves what the service recorded. It cannot prove that a reviewer
never saw a recommendation through another channel, or that the person
independently considered the evidence. A trusted presenter must withhold B's
recommendation until `record_precommit` has succeeded.

## Isolated 200-case campaign

From the repository root, choose a new output directory:

```sh
uv run --locked python examples/fl_approval01_simulation.py --out /tmp/fl-approval01-smoke
```

The runner performs eight warmup reviews, then 200 measured cases. It uses the
real journal, explicit software test signatures, an isolated simulated
authorization gate and a separate effect witness. It checks policy independently
of the answer key. It exports observations and a report marked simulation-only.
Synthetic final decisions follow the agent in both conditions, so the simulation
does not encode an assumed psychological benefit of precommit.

## Preparation and analysis of a future human trial

The expanded human preparation is documented in
[the human trial protocol](fl-approval01-human-trial.md). It provides a diverse
draft bank, matched reviewer allocation and human-adjudication checks. The older
three-template fixture below remains a software simulation tool.

```sh
uv run --locked python -m babylon60.cortex.approval_experiment prepare --out /tmp/fl-approval01-plan
uv run --locked python -m babylon60.cortex.approval_experiment analyze --plan /tmp/fl-approval01-plan/participant_plan.json --key /tmp/fl-approval01-plan/coordinator_key.json --observations /tmp/observations.json --source human --out /tmp/fl-approval01-human-report.json
```

Preparation balances condition × permitted/forbidden × agent recommendation,
25 cases per cell. Human preparation uses a private random seed; explicit seeds
are available for reproducible software fixtures. Keep the coordinator key,
recommendations and seed away from participants. The helper
`recommendation_packet` is coordinator-only and does not itself enforce exposure
order; the trusted presenter and journal must do so.

The supplied scenarios are functional fixtures from three templates, with
repeated combinations. They are insufficient as a diverse human study. Before
recruitment, expand and validate the cases, preregister reviewer allocation,
learning/contamination controls, clustered analysis, power, uncertainty and
stopping rules. No participants were recruited or contacted for this work.

Each imported observation includes `case_id`, `reviewer_id`, `final_decision`
and `authorization_latency_ms`; B also requires `initial_decision`. Independent
effect observations may supply `effect_observed` and `valid_authorization`.
An imported flag is a declaration, not a verified signature or hardware witness.

All rates expose numerators and denominators. Empty denominators are `null`.
Unobserved effects are unknown, not zero. The flip metric describes a switch
toward the agent among initial disagreements; it does not establish causality.
A normally has no independent baseline and its flip rate is not identifiable.
Latency p95 uses nearest rank in milliseconds and includes review software work;
it is not a measurement of human judgment or native broker latency.

The descriptive primary comparison is the incorrect-approval rate among
forbidden cases with an agent recommendation to approve. The proposed target is
at least 30% relative reduction in B, with legitimate approval no more than five
percentage points below A. A zero error baseline makes relative reduction
undefined. An incomplete dataset does not evaluate the target. The analyzer
never sets `hypothesis_confirmed=true`; inference requires the human protocol.

## Source and evidence boundary

[Anthropic, 27 October 2026](https://www.anthropic.com/research/agents-judgment-calls)
studied defensible analytical choices, not policy violations or erroneous
authorizations. Fifty participants used the agent; the 77%/15% survey figures
use 48 respondents. The 60%/6% switching comparison uses 38 observed prior
decisions and is not itself a causal estimate. The study motivates testing;
it does not validate this intervention or its 30%/five-point targets.

The software tests establish properties only under their fixtures and trusted
service assumptions. A prohibited effect observed despite denial falsifies
containment for that case; a zero count does not establish complete mediation
of all runtime entry points. Human efficacy remains **NOT_TESTED**.
