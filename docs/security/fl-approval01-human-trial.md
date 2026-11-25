# FL-APPROVAL-01 human trial preparation

Status: **PREPARED_PENDING_HUMAN_ADJUDICATION**. Actual human observations: **0**.
`activation_allowed=false` in every preparation and pilot-analysis result.
The live dispatcher and authorization policy are unchanged.

## Components and acceptance

- [Case bank](../../01_KISH_ENGINE/babylon60/cortex/approval_trial_cases.py):
  200 draft Spanish cases, 50 policy families, 100 permitted and 100 forbidden.
  Generated references are proposals requiring two independent human reviews.
- [Pilot preparation](../../01_KISH_ENGINE/babylon60/cortex/approval_human_trial.py):
  private allocation, adjudication/enrollment templates, readiness checks and
  descriptive analysis by reviewer. No recruitment, presentation UI or signature
  provisioning is performed by the generator.
- [Existing audit protocol](fl-approval01-independent-judgment.md): cryptographic
  review history and optional authorization adapter; separate from this study.

Acceptance checks cover balance, case uniqueness, policy boundary values,
unknown operations, concealed answer labels and seed, matched allocation,
adjudicator independence, malformed/duplicate imports and non-activation.
All software checks and synthetic datasets are separate from human evidence.

## Feasibility pilot

Allocate 12 reviewers to six A/B pairs, three pairs in each of two experience
strata. Each person sees 24 distinct families: six cases for each combination
of policy truth and recommendation. The same book and order are used by both
members of a pair. A sees recommendation and evidence together; B records a
first decision before recommendation exposure. No crossover is used.

Enroll and obtain consent before revealing assignment. Use a fixed enrollment
order within each stratum; a separate allocation custodian assigns the next
slot. Do not move participants between slots after inspecting their condition.
Complete training before revealing assignment. Adjudicators must not also be
trial participants. No trial decision executes a requested effect.

Two specialists independently review every case without the generated key or
each other's answers. They identify the correct decision and decisive evidence.
Disagreement requires revision and fresh independent adjudication, rather than
forcing agreement with the machine. Freeze and hash cases/recommendations before
participant use. A local digest is not an external preregistration.

Proposed progression thresholds, to freeze before data collection: at least
11 completed reviewers, at least 95% final responses out of 288 planned decisions,
zero B exposures without a sealed first decision, at most 5% ambiguous case
presentations, and a target median session of at most 60 minutes. Failure leads
to revision and a new feasibility assessment. Passing does not demonstrate efficacy.

Paper sessions require original signed/sealed forms and separate recommendation
cards. Human-verified paper references are declarations in the analysis export,
not cryptographic signatures. A digital presenter must separately integrate and
test the signed precommit barrier before it is used with participants.

## Commands

Start with the read-only Spanish status report. It reads the current inputs
instead of trusting a previously saved readiness report, separates declared
human observations from simulations, and always refuses activation.

```sh
uv run --locked python -m babylon60.cortex.approval_trial_status --kit /tmp/fl-approval01-human
```

```sh
uv run --locked python -m babylon60.cortex.approval_human_trial prepare --out /tmp/fl-approval01-human
uv run --locked python -m babylon60.cortex.approval_human_trial merge-adjudications --pilot /tmp/fl-approval01-human/coordinator/pilot_private.json --first /tmp/validator-1.json --second /tmp/validator-2.json --out /tmp/adjudications.json
uv run --locked python -m babylon60.cortex.approval_human_trial readiness --pilot /tmp/fl-approval01-human/coordinator/pilot_private.json --adjudications /tmp/adjudications.json --enrollment /tmp/enrollment.json --out /tmp/readiness.json
uv run --locked python -m babylon60.cortex.approval_human_trial analyze --pilot /tmp/fl-approval01-human/coordinator/pilot_private.json --observations /tmp/observations.json --source human --out /tmp/pilot-report.json
```

Use private randomness by default. `--seed` is for private reproduction; never
include it, assignments, answers or future recommendations in participant files.
The coordinator holds `0600` key files in a `0700` directory. Readiness validates
imported declarations; it does not authenticate a human, inspect consent forms
or provide hardware attestation. Preserve the original evidence for independent
audit. An empty observation list is not a completed study.

Validation checks the actual 200-case answer correspondence, unique reviewer
slots and roster membership, six matched A/B pairs, experience strata and
balanced 24-case books. Recomputing an unkeyed digest does not bypass these
structural checks. Explicit observation origins must agree with the requested
analysis origin. Commitment references are normalized before duplicate checks.
These checks detect malformed declarations; they do not authenticate people.

## Confirmatory study

Use new participants and keep the feasibility pilot out of the confirmatory
dataset. Proposed 48-case books contain 12 primary cases (forbidden request,
recommendation to approve), 24 legitimate cases and 12 other forbidden cases.
Each reviewer sees at most one variant of any family. Treat the case bank as
fixed and limit generalization to those cases and standardized recommendations.

Both coprimary criteria must pass:

1. Upper one-sided 97.5% confidence bound of primary error risk ratio B/A < 0.70.
2. Lower one-sided 97.5% confidence bound of legitimate approval difference
   B minus A > -0.05.

A point estimate of 30% reduction is insufficient. Zero baseline risk or invalid
inference is not evaluable. Use reviewer-level clustering, paired books and
experience strata in the final method. Preserve assignment in analysis and
report missing outcomes and protocol deviations. Predefine conservative missing
outcome sensitivities. Do not stop or enlarge the sample after inspecting benefit.

Approximate planning under true RR=0.50, ICC=0.05, legitimate approval=0.90 and
90% marginal power per coprimary criterion gives 192, 312 or 672 completed
reviewers when baseline error is 30%, 20% or 10%, respectively. These are
delta/Wald planning examples, not validated sample sizes; finalize the method,
sample, uncertainty and simulations with statistical review before recruitment.
The preparer contains no validated confirmatory inference engine.

The [CONSORT feasibility extension](https://doi.org/10.1136/bmj.i5239) distinguishes
feasibility from efficacy. The [cluster extension](https://doi.org/10.1136/bmj.e5661)
addresses correlated observations. These methodological references do not make
CORTEX a clinical study. Human confirmation, independent runtime checks and a
separate deployment decision remain necessary before any real-flow activation.
