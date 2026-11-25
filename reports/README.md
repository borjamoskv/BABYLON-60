# Reports: evidence index

Baseline reviewed: [42c1be8](https://github.com/borjamoskv/BABYLON-60/tree/42c1be84fcd7b3ced7e2251e52dc9fb4065113e4/reports), 2026-11-25.

The files below are preserved receipts or samples, not a current release certification.
Authoritative claim definitions: [CLAIMS.toml](../CLAIMS.toml).
Release evidence: [manifest](../RELEASE_MANIFEST.json), [lock](../claims.lock),
[evidence](../evidence.json), [sitrep](../scripts/c5_quality_gates/claims_sitrep.json).
The baseline manifest records 32 claims (7 verified, 25 bounded), state candidate,
and no signature. A successful CI run does not promote a report or establish legal conformity.

| Artifact | Class and scope | Treatment |
| --- | --- | --- |
| [ax0-adversarial-report.json](ax0-adversarial-report.json) | Historical bounded campaign, 250 observations | The recorded universal verdict is not established by those observations. |
| [nemesis-crash-report.json](nemesis-crash-report.json) | Historical simulated recovery | Simulated, not actual SIGKILL evidence. |
| [nemesis-kernel-report.json](nemesis-kernel-report.json) | Historical empirical summary | Bounded observations, not a universal guarantee. |
| [nemesis-model-report.json](nemesis-model-report.json) | Historical formal-model summary | Theorem names are not a fresh proof-check receipt or a production refinement proof. |
| [nemesis_evidence_report.json](nemesis_evidence_report.json) | Historical APFS harness, 7d9f9dd | Target criteria are not measured results. |
| [nemesis_verified_report.json](nemesis_verified_report.json) | Historical APFS campaign, 8650fe1 | Unsigned; not a current release attestation. |
| [nemesis_evidence_report_v2.json](nemesis_evidence_report_v2.json) | Historical local run, 6a34dcf + dirty tree | 19 tests reported passed; unsigned, exact source tree not established. |
| [confine/ci-demo-linux-x86_64-f9543fb.json](confine/ci-demo-linux-x86_64-f9543fb.json) | Historical Linux CI demo | Bounded to f9543fb and its tested platform; no current certification. |
| [confine/ci-demo-macos-arm64-f9543fb.json](confine/ci-demo-macos-arm64-f9543fb.json) | Historical macOS CI demo | Same revision and platform limitation. |
| [confine/demo-linux-x86_64-20261111.json](confine/demo-linux-x86_64-20261111.json) | Historical Linux demo | Same revision and platform limitation. |
| [confine/stress-linux-x86_64-20261111.json](confine/stress-linux-x86_64-20261111.json) | Historical Linux stress run | 3,600 reported blocked attempts in the declared domain, not current or universal. |
| [eu_ai_act_compliance_pack.json](eu_ai_act_compliance_pack.json) | Superseded 2026-11-06 source-claims export | Not executed, not authorized for publication, no legal conformity; outdated statements, including RFC 9942. Preserve original bytes. |
| [babylon_assurance_gateway_sample.json](babylon_assurance_gateway_sample.json) | Simulated provider sample | Demonstration only; witness independence and legal conformity not established. |
| [babylon_assurance_gateway_deployer_fria_sample.json](babylon_assurance_gateway_deployer_fria_sample.json) | Simulated deployer/FRIA sample | Demonstration only; witness independence and legal conformity not established. |
| [c5_valuation_receipt_v511.json](c5_valuation_receipt_v511.json) | Historical economic estimate, 5.1.1 | Not a market valuation, signed appraisal or current 5.1.0 release evidence; reconcile metrics and scenario factors. |
| [c5_valuation_receipt_v511.json.ots](c5_valuation_receipt_v511.json.ots) | Timestamp sidecar | Preserve beside its original bytes; presence does not verify the anchor or substantiate the valuation. |

## Refresh and acceptance

Preserve original bytes at the baseline and do not relabel historical results.
Export updated source claims to a separate location using the existing
[exporter](../tools/generate_compliance_audit_pack.py), for example:

```bash
python3 tools/generate_compliance_audit_pack.py --output /tmp/babylon-compliance-review.json
```

The exporter refuses to overwrite an existing destination; use a new output path for each export.
A fresh export is still pending legal review and is not publication-authorized.
Use [the existing NEMESIS generator](../scripts/c5_quality_gates/generate_nemesis_report.py)
and [CONFINE CI](../.github/workflows/confine.yml) for new bounded test receipts
on their applicable platforms; retain each source revision and raw outcome.
Use [the existing release refresh](../scripts/c5_quality_gates/refresh_tracked_evidence.py)
and [verification](../verify.sh) for a new clean-source release evidence set.
Do not copy or reinterpret old digests as new receipts. A separately authorized signing
key and actual verification are required to claim a signed release.
Publication and merge remain subject to the project's existing authorization policy.
