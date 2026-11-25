"""FL-AIACT-02: Regulatory Evidence Continuity & Evidence-to-Conformity Boundary.

Verifies the Regulatory Evidence Graph (`babylon.assurance.claim.v1`) in silicon:
  1. AcceptEvidence(c, a) => Bound(c, a) & Applicable(c, a) & Verified(c)
  2. TechnicalPASS !=> LegalConformity (never emits automatic COMPLIANT or EU_AI_ACT_CERTIFIED)
  3. Selective Graph Invalidation: mutating one dimension (e.g., policy_sha256)
     invalidates only claims bound to that dimension while preserving orthogonal
     valid claims (e.g., Art. 10 data lineage or Art. 17 QMS).
  4. Art. 43 vs. Art. 43.4 distinction (substantial modification vs. predetermined
     change envelope).
  5. Differential statutory retention (Art. 18 10 years, Art. 26.6 >= 6 months,
     and GDPR/EDPB salted commitments off-ledger).
  6. 1,000 deterministic controlled mutations + independent holdout set.
"""

from __future__ import annotations

import base64
import copy
import hashlib
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric import ed25519
import pytest

from babylon60.compliance_exporter.regulatory import (
    ANNEX_IV_MANDATORY_SECTIONS,
    ANNEX_IV_SCHEMA,
    ARTICLE_9_MANDATORY_PHASES,
    CATALOGUE_DIGEST,
    CLAIM_SCHEMA,
    FRIA_SCHEMA,
    GATEWAY_BUNDLE_SCHEMA,
    GRAPH_EVAL_SCHEMA,
    RISK_MANAGEMENT_SCHEMA,
    canonical,
    classify_system_change,
    digest,
    evaluate_claim_node,
    evaluate_evidence_graph,
    export_assurance_gateway_bundle,
    generate_deployer_fria_sample_bundle,
    generate_sample_assurance_gateway_bundle,
    load_json,
    requires_fria_article_27,
    validate_annex_iv_structure,
    validate_article_9_risk_management,
    validate_model_identity,
    validate_retention_policy,
)


