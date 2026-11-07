# FL-PKG-01: installation effects after package admission

This isolated experiment tests whether approved npm packages can produce effects
outside the install policy. Package identity and admission do not grant authority
to read a canary, modify a protected or unlisted resource, or reach a test sink.

The executable is `scripts/c5_quality_gates/fl_pkg_01.py`. It generates 300
deterministic artifacts: 100 benign, 100 flagged/suspicious, and 100 adversarial
artifacts with admissible metadata. These are synthetic packages, not downloaded
malware. No production files, real credentials, or external destinations are
targeted. Each trial has separate workspace, home, cache, and fixture directories.

| Policy | Actual mechanism |
| --- | --- |
| A | Real `npm ci`, fixed lockfile and SHA-512 SRI integrity |
| B | A plus a loopback test registry rejecting flagged metadata and downloads |
| C | B plus offline execution with default-deny OS capabilities and exact broker publication permits |
| C_CURRENT (optional) | B plus the original `MacOsAgentConfinement`, retained as a negative control |

Policy C is implemented in `babylon60.install_policy`. The trusted fetch phase
checks admission and npm SRI/BLAKE3 identity before staging a local archive. npm
executes with `--offline`, an empty user configuration, a scrubbed environment,
and a real `(deny default)` Seatbelt policy. Explicit runtime capabilities allow
Node/npm libraries, metadata, process creation and writes inside private staging.
Network, broker state, publication directories, user secrets and UI/IPC receive
no installer grants. Descendants inherit OS enforcement. Runtime aliases are
resolved for the installed executable/libraries; workspace roots preserve their
logical hierarchy and are opened component by component with `O_NOFOLLOW`.

The trusted broker snapshots only explicitly granted output roots. Each file
permit fixes its path, BLAKE3 content digest and safe mode; publication uses these
immutable bytes rather than reopening mutable installer output. Artifact identity,
directory inode identity, monotonic logical clock, authority epoch and expiry are
checked before effects. Revocation and publication use the same authority lock,
so their order is linearizable. Expiry is rechecked while copying. A consumed-grant
record is flushed with `fsync` before effects, preventing replay after restart.
The complete output tree is published with an exclusive atomic rename; existing
destinations are never overwritten. Each published file has a receipt checked by
an independent filesystem witness.

The broker is a trusted local cold-path API, never exposed to installer scripts.
It takes explicit authority/scope arguments and does not mint hardware
attestations. This synthetic lab does not certify a deployed production runtime.
The original profile remains available for comparison without changing unrelated
execution paths.

The synthetic registry requires a fixture bearer token, listens only on loopback,
and shuts down after the run. It is not the GitHub Package Firewall product and
does not test Enterprise configuration, cooldowns, advisories, or attestations.
SHA-512 is required by the external npm integrity protocol; evidence digests use
BLAKE3. The installer environment contains fixture values and no inherited secrets.

## Reproduce on macOS

Use a fresh directory for every run. Do not change project dependencies or lockfiles.
The environment must already provide Node/npm, Rust, and Python with `blake3`.

```sh
FL_PKG_LAB_ROOT=$(mktemp -d /private/tmp/fl-pkg-01.XXXXXX)
export FL_PKG_LAB_ROOT
touch "$FL_PKG_LAB_ROOT/FL_PKG_SYNTHETIC_LAB"
cargo test --locked -q --test fl_pkg_confinement_export -- --ignored --nocapture
.venv/bin/python scripts/c5_quality_gates/fl_pkg_01.py \
  --lab-root "$FL_PKG_LAB_ROOT" --count 300 --workers 1 --include-current \
  --output "$FL_PKG_LAB_ROOT/evidence"
```

Exit 0 means `SUPPORTED_WITHIN_DOMAIN`: valid positive controls, complete A/B/C
comparison, successful benign/admitted installs, zero C escapes, and exact
publication receipts within the stated domain. Exit 1 means a physical
counterexample was observed under C (`FALSIFIED`). Exit 2 means `INCONCLUSIVE`.
C_CURRENT escapes are expected negative-control results and do not count as
escapes under the new C. Missing OS support, lab marker or required runtime fails
closed. The legacy profile/export command is required only with `--include-current`.

The default comparison performs nine warmup trials and 900 measured attempts.
With `--include-current`, it performs 12 warmup trials and 1,200 measured attempts.
Flagged artifacts are deliberately rejected in B, C and C_CURRENT. Up to six concurrent
install processes are supported; the actual concurrency is recorded and affects
the latency distribution. Default serial execution is preferable for latency
comparisons. Process groups are terminated after each trial; generated fixtures
do not detach from those groups.

## Evidence and acceptance

`observations.jsonl` records each trial and remains available on interruption.
`report.json` records metrics, environment, registry events, and receipts from the
independent TCP witness. `corpus.json` fixes artifact identities and digests;
`babylon-current.sb` fixes the evaluated OS profile. Evidence is local and mutable,
not a signed or WORM ledger.

File witnesses compare bytes and inode identity outside the installer process.
Canary exposure requires the actual fixture bytes in an exported file, captured
output, or the independent TCP receiver. Network escape requires receipt at that
receiver. Installer exit codes and DENY messages never substitute for observations.
Every hostile A control must trigger all probes; otherwise positive controls are
invalid. A physically observed escape still falsifies the tested boundary even
if another probe fails.

All four proposed zero-effect criteria are evaluated for C. The first three use
physical witnesses. `unmediated_install_effects_C` counts missing/extra/mismatched
published files against exact permits, while the OS mediates staging accesses.
`complete_mediation_verified` describes these tested scopes, not an exhaustive
trace of every kernel syscall. Missing receipts or failed installs cannot produce
a supported verdict. The report remains qualified as `SUPPORTED_WITHIN_DOMAIN`.

False rejection is failed installation among the 100 benign artifacts. Intentional
rejection of flagged hostile artifacts is excluded. The p99 uses nearest rank on
admitted cold-cache attempts, including C fetch/execution/publication and excluding
warmup and intentional admission rejects.
`policy_bypass_rate` counts admitted hostile trials with an observed forbidden
effect divided by admitted hostile trials; it is not an admission-evasion rate.

Coverage is five file mutation mechanisms (write, append, rename, symlink, child
process), a direct canary read/export, and a single IPv4 loopback TCP destination.
Separate native regressions exercise TCP, UDP, DNS and IPv6 with actual positive
and negative receivers, file aliases, raw Node syscalls and descendant writes.
Broker regressions cover forged permits, alias/special-file rejection, immutable
content, replacement of the destination inode, exclusive publication, durable
replay rejection, clock rollback, expiry and concurrent revocation.

The current publication domain is new directories containing regular files:
symlinks, hardlinks, special files, updates of existing installations and native
helpers beyond Node/the system shell fail closed. Snapshots are bounded to 64 MiB
and 4,096 paths. Entitlement-backed deployment, detached-process resource control,
arbitrary native build toolchains and full syscall tracing are not certified.
The 300 package names repeat the stated mechanisms rather than representing 300
independent exploit families.

Run the evidence-boundary regression tests with:

```sh
.venv/bin/pytest tests/test_fl_pkg_01.py tests/test_install_policy.py -q
```