def _h(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


@pytest.fixture
def graph_workspace(tmp_path: Path) -> dict[str, Any]:
    """Create a realistic high-risk AI system evidence bundle and 9-node Regulatory Evidence Graph."""
    reviewer_key = ed25519.Ed25519PrivateKey.generate()
    policy = {
        "reviewers": {
            "legal-counsel-1": {
                "name": "Accountable Legal & Compliance Officer",
                "scopes": ["assessment"],
                "system_ids": ["SYS-HR-RECRUIT-01"],
                "public_key_hex": reviewer_key.public_key().public_bytes_raw().hex(),
            }
        },
        "revoked_reviews": [],
        "revoked_authorizations": [],
    }

    baseline_system = {
        "system_id": "SYS-HR-RECRUIT-01",
        "operator_role": "provider",
        "intended_purpose_id": _h("annex-iii-4a-recruitment-screening-v1"),
        "model_identity": f"sha256:{_h('weights-v1.0')}",
        "artifact_sha256": _h("babylon-guard-binary-v1.0"),
        "runtime_profile_sha256": _h("macos-seatbelt-profile-v1.0"),
        "policy_sha256": _h("capability-policy-epoch-1"),
    }

    articles_and_bindings: list[tuple[str, int, list[str], dict[str, Any]]] = [
        (
            "CLM-A9-RISK",
            9,
            ["intended_purpose_id", "model_identity", "policy_sha256"],
            {"data_class": "provider_technical_documentation", "retention_months": 120},
        ),
        (
            "CLM-A10-DATA",
            10,
            ["intended_purpose_id", "model_identity"],
            {
                "data_class": "gdpr_personal_or_prompt_data",
                "retention_months": 6,
                "contains_personal_data": True,
                "raw_personal_data_on_immutable_ledger": False,
                "unsalted_pii_hash_on_ledger": False,
                "commitment_scheme": "BLAKE3_DERIVE_KEY_SALTED",
                "off_ledger_erasable_store": True,
            },
        ),
        (
            "CLM-A11-DOC",
            11,
            ["intended_purpose_id", "artifact_sha256"],
            {"data_class": "provider_technical_documentation", "retention_months": 120},
        ),
        (
            "CLM-A12-LOG",
            12,
            ["artifact_sha256", "runtime_profile_sha256"],
            {
                "data_class": "operational_event_logs",
                "retention_months": 6,
                "contains_personal_data": True,
                "raw_personal_data_on_immutable_ledger": False,
                "unsalted_pii_hash_on_ledger": False,
                "commitment_scheme": "BLAKE3_DERIVE_KEY_SALTED",
                "off_ledger_erasable_store": True,
            },
        ),
        (
            "CLM-A13-TRANSPARENCY",
            13,
            ["intended_purpose_id"],
            {"data_class": "provider_technical_documentation", "retention_months": 120},
        ),
        (
            "CLM-A14-OVERSIGHT",
            14,
            ["intended_purpose_id", "policy_sha256"],
            {"data_class": "operational_event_logs", "retention_months": 12},
        ),
        (
            "CLM-A15-ROBUSTNESS",
            15,
            ["artifact_sha256", "runtime_profile_sha256", "policy_sha256"],
            {"data_class": "provider_technical_documentation", "retention_months": 120},
        ),
        (
            "CLM-A17-QMS",
            17,
            ["intended_purpose_id"],
            {"data_class": "provider_technical_documentation", "retention_months": 120},
        ),
        (
            "CLM-A43-CONFORMITY-TRIGGERS",
            43,
            ["intended_purpose_id", "artifact_sha256"],
            {"data_class": "provider_technical_documentation", "retention_months": 120},
        ),
    ]

    claims: list[dict[str, Any]] = []
    for cid, article, bound_dims, retention in articles_and_bindings:
        ev_rel = f"evidence_{cid.lower()}.json"
        ev_file = tmp_path / ev_rel
        ev_bytes = f'{{"claim_id":"{cid}","article":{article},"verified":true}}'.encode("utf-8")
        ev_file.write_bytes(ev_bytes)
        ev_sha = hashlib.sha256(ev_bytes).hexdigest()

        claims.append(
            {
                "schema": CLAIM_SCHEMA,
                "claim_id": cid,
                "bound_dimensions": bound_dims,
                "legal": {
                    "jurisdiction": "EU",
                    "regulation": "2024/1689",
                    "consolidated_at": "2026-07-27",
                    "article": article,
                    "applicability": "applicable",
                    "operator_role": "provider",
                },
                "system": copy.deepcopy(baseline_system),
                "retention": retention,
                "claim": {
                    "predicate": f"article_{article}_invariants_verified == true",
                    "scope": "isolated_test_environment",
                    "evidence_path": ev_rel,
                    "evidence_digest": ev_sha,
                    "verdict": "SUPPORTED_WITHIN_DOMAIN",
                },
                "evaluation": {
                    "test_suite_digest": _h(f"suite-{cid}"),
                    "independent_witness": True,
                    "unresolved_findings": 0,
                },
                "review": {
                    "technical_status": "PASS",
                    "legal_status": "NOT_ASSESSED",
                },
            }
        )

    return {
        "root": tmp_path,
        "baseline_system": baseline_system,
        "target_deployment": {"system": copy.deepcopy(baseline_system)},
        "claims": claims,
        "policy": policy,
        "reviewer_key": reviewer_key,
    }


def test_baseline_graph_accepts_all_and_preserves_legal_boundary(graph_workspace: dict[str, Any]) -> None:
    res = evaluate_evidence_graph(
        graph_workspace["claims"],
        graph_workspace["target_deployment"],
        graph_workspace["root"],
        baseline_system=graph_workspace["baseline_system"],
        policy=graph_workspace["policy"],
        now=1_800_000_000,
    )
    assert res["schema"] == GRAPH_EVAL_SCHEMA
    assert res["technical_status"] == "TECHNICAL_EVIDENCE_VALID"
    assert res["legal_status"] == "LEGAL_REVIEW_REQUIRED"
    assert res["verdict"] == "SUPPORTED_WITHIN_TESTED_DOMAIN"
    assert res["eu_ai_act_certified"] is False
    assert res["critical_checks_missing"] == 0
    assert res["stale_or_invalid_claims_rejected"] == 0
    assert len(res["accepted_claim_ids"]) == 9


def test_selective_invalidation_preserves_orthogonal_claims(graph_workspace: dict[str, Any]) -> None:
    """Changing policy_sha256 invalidates only policy-bound claims (Arts. 9, 14, 15)
    while preserving orthogonal claims (Arts. 10, 11, 12, 13, 17, 43).
    """
    target = copy.deepcopy(graph_workspace["target_deployment"])
    target["system"]["policy_sha256"] = _h("capability-policy-epoch-2-mutated")

    res = evaluate_evidence_graph(
        graph_workspace["claims"],
        target,
        graph_workspace["root"],
        baseline_system=graph_workspace["baseline_system"],
        now=1_800_000_000,
    )
    assert res["change_classification"]["classification"] == "SELECTIVE_TECHNICAL_REVALIDATION"
    assert res["change_classification"]["requires_substantial_modification_assessment"] is False
    assert set(res["rejected_claim_ids"]) == {"CLM-A9-RISK", "CLM-A14-OVERSIGHT", "CLM-A15-ROBUSTNESS"}
    assert set(res["accepted_claim_ids"]) == {
        "CLM-A10-DATA",
        "CLM-A11-DOC",
        "CLM-A12-LOG",
        "CLM-A13-TRANSPARENCY",
        "CLM-A17-QMS",
        "CLM-A43-CONFORMITY-TRIGGERS",
    }
    assert res["technical_status"] == "EVIDENCE_INCOMPLETE"


def test_art43_4_predetermined_change_envelope_avoids_false_rejection(graph_workspace: dict[str, Any]) -> None:
    """A change pre-authorized under Art. 43.4 envelope without retest keeps claims valid."""
    old_policy = graph_workspace["baseline_system"]["policy_sha256"]
    new_policy = _h("capability-policy-epoch-2-preauthorized")
    target = copy.deepcopy(graph_workspace["target_deployment"])
    target["system"]["policy_sha256"] = new_policy

    envelopes = [
        {
            "dimension": "policy_sha256",
            "baseline_values": [old_policy],
            "allowed_values": [new_policy],
            "requires_technical_retest": False,
        }
    ]
    res = evaluate_evidence_graph(
        graph_workspace["claims"],
        target,
        graph_workspace["root"],
        baseline_system=graph_workspace["baseline_system"],
        predetermined_envelopes=envelopes,
        now=1_800_000_000,
    )
    assert res["change_classification"]["classification"] == "WITHIN_PREDETERMINED_ENVELOPE"
    assert res["change_classification"]["requires_substantial_modification_assessment"] is False
    assert res["technical_status"] == "TECHNICAL_EVIDENCE_VALID"
    assert len(res["accepted_claim_ids"]) == 9


def test_external_model_uncertainty_and_gdpr_retention_rules(graph_workspace: dict[str, Any]) -> None:
    # 1. External model without uncertainty_declared is rejected
    ok, reason, is_ext = validate_model_identity({"model_identity": "openai:gpt-5:2026-08"})
    assert not ok and reason == "MODEL_UNCERTAINTY_NOT_DECLARED" and is_ext

    # 2. External model with uncertainty_declared + containment_policy is accepted
    ok, reason, is_ext = validate_model_identity(
        {
            "model_identity": "openai:gpt-5:2026-08",
            "model_uncertainty_declared": True,
            "containment_policy": "BROKER_STRICT_SANDBOX",
        }
    )
    assert ok and reason == "EXTERNAL_MODEL_WITH_DECLARED_UNCERTAINTY" and is_ext

    # 3. GDPR & Statutory retention checks
    ok, reason = validate_retention_policy({"data_class": "provider_technical_documentation", "retention_months": 60})
    assert not ok and reason == "RETENTION_BELOW_STATUTORY_MINIMUM_ART_18"

    ok, reason = validate_retention_policy({"data_class": "operational_event_logs", "retention_months": 3})
    assert not ok and reason == "RETENTION_BELOW_STATUTORY_MINIMUM_ART_26"

    ok, reason = validate_retention_policy(
        {
            "data_class": "operational_event_logs",
            "retention_months": 6,
            "raw_personal_data_on_immutable_ledger": True,
        }
    )
    assert not ok and reason == "GDPR_IMMUTABLE_LEDGER_RAW_PII_FORBIDDEN"

    ok, reason = validate_retention_policy(
        {
            "data_class": "operational_event_logs",
            "retention_months": 6,
            "contains_personal_data": True,
            "unsalted_pii_hash_on_ledger": True,
        }
    )
    assert not ok and reason == "EDPB_UNSALTED_PII_HASH_ON_LEDGER_FORBIDDEN"


def test_accountable_human_signature_enables_conformity_documented(graph_workspace: dict[str, Any]) -> None:
    now = 1_800_000_000
    key: ed25519.Ed25519PrivateKey = graph_workspace["reviewer_key"]
    signed_claims = copy.deepcopy(graph_workspace["claims"])

    for node in signed_claims:
        node_without_review = {k: v for k, v in node.items() if k != "review"}
        stmt = {
            "reviewer": "legal-counsel-1",
            "system_id": "SYS-HR-RECRUIT-01",
            "claim_digest": digest(node_without_review),
            "expires_at": now + 3600,
        }
        sig = base64.b64encode(key.sign(canonical(stmt))).decode("ascii")
        node["review"] = {
            "technical_status": "PASS",
            "legal_status": "CONFORMITY_DOCUMENTED",
            "human_review_record": {"statement": stmt, "signature": sig},
        }

    res = evaluate_evidence_graph(
        signed_claims,
        graph_workspace["target_deployment"],
        graph_workspace["root"],
        baseline_system=graph_workspace["baseline_system"],
        policy=graph_workspace["policy"],
        now=now,
    )
    assert res["technical_status"] == "TECHNICAL_EVIDENCE_VALID"
    assert res["legal_status"] == "CONFORMITY_DOCUMENTED"
    assert res["eu_ai_act_certified"] is False


def test_fl_aiact_02_1000_controlled_mutations_and_holdout(graph_workspace: dict[str, Any]) -> None:
    """Execute 1,000 deterministic mutations across 8 scenario families + 40 holdout cases.

    Proves:
      - false_acceptances == 0 (AcceptEvidence(c,a) => Bound(c,a) & Applicable(c,a) & Verified(c))
      - illegal_auto_conformity == 0 (TechnicalPASS !=> LegalConformity)
      - false_rejections == 0 (valid nodes and orthogonal nodes remain accepted)
    """
    base_claim = graph_workspace["claims"][6]  # CLM-A15-ROBUSTNESS (bound to artifact, runtime, policy)
    orthogonal_claim = graph_workspace["claims"][1]  # CLM-A10-DATA (bound to intended_purpose, model_identity)
    base_target = graph_workspace["target_deployment"]
    root = graph_workspace["root"]

    false_acceptances = 0
    false_rejections = 0
    illegal_auto_conformity = 0
    orthogonal_preservation_failures = 0

    for i in range(1000):
        family = i % 8
        c = copy.deepcopy(base_claim)
        orth = copy.deepcopy(orthogonal_claim)
        t = copy.deepcopy(base_target)
        envelopes: list[dict[str, Any]] = []
        expect_c_accepted = False
        expect_orth_accepted = True

        if family == 0:
            # Family 0: Verified binary replaced after testing -> must reject c, preserve orth
            t["system"]["artifact_sha256"] = _h(f"tampered-binary-{i}")
            expect_c_accepted = False
            expect_orth_accepted = True
        elif family == 1:
            # Family 1: Execution policy mutated -> must reject c, preserve orth
            t["system"]["policy_sha256"] = _h(f"mutated-policy-{i}")
            expect_c_accepted = False
            expect_orth_accepted = True
        elif family == 2:
            # Family 2: Unverifiable external model injected without uncertainty declaration -> reject orth
            t["system"]["model_identity"] = f"vendor:opaque-llm:v{i}"
            t["system"]["model_uncertainty_declared"] = False
            expect_c_accepted = True  # c is not bound to model_identity!
            expect_orth_accepted = False  # orth IS bound to model_identity
        elif family == 3:
            # Family 3: Critical check omitted or unresolved findings > 0 -> reject c, preserve orth
            c["evaluation"]["unresolved_findings"] = (i % 5) + 1
            expect_c_accepted = False
            expect_orth_accepted = True
        elif family == 4:
            # Family 4: Intended purpose modified -> orth rejected + substantial modification triggered
            t["system"]["intended_purpose_id"] = _h(f"new-purpose-{i}")
            expect_c_accepted = True  # c is only bound to artifact, runtime, policy
            expect_orth_accepted = False  # orth is bound to intended_purpose_id
        elif family == 5:
            # Family 5: Agent attempts automatic legal conformity promotion (TechnicalPASS -> COMPLIANT)
            c["review"]["legal_status"] = "COMPLIANT" if i % 2 == 0 else "EU_AI_ACT_CERTIFIED"
            expect_c_accepted = False
            expect_orth_accepted = True
        elif family == 6:
            # Family 6: Predetermined change envelope (Art. 43.4) with no retest required -> both accepted
            new_pol = _h(f"envelope-policy-{i}")
            old_pol = c["system"]["policy_sha256"]
            t["system"]["policy_sha256"] = new_pol
            envelopes = [
                {
                    "dimension": "policy_sha256",
                    "baseline_values": [old_pol],
                    "allowed_values": [new_pol],
                    "requires_technical_retest": False,
                }
            ]
            expect_c_accepted = True
            expect_orth_accepted = True
        else:
            # Family 7: Legitimate deployment (positive control) -> both accepted
            expect_c_accepted = True
            expect_orth_accepted = True

        res_c = evaluate_claim_node(c, t, root, predetermined_envelopes=envelopes, now=1_800_000_000)
        res_orth = evaluate_claim_node(orth, t, root, predetermined_envelopes=envelopes, now=1_800_000_000)

        if res_c["accepted"]:
            if not (res_c["bound"] and res_c["applicable"] and res_c["verified"]):
                false_acceptances += 1
            if not expect_c_accepted:
                false_acceptances += 1
        elif expect_c_accepted:
            false_rejections += 1

        if res_orth["accepted"] != expect_orth_accepted:
            orthogonal_preservation_failures += 1

        if res_c["legal_status"] in {"COMPLIANT", "EU_AI_ACT_CERTIFIED"} or res_orth["legal_status"] in {
            "COMPLIANT",
            "EU_AI_ACT_CERTIFIED",
        }:
            illegal_auto_conformity += 1

    # Independent Holdout Set (40 classified boundary cases: GDPR violations, post-market incidents, role mismatches)
    for h_idx in range(40):
        c_hold = copy.deepcopy(base_claim)
        t_hold = copy.deepcopy(base_target)
        mode = h_idx % 4
        if mode == 0:
            # GDPR raw personal data on immutable ledger
            c_hold["retention"]["raw_personal_data_on_immutable_ledger"] = True
            r = evaluate_claim_node(c_hold, t_hold, root, now=1_800_000_000)
            if r["accepted"]:
                false_acceptances += 1
        elif mode == 1:
            # Evidence digest mismatch against file on disk
            c_hold["claim"]["evidence_digest"] = _h(f"forged-evidence-{h_idx}")
            r = evaluate_claim_node(c_hold, t_hold, root, now=1_800_000_000)
            if r["accepted"]:
                false_acceptances += 1
        elif mode == 2:
            # Post-market serious incident reported (Art. 72/73) blocks overall graph
            g_res = evaluate_evidence_graph(
                graph_workspace["claims"],
                t_hold,
                root,
                baseline_system=graph_workspace["baseline_system"],
                post_market_incidents=[{"incident_id": f"INC-{h_idx}", "severity": "SERIOUS"}],
                now=1_800_000_000,
            )
            if (
                g_res["change_classification"]["classification"] != "POST_MARKET_INCIDENT_REVIEW_REQUIRED"
                or g_res["technical_status"] == "TECHNICAL_EVIDENCE_VALID"
            ):
                false_acceptances += 1
        else:
            # Valid external model with declared uncertainty + containment
            c_ext = copy.deepcopy(orthogonal_claim)
            ext_sys = copy.deepcopy(t_hold["system"])
            ext_sys["model_identity"] = f"google:gemini-4-argon:2026-11-{h_idx}"
            ext_sys["model_uncertainty_declared"] = True
            ext_sys["containment_policy"] = "RING0_CAPABILITY_BROKER"
            c_ext["system"] = copy.deepcopy(ext_sys)
            r = evaluate_claim_node(c_ext, {"system": ext_sys}, root, now=1_800_000_000)
            if not r["accepted"]:
                false_rejections += 1

    assert false_acceptances == 0
    assert false_rejections == 0
    assert illegal_auto_conformity == 0
    assert orthogonal_preservation_failures == 0


def test_change_classifier_distinguishes_all_five_regimes(graph_workspace: dict[str, Any]) -> None:
    base = graph_workspace["baseline_system"]

    # 1. No change
    assert classify_system_change(base, copy.deepcopy(base))["classification"] == "NO_CHANGE"

    # 2. Localized technical change
    t_pol = copy.deepcopy(base)
    t_pol["policy_sha256"] = _h("pol-2")
    assert classify_system_change(base, t_pol)["classification"] == "SELECTIVE_TECHNICAL_REVALIDATION"

    # 3. Predetermined envelope (Art. 43.4)
    env = [{"dimension": "policy_sha256", "allowed_values": [_h("pol-2")], "requires_technical_retest": False}]
    assert (
        classify_system_change(base, t_pol, predetermined_envelopes=env)["classification"]
        == "WITHIN_PREDETERMINED_ENVELOPE"
    )

    # 4. Substantial modification (Art. 43 / Art. 3.23)
    t_purp = copy.deepcopy(base)
    t_purp["intended_purpose_id"] = _h("credit-scoring-annex-iii-5b")
    assert classify_system_change(base, t_purp)["classification"] == "SUBSTANTIAL_MODIFICATION_REVIEW_REQUIRED"

    # 5. Post-market incident (Art. 72 / Art. 73)
    assert (
        classify_system_change(base, base, post_market_incidents=[{"id": "INC-1"}])["classification"]
        == "POST_MARKET_INCIDENT_REVIEW_REQUIRED"
    )


def test_export_assurance_gateway_bundle_three_deliverables(graph_workspace: dict[str, Any]) -> None:
    """Verify the three BABYLON Assurance Gateway outputs (Execution Evidence,
    Assurance Dossier, Continuous Evidence Monitoring) under baseline and post-change states.
    """
    bundle = export_assurance_gateway_bundle(
        graph_workspace["claims"],
        graph_workspace["target_deployment"],
        graph_workspace["root"],
        baseline_system=graph_workspace["baseline_system"],
        policy=graph_workspace["policy"],
        now=1_800_000_000,
    )
    assert bundle["schema"] == GATEWAY_BUNDLE_SCHEMA
    assert bundle["eu_ai_act_certified"] is False

    # 1. Execution Evidence
    exec_ev = bundle["execution_evidence"]
    assert exec_ev["system_identity"]["model_identity_valid"] is True
    assert exec_ev["unauthorized_effects"] == 0
    assert len(exec_ev["reproducible_test_receipts"]) == 9
    assert all(r["retention_valid"] for r in exec_ev["retention_and_gdpr_controls"])

    # 2. Assurance Dossier
    dossier = bundle["assurance_dossier"]
    assert dossier["regulation"]["amendment"] == "Regulation (EU) 2026/1744"
    assert dossier["value_chain_positioning"] == "ART_25_4_TECHNICAL_EVIDENCE_AND_ASSURANCE_INTERFACE"
    assert dossier["technical_status"] == "TECHNICAL_EVIDENCE_VALID"
    assert dossier["legal_status"] == "LEGAL_REVIEW_REQUIRED"
    assert dossier["verdict"] == "SUPPORTED_WITHIN_TESTED_DOMAIN"
    assert dossier["eu_ai_act_certified"] is False

    # 3. Continuous Evidence Monitoring under selective policy mutation
    mutated_target = copy.deepcopy(graph_workspace["target_deployment"])
    mutated_target["system"]["policy_sha256"] = _h("mutated-policy-epoch-99")
    monitored = export_assurance_gateway_bundle(
        graph_workspace["claims"],
        mutated_target,
        graph_workspace["root"],
        baseline_system=graph_workspace["baseline_system"],
        policy=graph_workspace["policy"],
        now=1_800_000_000,
    )
    mon = monitored["continuous_evidence_monitoring"]
    assert mon["change_classification"]["classification"] == "SELECTIVE_TECHNICAL_REVALIDATION"
    assert mon["requires_substantial_modification_assessment"] is False
    assert set(mon["invalidated_or_stale_claim_ids"]) == {
        "CLM-A9-RISK",
        "CLM-A14-OVERSIGHT",
        "CLM-A15-ROBUSTNESS",
    }
    assert set(mon["accepted_orthogonal_claim_ids"]) == {
        "CLM-A10-DATA",
        "CLM-A11-DOC",
        "CLM-A12-LOG",
        "CLM-A13-TRANSPARENCY",
        "CLM-A17-QMS",
        "CLM-A43-CONFORMITY-TRIGGERS",
    }


def test_cli_gateway_bundle_mode_exit_codes_and_json_structure(graph_workspace: dict[str, Any]) -> None:
    """Verify `--mode gateway-bundle` CLI invocation returns 0 on valid evidence and 2 on stale/incomplete evidence."""
    import json
    import os
    import subprocess
    import sys

    repo_root = Path(__file__).absolute().parents[1]
    cli_env = {**os.environ, "PYTHONPATH": str(repo_root / "01_KISH_ENGINE")}
    root: Path = graph_workspace["root"]
    graph_file = root / "claims_graph.json"
    out_file = root / "gateway_bundle_out.json"

    graph_payload = {
        "claims": graph_workspace["claims"],
        "baseline_system": graph_workspace["baseline_system"],
        "target_deployment": graph_workspace["target_deployment"],
    }
    graph_file.write_text(json.dumps(graph_payload), encoding="utf-8")

    cmd = [
        sys.executable,
        "-m",
        "babylon60.compliance_exporter.eu_ai_act",
        "--mode",
        "gateway-bundle",
        "--claims-graph",
        str(graph_file),
        "--bundle",
        str(root),
        "--output",
        str(out_file),
    ]
    proc_ok = subprocess.run(cmd, capture_output=True, text=True, check=False, env=cli_env)
    assert proc_ok.returncode == 0, proc_ok.stderr
    bundle_data = json.loads(out_file.read_text(encoding="utf-8"))
    assert bundle_data["schema"] == GATEWAY_BUNDLE_SCHEMA
    assert bundle_data["eu_ai_act_certified"] is False
    assert bundle_data["assurance_dossier"]["technical_status"] == "TECHNICAL_EVIDENCE_VALID"
    assert bundle_data["assurance_dossier"]["legal_status"] == "LEGAL_REVIEW_REQUIRED"

    # Mutate policy_sha256 in target_deployment -> must exit with code 2 (EVIDENCE_INCOMPLETE)
    graph_payload["target_deployment"]["system"]["policy_sha256"] = _h("cli-mutated-policy")
    graph_file.write_text(json.dumps(graph_payload), encoding="utf-8")
    proc_stale = subprocess.run(cmd, capture_output=True, text=True, check=False, env=cli_env)
    assert proc_stale.returncode == 2
    stale_bundle = json.loads(out_file.read_text(encoding="utf-8"))
    assert stale_bundle["assurance_dossier"]["technical_status"] == "EVIDENCE_INCOMPLETE"
    assert len(stale_bundle["continuous_evidence_monitoring"]["accepted_orthogonal_claim_ids"]) == 6


def test_sample_assurance_gateway_report_reproducible_and_valid(tmp_path: Path) -> None:
    """Verify reports/babylon_assurance_gateway_sample.json is reproducible and satisfies FL-AIACT-02."""
    repo_root = Path(__file__).absolute().parents[1]
    sample_path = repo_root / "reports" / "babylon_assurance_gateway_sample.json"
    assert sample_path.is_file()

    on_disk = load_json(sample_path)
    regenerated = generate_sample_assurance_gateway_bundle(tmp_path / "sample_bundle")

    assert on_disk == regenerated
    assert on_disk["schema"] == GATEWAY_BUNDLE_SCHEMA
    assert on_disk["eu_ai_act_certified"] is False
    assert on_disk["execution_evidence"]["system_identity"]["is_external_opaque_model"] is True
    assert on_disk["execution_evidence"]["system_identity"]["model_identity_status"] == (
        "EXTERNAL_MODEL_WITH_DECLARED_UNCERTAINTY"
    )
    assert on_disk["assurance_dossier"]["technical_status"] == "TECHNICAL_EVIDENCE_VALID"
    assert on_disk["assurance_dossier"]["legal_status"] == "LEGAL_REVIEW_REQUIRED"
    assert on_disk["assurance_dossier"]["verdict"] == "SUPPORTED_WITHIN_TESTED_DOMAIN"


def test_art27_fria_conditional_applicability_by_deployer_and_use_case(graph_workspace: dict[str, Any]) -> None:
    """Verify Art. 27 FRIA is conditionally required only for qualifying deployers and Annex III 5(b)/(c) uses."""
    # Provider or generic private deployer in HR does not automatically trigger Art. 27 FRIA
    assert requires_fria_article_27({"operator_role": "provider", "deployer_category": "public_body"}) is False
    assert requires_fria_article_27({"operator_role": "deployer", "deployer_category": "private_enterprise"}) is False

    # Public body or Annex III 5(b)/(c) deployer triggers Art. 27 FRIA
    pub_deployer = {
        **copy.deepcopy(graph_workspace["baseline_system"]),
        "operator_role": "deployer",
        "deployer_category": "public_body",
    }
    credit_deployer = {
        **copy.deepcopy(graph_workspace["baseline_system"]),
        "operator_role": "deployer",
        "deployer_category": "private_enterprise",
        "annex_iii_use_case": "annex_iii_5b_creditworthiness",
    }
    assert requires_fria_article_27(pub_deployer) is True
    assert requires_fria_article_27(credit_deployer) is True

    deployer_claims = copy.deepcopy(graph_workspace["claims"])
    for c in deployer_claims:
        c["legal"]["operator_role"] = "deployer"
        c["system"]["operator_role"] = "deployer"

    # Without an Article 27 claim, a public_body deployer fails missing_critical_articles == [27]
    res_missing_fria = evaluate_evidence_graph(
        deployer_claims,
        {"system": pub_deployer},
        graph_workspace["root"],
        baseline_system=pub_deployer,
        now=1_800_000_000,
    )
    assert res_missing_fria["fria_article_27_required"] is True
    assert res_missing_fria["missing_critical_articles"] == [27]
    assert res_missing_fria["technical_status"] == "EVIDENCE_INCOMPLETE"

    # Attempting to exempt Art. 27 as not_applicable for a qualifying deployer is rejected fail-closed
    fria_exempt = copy.deepcopy(deployer_claims[0])
    fria_exempt["claim_id"] = "CLM-A27-FRIA"
    fria_exempt["legal"]["article"] = 27
    fria_exempt["legal"]["applicability"] = "not_applicable"
    r_exempt = evaluate_claim_node(fria_exempt, {"system": pub_deployer}, graph_workspace["root"], now=1_800_000_000)
    assert r_exempt["accepted"] is False
    assert "ART_27_FRIA_MANDATORY_FOR_DEPLOYER_PROFILE" in r_exempt["reasons"]


def test_requirement_drift_and_temporal_evidence_expiration_fail_closed(
    graph_workspace: dict[str, Any],
) -> None:
    """Verify FL-AIACT-01-v2 requirement version drift and temporal evidence TTL checks."""
    now = 1_800_000_000
    target = copy.deepcopy(graph_workspace["target_deployment"])
    target["evaluation_profile_digest"] = _h("eval-profile-v2")

    # 1. Catalogue digest drift is rejected
    c_cat_drift = copy.deepcopy(graph_workspace["claims"][0])
    c_cat_drift["legal"]["catalogue_digest"] = _h("outdated-catalogue-v0")
    r_cat = evaluate_claim_node(c_cat_drift, target, graph_workspace["root"], now=now)
    assert r_cat["accepted"] is False
    assert "REQUIREMENT_CATALOGUE_DIGEST_DRIFT" in r_cat["reasons"]

    # 2. Matching catalogue_digest + evaluation_profile_digest succeeds
    c_valid_pin = copy.deepcopy(graph_workspace["claims"][0])
    c_valid_pin["legal"]["catalogue_digest"] = CATALOGUE_DIGEST
    c_valid_pin["legal"]["evaluation_profile_digest"] = _h("eval-profile-v2")
    r_pin_ok = evaluate_claim_node(c_valid_pin, target, graph_workspace["root"], now=now)
    assert r_pin_ok["accepted"] is True

    # 3. Evaluation profile digest mismatch is rejected
    c_prof_drift = copy.deepcopy(c_valid_pin)
    c_prof_drift["legal"]["evaluation_profile_digest"] = _h("eval-profile-v1-stale")
    r_prof = evaluate_claim_node(c_prof_drift, target, graph_workspace["root"], now=now)
    assert r_prof["accepted"] is False
    assert "EVALUATION_PROFILE_DIGEST_DRIFT" in r_prof["reasons"]

    # 4. Expired evidence (expires_at <= now) is rejected
    c_expired = copy.deepcopy(graph_workspace["claims"][0])
    c_expired["evaluation"]["expires_at"] = now
    r_exp = evaluate_claim_node(c_expired, target, graph_workspace["root"], now=now)
    assert r_exp["accepted"] is False
    assert "EVIDENCE_EXPIRED" in r_exp["reasons"]

    # 5. Graph-level FL-AIACT-01-v2 gate counters record blocked attacks with 0 false acceptances
    mutated_claims = copy.deepcopy(graph_workspace["claims"])
    mutated_claims[0] = c_cat_drift
    mutated_claims[1] = c_expired
    mutated_claims[2]["review"]["legal_status"] = "COMPLIANT"
    mutated_claims[3]["system"]["artifact_sha256"] = _h("other-artifact")

    g_eval = evaluate_evidence_graph(
        mutated_claims,
        target,
        graph_workspace["root"],
        baseline_system=graph_workspace["baseline_system"],
        now=now,
    )
    gate = g_eval["fl_aiact_01_v2_gate"]
    assert gate["cross_artifact_evidence_reuse"] == 0
    assert gate["stale_critical_evidence_accept"] == 0
    assert gate["unauthorized_status_promotions"] == 0
    assert gate["undetected_requirement_drift"] == 0
    assert gate["unauthorized_deployment_effects"] == 0
    assert gate["blocked_requirement_drift"] == 1
    assert gate["blocked_stale_or_expired_evidence"] == 1
    assert gate["blocked_unauthorized_promotions"] == 1
    assert gate["blocked_cross_artifact_or_unbound"] == 1
    assert gate["legitimate_deployment_acceptance"] == 0


def test_annex_iv_structural_validation_rules(tmp_path: Path, graph_workspace: dict[str, Any]) -> None:
    """Verify EU AI Act Annex IV structural validation rules and claim integration."""
    # 1. Non-dict input
    ok, reason, missing = validate_annex_iv_structure("not a dict")
    assert not ok and reason == "ANNEX_IV_NOT_A_DOCUMENT" and len(missing) == len(ANNEX_IV_MANDATORY_SECTIONS)

    # 2. Schema invalid
    ok, reason, _ = validate_annex_iv_structure({"schema": "invalid.schema"})
    assert not ok and reason == "ANNEX_IV_SCHEMA_INVALID"

    # 3. Missing sections
    partial_doc = {"schema": ANNEX_IV_SCHEMA, "section_1_general_description": {"intended_purpose": "test"}}
    ok, reason, missing = validate_annex_iv_structure(partial_doc)
    assert not ok and "ANNEX_IV_MISSING_SECTIONS_" in reason and len(missing) == 7

    # 4. Valid document passes
    valid_annex_iv: dict[str, Any] = {
        "schema": ANNEX_IV_SCHEMA,
        "section_1_general_description": {
            "intended_purpose": "Annex III high-risk AI assessment",
            "system_version": "v1.0",
            "hardware_requirements": "apple-silicon-m3",
        },
        "section_2_development_process": {
            "data_governance": {"lineage_verified": True},
            "human_oversight": "dual_review",
            "validation_and_testing": {"status": "passed"},
        },
        "section_3_monitoring_and_control": {
            "capabilities_and_limitations": "documented",
            "cybersecurity_measures": "seatbelt",
        },
        "section_4_risk_management": {"risk_management_system": "ISO_42001"},
        "section_5_change_log": {"changes": []},
        "section_6_standards": {"harmonised_standards": ["EN_ISO_42001"]},
        "section_7_declaration_of_conformity": {"eu_declaration_of_conformity_status": "PENDING"},
        "section_8_post_market_monitoring": {"post_market_monitoring_plan": "continuous"},
    }
    ok, reason, missing = validate_annex_iv_structure(valid_annex_iv)
    assert ok and reason == "ANNEX_IV_STRUCTURE_VALID" and missing == []

    # 5. Incomplete Section 1 (missing hardware_requirements)
    broken_s1 = copy.deepcopy(valid_annex_iv)
    broken_s1["section_1_general_description"].pop("hardware_requirements")
    ok, reason, missing = validate_annex_iv_structure(broken_s1)
    assert not ok and reason == "ANNEX_IV_SECTION_1_HARDWARE_REQUIREMENTS_MISSING"

    # 6. Integration with evaluate_claim_node
    target = graph_workspace["target_deployment"]
    root = graph_workspace["root"]
    c_a11 = copy.deepcopy(graph_workspace["claims"][2])  # CLM-A11-DOC

    # With invalid embedded annex_iv -> claim rejected
    c_a11["annex_iv"] = broken_s1
    r_bad = evaluate_claim_node(c_a11, target, root, now=1_800_000_000)
    assert r_bad["accepted"] is False
    assert "ANNEX_IV_SECTION_1_HARDWARE_REQUIREMENTS_MISSING" in r_bad["reasons"]

    # With valid embedded annex_iv -> claim accepted
    c_a11["annex_iv"] = valid_annex_iv
    r_good = evaluate_claim_node(c_a11, target, root, now=1_800_000_000)
    assert r_good["accepted"] is True

    # With validate_annex_iv pointing to evidence file on disk
    ev_a4_path = root / "evidence_annex_iv.json"
    ev_a4_bytes = canonical(valid_annex_iv)
    ev_a4_path.write_bytes(ev_a4_bytes)
    c_a11_file = copy.deepcopy(graph_workspace["claims"][2])
    c_a11_file["claim"]["evidence_path"] = "evidence_annex_iv.json"
    c_a11_file["claim"]["evidence_digest"] = hashlib.sha256(ev_a4_bytes).hexdigest()
    c_a11_file["validate_annex_iv"] = True
    r_file = evaluate_claim_node(c_a11_file, target, root, now=1_800_000_000)
    assert r_file["accepted"] is True


def test_article_9_continuous_risk_management_validation(tmp_path: Path, graph_workspace: dict[str, Any]) -> None:
    """Verify Article 9 continuous risk management lifecycle validation and claim integration."""
    # 1. Non-dict input
    ok, reason, missing = validate_article_9_risk_management("invalid")
    assert not ok and reason == "RISK_MANAGEMENT_NOT_A_DOCUMENT" and len(missing) == len(ARTICLE_9_MANDATORY_PHASES)

    # 2. Schema invalid
    ok, reason, _ = validate_article_9_risk_management({"schema": "wrong"})
    assert not ok and reason == "RISK_MANAGEMENT_SCHEMA_INVALID"

    # 3. Missing phase
    ok, reason, missing = validate_article_9_risk_management(
        {"schema": RISK_MANAGEMENT_SCHEMA, "risk_identification": {"identified_risks": ["r1"]}}
    )
    assert not ok and "RISK_MANAGEMENT_MISSING_PHASES_" in reason and len(missing) == 5

    # 4. Valid document passes
    valid_risk: dict[str, Any] = {
        "schema": RISK_MANAGEMENT_SCHEMA,
        "periodic_review_months": 6,
        "risk_identification": {"identified_risks": [{"risk_id": "R1", "desc": "bias"}]},
        "risk_estimation_and_evaluation": {"methodology": "probabilistic"},
        "post_market_risk_evaluation": {"post_market_data_integrated": True},
        "risk_mitigation_measures": {"mitigations": [{"risk_id": "R1", "mitigation": "filter"}]},
        "testing_and_validation": {
            "predefined_thresholds": {"accuracy": "0.95"},
            "testing_status": "TESTS_PASSED",
        },
        "residual_risk_acceptance": {
            "accountable_owner": "Chief Risk Officer",
            "residual_risk_status": "ACCEPTED",
            "unacceptable_risks_count": 0,
        },
    }
    ok, reason, missing = validate_article_9_risk_management(valid_risk)
    assert ok and reason == "RISK_MANAGEMENT_LIFECYCLE_VALID" and missing == []

    # 5. Invalid periodic review cadence (cadence <= 0)
    bad_cadence = copy.deepcopy(valid_risk)
    bad_cadence["periodic_review_months"] = 0
    ok, reason, missing = validate_article_9_risk_management(bad_cadence)
    assert not ok and reason == "RISK_MANAGEMENT_REVIEW_CADENCE_INVALID"

    # 6. Unacceptable residual risks (> 0) fails closed
    bad_residual = copy.deepcopy(valid_risk)
    bad_residual["residual_risk_acceptance"]["unacceptable_risks_count"] = 1
    ok, reason, missing = validate_article_9_risk_management(bad_residual)
    assert not ok and reason == "RISK_MANAGEMENT_UNACCEPTABLE_RISKS_PRESENT"

    # 7. Integration with evaluate_claim_node
    target = graph_workspace["target_deployment"]
    root = graph_workspace["root"]
    c_a9 = copy.deepcopy(graph_workspace["claims"][0])  # CLM-A9-RISK

    c_a9["risk_management"] = bad_residual
    r_bad = evaluate_claim_node(c_a9, target, root, now=1_800_000_000)
    assert r_bad["accepted"] is False
    assert "RISK_MANAGEMENT_UNACCEPTABLE_RISKS_PRESENT" in r_bad["reasons"]

    c_a9["risk_management"] = valid_risk
    r_good = evaluate_claim_node(c_a9, target, root, now=1_800_000_000)
    assert r_good["accepted"] is True


def test_deployer_fria_sample_bundle_reproducible_and_valid(tmp_path: Path) -> None:
    """Verify reports/babylon_assurance_gateway_deployer_fria_sample.json is reproducible and valid under Art. 27."""
    repo_root = Path(__file__).absolute().parents[1]
    sample_path = repo_root / "reports" / "babylon_assurance_gateway_deployer_fria_sample.json"
    assert sample_path.is_file()

    on_disk = load_json(sample_path)
    regenerated = generate_deployer_fria_sample_bundle(tmp_path / "deployer_bundle")

    assert on_disk == regenerated
    assert on_disk["schema"] == GATEWAY_BUNDLE_SCHEMA
    assert on_disk["eu_ai_act_certified"] is False
    assert on_disk["execution_evidence"]["system_identity"]["operator_role"] == "deployer"
    assert on_disk["execution_evidence"]["system_identity"]["annex_iii_use_case"] == "annex_iii_5b_creditworthiness"
    assert on_disk["assurance_dossier"]["fria_article_27_required"] is True
    assert on_disk["assurance_dossier"]["missing_critical_articles"] == []
    assert on_disk["assurance_dossier"]["critical_checks_missing"] == 0
    assert on_disk["assurance_dossier"]["technical_status"] == "TECHNICAL_EVIDENCE_VALID"
    assert on_disk["assurance_dossier"]["legal_status"] == "LEGAL_REVIEW_REQUIRED"
    assert on_disk["assurance_dossier"]["verdict"] == "SUPPORTED_WITHIN_TESTED_DOMAIN"
    assert on_disk["assurance_dossier"]["fl_aiact_01_v2_gate"]["legitimate_deployment_acceptance"] == 1
    assert on_disk["assurance_dossier"]["fl_aiact_01_v2_gate"]["cross_artifact_evidence_reuse"] == 0
    assert on_disk["assurance_dossier"]["fl_aiact_01_v2_gate"]["stale_critical_evidence_accept"] == 0
    assert on_disk["assurance_dossier"]["fl_aiact_01_v2_gate"]["unauthorized_status_promotions"] == 0
    assert on_disk["assurance_dossier"]["fl_aiact_01_v2_gate"]["undetected_requirement_drift"] == 0
    assert FRIA_SCHEMA == "babylon60.euai.fria.v1"
