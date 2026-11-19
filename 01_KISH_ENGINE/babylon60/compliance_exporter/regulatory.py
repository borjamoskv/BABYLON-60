"""Evidence assessment, distinct from legal conformity and hardware authorization.

Trust is supplied by the operator, never by an evidence bundle. Reviews attest
accountable human acceptance of this precise snapshot, not legal infallibility.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import stat
import time
from pathlib import Path, PurePosixPath
from typing import Any, TypeAlias, cast

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

# JSON documents are the untrusted protocol boundary; fields are checked below.
JSONDocument: TypeAlias = dict[str, Any]

CATALOGUE_PATH = Path(__file__).with_name("regulatory_catalogue.json")
CATALOGUE_BYTES = CATALOGUE_PATH.read_bytes()
CATALOGUE: JSONDocument = json.loads(CATALOGUE_BYTES)
CATALOGUE_DIGEST = hashlib.sha256(CATALOGUE_BYTES).hexdigest()
BLOCKING_IDS = sorted(r["id"] for r in CATALOGUE["requirements"] if r.get("blocking"))
MAX_BYTES = 32 * 1024 * 1024
ROLES = {"provider", "deployer", "importer", "distributor", "representative", "gpai_provider"}


def canonical(value: Any) -> bytes:
    """Protocol JSON excludes floats to keep Python/Rust canonicalization identical."""

    def check(item: Any) -> None:
        if isinstance(item, float):
            raise ValueError("Floating-point values are not allowed in signed metadata")
        if isinstance(item, dict):
            if not all(isinstance(k, str) for k in item):
                raise ValueError("Metadata keys must be strings")
            for child in item.values():
                check(child)
        elif isinstance(item, list):
            for child in item:
                check(child)

    check(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def load_json(path: str | Path) -> JSONDocument:
    def pairs(items: list[tuple[str, Any]]) -> JSONDocument:
        result: JSONDocument = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    with Path(path).open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("JSON document too large")
    value = json.loads(
        data, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Invalid JSON number"))
    )
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object")
    canonical(value)
    return cast(JSONDocument, value)


def evidence_hash(root: Path, relative: str) -> str:
    """Read a regular file without following symlinks, including intermediate dirs."""
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError("Invalid evidence path")
    path = PurePosixPath(relative)
    if path.is_absolute() or any(p in {"", ".", ".."} for p in relative.split("/")):
        raise ValueError("Evidence must be confined to its bundle")
    fd = os.open(root.absolute(), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        file_fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        with os.fdopen(file_fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
                raise ValueError("Evidence must be a bounded regular file")
            data = stream.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise ValueError("Evidence too large")
            return hashlib.sha256(data).hexdigest()
    finally:
        os.close(fd)


def verify_review(record: JSONDocument, policy: JSONDocument, now: int) -> JSONDocument:
    statement = record["statement"]
    reviewer = policy["reviewers"][statement["reviewer"]]
    if reviewer.get("revoked", False) or "assessment" not in reviewer.get("scopes", []):
        raise ValueError("Reviewer is revoked or unauthorized")
    if statement["system_id"] not in reviewer.get("system_ids", []):
        raise ValueError("Reviewer has no authority over this system")
    if type(statement["expires_at"]) is not int or statement["expires_at"] <= now:
        raise ValueError("Review expired")
    if not isinstance(reviewer.get("name"), str) or not reviewer["name"].strip():
        raise ValueError("Reviewer identity missing")
    if digest(record) in policy.get("revoked_reviews", []):
        raise ValueError("Review revoked")
    Ed25519PublicKey.from_public_bytes(bytes.fromhex(reviewer["public_key_hex"])).verify(
        base64.b64decode(record["signature"], validate=True), canonical(statement)
    )
    return cast(JSONDocument, statement)


def _verify_evidence_refs(root: Path, refs: object) -> None:
    """Require a non-empty evidence list whose files match their declared SHA-256 digests."""
    if not isinstance(refs, list) or not refs:
        raise FileNotFoundError("Evidence missing")
    for ref in refs:
        if evidence_hash(root, ref["path"]) != ref["sha256"]:
            raise ValueError("Evidence digest mismatch")


def assess(
    profile: JSONDocument,
    assessment: JSONDocument,
    root: Path,
    policy: JSONDocument,
    *,
    now: int | None = None,
) -> JSONDocument:
    now = int(time.time()) if now is None else now
    errors = []
    required = (
        "system_id",
        "system_version",
        "intended_purpose",
        "context",
        "responsible_entity",
        "classification_reason",
    )
    for name in required:
        if not isinstance(profile.get(name), str) or not profile[name].strip():
            errors.append(f"PROFILE_{name.upper()}_MISSING")
    if not re.fullmatch(r"[0-9a-f]{64}", str(profile.get("configuration_digest", ""))):
        errors.append("PROFILE_CONFIGURATION_DIGEST_INVALID")
    roles = profile.get("roles", [])
    if not isinstance(roles, list) or not roles or any(not isinstance(r, str) or r not in ROLES for r in roles):
        errors.append("PROFILE_ROLES_INVALID")
    classification = profile.get("classification", "unknown")
    if classification not in {"high_risk", "infrastructure", "not_high_risk"}:
        errors.append("CLASSIFICATION_UNRESOLVED")
    if profile.get("schema") != "babylon60.euai.profile.v1":
        errors.append("PROFILE_SCHEMA_INVALID")
    if assessment.get("schema") != "babylon60.euai.assessment.v1":
        errors.append("ASSESSMENT_SCHEMA_INVALID")
    entries = assessment.get("requirements", {})
    if not isinstance(entries, dict):
        entries = {}
        errors.append("ASSESSMENT_REQUIREMENTS_INVALID")
    unknown = set(entries) - {r["id"] for r in CATALOGUE["requirements"]}
    if unknown:
        errors.append("UNKNOWN_REQUIREMENTS")
    results = []
    for requirement in CATALOGUE["requirements"]:
        item = entries.get(requirement["id"], {})
        status, detail = "MISSING", "Evidence and accountable decision required"
        try:
            applicability = item.get("applicability", "unknown")
            if applicability == "not_applicable":
                if classification == "high_risk" and requirement.get("blocking"):
                    raise ValueError("Core high-risk requirement cannot be exempted")
                if not item.get("justification", "").strip():
                    raise ValueError("Non-applicability requires justification")
                status, detail = "NOT_APPLICABLE", item["justification"]
            elif applicability == "applicable":
                _verify_evidence_refs(root, item.get("evidence", []))
                status, detail = "ACCEPTED", "Evidence matches declared snapshot"
            elif item:
                status, detail = "PENDING_REVIEW", "Applicability unresolved"
            if status in {"ACCEPTED", "NOT_APPLICABLE"}:
                if not item.get("owner", "").strip() or item.get("decision") != "accepted":
                    status, detail = "PENDING_REVIEW", "Accountable acceptance required"
        except FileNotFoundError:
            status, detail = "MISSING", "Evidence file missing"
        except (ValueError, KeyError, TypeError, AttributeError, OSError):
            status, detail = "INVALID", "Invalid evidence, applicability or metadata"
        results.append(
            {
                **requirement,
                "source": f"https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-{requirement['article']}",
                "applicability": item.get("applicability", "unknown") if isinstance(item, dict) else "unknown",
                "owner": item.get("owner") if isinstance(item, dict) else None,
                "status": status,
                "detail": detail,
            }
        )
    eligible = (
        not errors
        and classification == "high_risk"
        and all(r["status"] == "ACCEPTED" for r in results if r.get("blocking"))
    )
    record = assessment.get("review", {})
    submitted = record.get("statement", {}) if isinstance(record, dict) else {}
    statement = {
        "schema": "babylon60.euai.review.v1",
        "system_id": profile.get("system_id"),
        "system_version": profile.get("system_version"),
        "classification": classification,
        "profile_digest": digest(profile),
        "assessment_digest": digest({key: value for key, value in assessment.items() if key != "review"}),
        "catalogue_digest": CATALOGUE_DIGEST,
        "requirements_digest": digest(results),
        "blocking_ids": BLOCKING_IDS,
        "gate_eligible": eligible,
        "reviewer": submitted.get("reviewer", ""),
        "expires_at": submitted.get("expires_at", now + 86400),
    }
    review_valid = False
    if record:
        try:
            if verify_review(record, policy, now) != statement:
                raise ValueError("Review is for another snapshot")
            review_valid = True
        except Exception:
            errors.append("REVIEW_INVALID_OR_STALE")
    if not review_valid:
        for result in results:
            if result["status"] in {"ACCEPTED", "NOT_APPLICABLE"}:
                result["status"] = "PENDING_REVIEW"
    return {
        "schema": "babylon60.euai.evaluation.v1",
        "catalogue_version": CATALOGUE["version"],
        "catalogue_digest": CATALOGUE_DIGEST,
        "profile_digest": digest(profile),
        "requirements": results,
        "errors": errors,
        "review_valid": review_valid,
        "review_statement": statement,
        "source_fact_hash": digest(record) if review_valid else None,
        "gate_eligible": eligible and review_valid,
        "blocking_scope": "articles_9_14",
        "regulatory_assessment": "REVIEW_RECORDED" if review_valid else "PENDING_REVIEW",
        "publication_authorized": False,
        "legal_conformity": "NOT_DETERMINED",
        "hardware_status": "NO_VERIFICADO",
        "native_validation_digest": digest(policy.get("native_validation")),
    }


# ---------------------------------------------------------------------------
# FL-AIACT-02: REGULATORY EVIDENCE GRAPH (babylon.assurance.claim.v1)
# ---------------------------------------------------------------------------

CLAIM_SCHEMA = "babylon.assurance.claim.v1"
GRAPH_EVAL_SCHEMA = "babylon.assurance.graph_evaluation.v1"
BINDING_DIMENSIONS = (
    "intended_purpose_id",
    "model_identity",
    "artifact_sha256",
    "runtime_profile_sha256",
    "policy_sha256",
)
CATALOGUE_ARTICLES = {int(r["article"]) for r in CATALOGUE["requirements"]}
FORBIDDEN_AUTO_LEGAL_STATUSES = {"COMPLIANT", "EU_AI_ACT_CERTIFIED", "CERTIFIED", "AUTO_COMPLIANT"}
ALLOWED_LEGAL_STATUSES = {"NOT_ASSESSED", "LEGAL_REVIEW_REQUIRED", "CONFORMITY_DOCUMENTED"}
ALLOWED_TECHNICAL_STATUSES = {"PASS", "FAIL", "UNTESTED", "EVIDENCE_INCOMPLETE", "TECHNICAL_EVIDENCE_VALID"}
FRIA_DEPLOYER_CATEGORIES = {"public_body", "private_public_service_operator"}
FRIA_ANNEX_III_USE_CASES = {
    "annex_iii_5b_creditworthiness",
    "annex_iii_5c_life_health_insurance",
}

ANNEX_IV_SCHEMA = "babylon60.euai.annex_iv.v1"
RISK_MANAGEMENT_SCHEMA = "babylon60.euai.risk_management.v1"
FRIA_SCHEMA = "babylon60.euai.fria.v1"

ANNEX_IV_MANDATORY_SECTIONS = (
    "section_1_general_description",
    "section_2_development_process",
    "section_3_monitoring_and_control",
    "section_4_risk_management",
    "section_5_change_log",
    "section_6_standards",
    "section_7_declaration_of_conformity",
    "section_8_post_market_monitoring",
)

ARTICLE_9_MANDATORY_PHASES = (
    "risk_identification",
    "risk_estimation_and_evaluation",
    "post_market_risk_evaluation",
    "risk_mitigation_measures",
    "testing_and_validation",
    "residual_risk_acceptance",
)


def requires_fria_article_27(system: JSONDocument) -> bool:
    """Determine if Fundamental Rights Impact Assessment (Art. 27) is mandatory for this deployment.

    Per Art. 27(1) of Regulation (EU) 2024/1689, FRIA applies to deployers that are bodies
    governed by public law, private entities providing public services, or deployers of
    high-risk systems under Annex III point 5(b) (creditworthiness) or 5(c) (life/health insurance).
    """
    if not isinstance(system, dict):
        return False
    if system.get("requires_fria_art27") is True:
        return True
    if system.get("operator_role") != "deployer":
        return False
    return (
        system.get("deployer_category") in FRIA_DEPLOYER_CATEGORIES
        or system.get("annex_iii_use_case") in FRIA_ANNEX_III_USE_CASES
    )


RETENTION_RULES: dict[str, dict[str, Any]] = {
    "provider_technical_documentation": {
        "article": 18,
        "min_months": 120,  # 10 years per Art. 18
        "allow_raw_personal_data_on_ledger": False,
        "require_salted_commitment_for_pii": True,
    },
    "operational_event_logs": {
        "article": 26,
        "min_months": 6,  # >= 6 months per Arts. 19 / 26.6
        "allow_raw_personal_data_on_ledger": False,
        "require_salted_commitment_for_pii": True,
    },
    "gdpr_personal_or_prompt_data": {
        "article": 12,
        "min_months": 0,  # GDPR Art. 5(1)(e) storage limitation & Art. 17 erasure
        "allow_raw_personal_data_on_ledger": False,
        "require_salted_commitment_for_pii": True,
        "require_off_ledger_erasable_store": True,
    },
}


def validate_model_identity(system: JSONDocument) -> tuple[bool, str, bool]:
    """Validate model_identity and enforce explicit uncertainty for non-hashable external models.

    Returns (valid, reason_code, is_external_opaque_model).
    """
    raw_id = system.get("model_identity")
    if not isinstance(raw_id, str) or not raw_id.strip():
        return False, "MODEL_IDENTITY_MISSING", False

    # Case 1: Deterministically verifiable weights digest ("sha256:<64-hex>")
    if raw_id.startswith("sha256:"):
        digest_part = raw_id[len("sha256:") :]
        if re.fullmatch(r"[0-9a-f]{64}", digest_part):
            return True, "VERIFIABLE_WEIGHTS_DIGEST", False
        return False, "MODEL_WEIGHTS_DIGEST_INVALID", False

    # Case 2: External / closed model ("provider:model:version")
    parts = [p.strip() for p in raw_id.split(":")]
    if len(parts) != 3 or any(not p or p == "unknown" for p in parts):
        return False, "MODEL_IDENTITY_UNVERIFIABLE_FORMAT", True

    if system.get("model_uncertainty_declared") is not True:
        return False, "MODEL_UNCERTAINTY_NOT_DECLARED", True
    containment = system.get("containment_policy", "")
    if not isinstance(containment, str) or not containment.strip():
        return False, "MODEL_CONTAINMENT_POLICY_MISSING", True

    return True, "EXTERNAL_MODEL_WITH_DECLARED_UNCERTAINTY", True


def validate_retention_policy(retention: JSONDocument | None) -> tuple[bool, str]:
    """Enforce differential retention under AI Act Art. 18 (10y), Art. 26.6 (6m), and GDPR."""
    if retention is None:
        return True, "DEFAULT_RETENTION_UNSPECIFIED"
    if not isinstance(retention, dict):
        return False, "RETENTION_POLICY_INVALID"

    data_class = retention.get("data_class", "")
    if data_class not in RETENTION_RULES:
        return False, "RETENTION_DATA_CLASS_UNKNOWN"

    rule = RETENTION_RULES[data_class]
    months = retention.get("retention_months")
    if type(months) is not int or months < rule["min_months"]:
        return False, f"RETENTION_BELOW_STATUTORY_MINIMUM_ART_{rule['article']}"

    if retention.get("raw_personal_data_on_immutable_ledger") is True:
        return False, "GDPR_IMMUTABLE_LEDGER_RAW_PII_FORBIDDEN"

    if retention.get("contains_personal_data") is True:
        if retention.get("unsalted_pii_hash_on_ledger") is True:
            return False, "EDPB_UNSALTED_PII_HASH_ON_LEDGER_FORBIDDEN"
        if retention.get("commitment_scheme") != "BLAKE3_DERIVE_KEY_SALTED":
            return False, "GDPR_SALTED_COMMITMENT_REQUIRED"
        if retention.get("off_ledger_erasable_store") is not True:
            return False, "GDPR_OFF_LEDGER_ERASABLE_STORE_REQUIRED"

    return True, "RETENTION_COMPLIANT_WITH_STATUTORY_BOUNDS"


def validate_annex_iv_structure(doc: Any) -> tuple[bool, str, list[str]]:
    """Validate completeness and structure of EU AI Act Annex IV technical documentation.

    Regulation (EU) 2024/1689 Annex IV requirements:
      - Section 1: General description of the AI system
      - Section 2: Detailed description of elements and development process (data, oversight, testing)
      - Section 3: Monitoring, functioning and control (capabilities, limitations, cybersecurity)
      - Section 4: Risk management system (Article 9 reference/implementation)
      - Section 5: Changes to the system through its lifecycle
      - Section 6: Harmonised standards / common specifications (Articles 40, 41)
      - Section 7: EU declaration of conformity (Article 47)
      - Section 8: Post-market monitoring system (Article 72)
    """
    if not isinstance(doc, dict):
        return False, "ANNEX_IV_NOT_A_DOCUMENT", list(ANNEX_IV_MANDATORY_SECTIONS)

    if doc.get("schema") != ANNEX_IV_SCHEMA:
        return False, "ANNEX_IV_SCHEMA_INVALID", []

    missing_sections: list[str] = []
    for sec in ANNEX_IV_MANDATORY_SECTIONS:
        val = doc.get(sec)
        if not isinstance(val, dict) or not val:
            missing_sections.append(sec)

    if missing_sections:
        return False, f"ANNEX_IV_MISSING_SECTIONS_{len(missing_sections)}", missing_sections

    # Section 1 validation
    s1 = doc["section_1_general_description"]
    if not isinstance(s1.get("intended_purpose"), str) or not s1["intended_purpose"].strip():
        return False, "ANNEX_IV_SECTION_1_INTENDED_PURPOSE_MISSING", ["intended_purpose"]
    if not isinstance(s1.get("system_version"), str) or not s1["system_version"].strip():
        return False, "ANNEX_IV_SECTION_1_SYSTEM_VERSION_MISSING", ["system_version"]
    if not s1.get("hardware_requirements"):
        return False, "ANNEX_IV_SECTION_1_HARDWARE_REQUIREMENTS_MISSING", ["hardware_requirements"]

    # Section 2 validation
    s2 = doc["section_2_development_process"]
    if not isinstance(s2.get("data_governance"), dict) or not s2["data_governance"]:
        return False, "ANNEX_IV_SECTION_2_DATA_GOVERNANCE_MISSING", ["data_governance"]
    if not s2.get("human_oversight"):
        return False, "ANNEX_IV_SECTION_2_HUMAN_OVERSIGHT_MISSING", ["human_oversight"]
    if not isinstance(s2.get("validation_and_testing"), dict) or not s2["validation_and_testing"]:
        return False, "ANNEX_IV_SECTION_2_VALIDATION_AND_TESTING_MISSING", ["validation_and_testing"]

    # Section 3 validation
    s3 = doc["section_3_monitoring_and_control"]
    if not s3.get("capabilities_and_limitations"):
        return False, "ANNEX_IV_SECTION_3_CAPABILITIES_LIMITATIONS_MISSING", ["capabilities_and_limitations"]
    if not s3.get("cybersecurity_measures"):
        return False, "ANNEX_IV_SECTION_3_CYBERSECURITY_MISSING", ["cybersecurity_measures"]

    # Section 4 validation
    s4 = doc["section_4_risk_management"]
    if not s4.get("risk_management_system"):
        return False, "ANNEX_IV_SECTION_4_RISK_SYSTEM_MISSING", ["risk_management_system"]

    # Section 8 validation
    s8 = doc["section_8_post_market_monitoring"]
    if not s8.get("post_market_monitoring_plan"):
        return False, "ANNEX_IV_SECTION_8_MONITORING_PLAN_MISSING", ["post_market_monitoring_plan"]

    return True, "ANNEX_IV_STRUCTURE_VALID", []


def validate_article_9_risk_management(doc: Any) -> tuple[bool, str, list[str]]:
    """Validate continuous risk management lifecycle under EU AI Act Article 9.

    Article 9 requirements:
      - Continuous, iterative process planned and run throughout entire lifecycle
      - 1. Identification and analysis of known and foreseeable risks (health, safety, fundamental rights)
      - 2. Estimation and evaluation of risks under intended use and foreseeable misuse
      - 3. Evaluation of risks emerging from post-market monitoring data (Art. 72)
      - 4. Adoption of suitable risk mitigation/control measures (inherent safety, mitigations, training)
      - 5. Testing with predefined metrics and probabilistic thresholds (including vulnerable groups)
      - 6. Residual risk evaluation and accountable acceptance by designated authority
      - Review schedule: explicit continuous review cadence in months
    """
    if not isinstance(doc, dict):
        return False, "RISK_MANAGEMENT_NOT_A_DOCUMENT", list(ARTICLE_9_MANDATORY_PHASES)

    if doc.get("schema") != RISK_MANAGEMENT_SCHEMA:
        return False, "RISK_MANAGEMENT_SCHEMA_INVALID", []

    missing_phases: list[str] = []
    for phase in ARTICLE_9_MANDATORY_PHASES:
        val = doc.get(phase)
        if not isinstance(val, dict) or not val:
            missing_phases.append(phase)

    if missing_phases:
        return False, f"RISK_MANAGEMENT_MISSING_PHASES_{len(missing_phases)}", missing_phases

    # Continuous lifecycle review cadence
    cadence = doc.get("periodic_review_months")
    if type(cadence) is not int or cadence <= 0:
        return False, "RISK_MANAGEMENT_REVIEW_CADENCE_INVALID", ["periodic_review_months"]

    # Phase 1: Identification
    p1 = doc["risk_identification"]
    risks = p1.get("identified_risks")
    if not isinstance(risks, list) or not risks:
        return False, "RISK_MANAGEMENT_IDENTIFIED_RISKS_EMPTY", ["identified_risks"]

    # Phase 4: Mitigations
    p4 = doc["risk_mitigation_measures"]
    mitigations = p4.get("mitigations")
    if not isinstance(mitigations, list) or not mitigations:
        return False, "RISK_MANAGEMENT_MITIGATIONS_EMPTY", ["mitigations"]

    # Phase 5: Testing
    p5 = doc["testing_and_validation"]
    thresholds = p5.get("predefined_thresholds")
    if not isinstance(thresholds, (dict, list)) or not thresholds:
        return False, "RISK_MANAGEMENT_THRESHOLDS_MISSING", ["predefined_thresholds"]
    if p5.get("testing_status") not in {"TESTS_PASSED", "PASS"}:
        return False, "RISK_MANAGEMENT_TESTING_NOT_PASSED", ["testing_status"]

    # Phase 6: Residual Risk Acceptance
    p6 = doc["residual_risk_acceptance"]
    owner = p6.get("accountable_owner")
    if not isinstance(owner, str) or not owner.strip():
        return False, "RISK_MANAGEMENT_ACCOUNTABLE_OWNER_MISSING", ["accountable_owner"]
    if p6.get("residual_risk_status") != "ACCEPTED":
        return False, "RISK_MANAGEMENT_RESIDUAL_RISK_NOT_ACCEPTED", ["residual_risk_status"]
    unacceptable = p6.get("unacceptable_risks_count")
    if type(unacceptable) is not int or unacceptable != 0:
        return False, "RISK_MANAGEMENT_UNACCEPTABLE_RISKS_PRESENT", ["unacceptable_risks_count"]

    return True, "RISK_MANAGEMENT_LIFECYCLE_VALID", []


def classify_system_change(
    baseline_system: JSONDocument,
    target_system: JSONDocument,
    *,
    predetermined_envelopes: list[JSONDocument] | None = None,
    post_market_incidents: list[JSONDocument] | None = None,
) -> JSONDocument:
    """Classify changes between evaluated baseline and deployed target (Art. 43 vs Art. 43.4).

    Distinguishes:
      - NO_CHANGE
      - WITHIN_PREDETERMINED_ENVELOPE (Art. 43.4: documented parameter change, no automatic Art. 43 reset)
      - SELECTIVE_TECHNICAL_REVALIDATION (localized technical change invalidating only bound claims)
      - SUBSTANTIAL_MODIFICATION_REVIEW_REQUIRED (Art. 43 / Art. 3.23: intended purpose, role, or unplanned core shift)
      - POST_MARKET_INCIDENT_REVIEW_REQUIRED (Art. 72 / Art. 73: serious incident linked to deployment)
    """
    changed_dimensions: list[str] = []
    for dim in BINDING_DIMENSIONS:
        if baseline_system.get(dim) != target_system.get(dim):
            changed_dimensions.append(dim)

    role_changed = baseline_system.get("operator_role") != target_system.get("operator_role")
    incidents = [inc for inc in (post_market_incidents or []) if isinstance(inc, dict)]

    if incidents:
        return {
            "classification": "POST_MARKET_INCIDENT_REVIEW_REQUIRED",
            "changed_dimensions": changed_dimensions,
            "requires_substantial_modification_assessment": True,
            "requires_post_market_corrective_action": True,
            "incident_count": len(incidents),
        }

    if "intended_purpose_id" in changed_dimensions or role_changed:
        return {
            "classification": "SUBSTANTIAL_MODIFICATION_REVIEW_REQUIRED",
            "changed_dimensions": changed_dimensions + (["operator_role"] if role_changed else []),
            "requires_substantial_modification_assessment": True,
            "requires_post_market_corrective_action": False,
            "incident_count": 0,
        }

    if not changed_dimensions:
        return {
            "classification": "NO_CHANGE",
            "changed_dimensions": [],
            "requires_substantial_modification_assessment": False,
            "requires_post_market_corrective_action": False,
            "incident_count": 0,
        }

    # Check if all changed dimensions are covered by Art. 43.4 predetermined change envelopes
    envelopes = predetermined_envelopes or []
    covered_by_envelope = True
    requires_retest = False
    for dim in changed_dimensions:
        new_val = target_system.get(dim)
        matched = [
            env
            for env in envelopes
            if isinstance(env, dict) and env.get("dimension") == dim and new_val in env.get("allowed_values", [])
        ]
        if not matched:
            covered_by_envelope = False
            break
        if any(env.get("requires_technical_retest", False) for env in matched):
            requires_retest = True

    if covered_by_envelope:
        return {
            "classification": "WITHIN_PREDETERMINED_ENVELOPE",
            "changed_dimensions": changed_dimensions,
            "requires_substantial_modification_assessment": False,
            "requires_selective_technical_retest": requires_retest,
            "requires_post_market_corrective_action": False,
            "incident_count": 0,
        }

    return {
        "classification": "SELECTIVE_TECHNICAL_REVALIDATION",
        "changed_dimensions": changed_dimensions,
        "requires_substantial_modification_assessment": False,
        "requires_selective_technical_retest": True,
        "requires_post_market_corrective_action": False,
        "incident_count": 0,
    }


def evaluate_claim_node(
    claim_node: JSONDocument,
    target_deployment: JSONDocument,
    root: Path,
    *,
    policy: JSONDocument | None = None,
    predetermined_envelopes: list[JSONDocument] | None = None,
    now: int | None = None,
) -> JSONDocument:
    """Evaluate a single `babylon.assurance.claim.v1` node in the Regulatory Evidence Graph.

    Enforces:
      1. AcceptEvidence(c, a) => Bound(c, a) & Applicable(c, a) & Verified(c)
      2. TechnicalPASS !=> LegalConformity
    """
    now = int(time.time()) if now is None else now
    reasons: list[str] = []

    if claim_node.get("schema") != CLAIM_SCHEMA:
        reasons.append("CLAIM_SCHEMA_INVALID")

    legal = claim_node.get("legal", {})
    system = claim_node.get("system", {})
    claim = claim_node.get("claim", {})
    evaluation = claim_node.get("evaluation", {})
    review = claim_node.get("review", {})
    target_sys = target_deployment.get("system", {})

    if not all(isinstance(x, dict) for x in (legal, system, claim, evaluation, review, target_sys)):
        return {
            "claim_id": claim_node.get("claim_id", "unknown"),
            "bound": False,
            "applicable": False,
            "verified": False,
            "accepted": False,
            "technical_status": "EVIDENCE_INCOMPLETE",
            "legal_status": "LEGAL_REVIEW_REQUIRED",
            "reasons": ["MALFORMED_CLAIM_STRUCTURE"],
        }

    # --- 1. APPLICABLE(c, a) ---
    applicable = True
    if legal.get("jurisdiction") != "EU" or legal.get("regulation") != "2024/1689":
        applicable = False
        reasons.append("LEGAL_REGULATION_MISMATCH")
    if legal.get("consolidated_at") != "2026-07-27":
        applicable = False
        reasons.append("LEGAL_CONSOLIDATION_DATE_MISMATCH")
    article = legal.get("article")
    if type(article) is not int or article not in CATALOGUE_ARTICLES:
        applicable = False
        reasons.append("LEGAL_ARTICLE_UNKNOWN")
    role = legal.get("operator_role")
    if not isinstance(role, str) or role not in ROLES:
        applicable = False
        reasons.append("OPERATOR_ROLE_INVALID")
    if target_sys.get("operator_role") and role != target_sys.get("operator_role"):
        applicable = False
        reasons.append("OPERATOR_ROLE_MISMATCH")
    if article == 27 and legal.get("applicability") == "not_applicable" and requires_fria_article_27(target_sys):
        applicable = False
        reasons.append("ART_27_FRIA_MANDATORY_FOR_DEPLOYER_PROFILE")
    if legal.get("applicability") not in {"applicable", "pending_review"}:
        applicable = False
        reasons.append("APPLICABILITY_STATE_INVALID")

    declared_cat_digest = legal.get("catalogue_digest")
    if declared_cat_digest is not None and declared_cat_digest != CATALOGUE_DIGEST:
        applicable = False
        reasons.append("REQUIREMENT_CATALOGUE_DIGEST_DRIFT")

    eval_prof_digest = legal.get("evaluation_profile_digest")
    if eval_prof_digest is not None:
        if not re.fullmatch(r"[0-9a-f]{64}", str(eval_prof_digest)):
            applicable = False
            reasons.append("EVALUATION_PROFILE_DIGEST_INVALID")
        else:
            expected_prof = target_deployment.get("evaluation_profile_digest") or target_sys.get(
                "evaluation_profile_digest"
            )
            if expected_prof is not None and eval_prof_digest != expected_prof:
                applicable = False
                reasons.append("EVALUATION_PROFILE_DIGEST_DRIFT")

    ret_ok, ret_reason = validate_retention_policy(claim_node.get("retention"))
    if not ret_ok:
        applicable = False
        reasons.append(ret_reason)

    model_ok, model_reason, _ = validate_model_identity(target_sys)
    bound_dims_raw = claim_node.get("bound_dimensions", list(BINDING_DIMENSIONS))
    if (
        not isinstance(bound_dims_raw, list)
        or not bound_dims_raw
        or any(not isinstance(d, str) or d not in BINDING_DIMENSIONS for d in bound_dims_raw)
    ):
        bound_dims: tuple[str, ...] = BINDING_DIMENSIONS
        applicable = False
        reasons.append("BOUND_DIMENSIONS_INVALID")
    else:
        bound_dims = tuple(bound_dims_raw)

    if "model_identity" in bound_dims and not model_ok:
        applicable = False
        reasons.append(model_reason)

    # --- 2. BOUND(c, a) (with selective dimension binding & Art. 43.4 envelopes) ---
    bound = True
    envelopes = predetermined_envelopes or []
    for dim in bound_dims:
        c_val = system.get(dim)
        t_val = target_sys.get(dim)
        if not isinstance(c_val, str) or not c_val.strip() or not isinstance(t_val, str) or not t_val.strip():
            bound = False
            reasons.append(f"DIMENSION_{dim.upper()}_MISSING")
            continue
        if dim.endswith("_sha256") and (
            not re.fullmatch(r"[0-9a-f]{64}", c_val) or not re.fullmatch(r"[0-9a-f]{64}", t_val)
        ):
            bound = False
            reasons.append(f"DIMENSION_{dim.upper()}_INVALID_DIGEST")
            continue
        if c_val != t_val:
            # Check if an Art. 43.4 predetermined change envelope explicitly authorizes this transition without retest
            allowed_without_retest = any(
                isinstance(env, dict)
                and env.get("dimension") == dim
                and c_val in env.get("baseline_values", [c_val])
                and t_val in env.get("allowed_values", [])
                and env.get("requires_technical_retest", True) is False
                for env in envelopes
            )
            if not allowed_without_retest:
                bound = False
                reasons.append(f"BOUND_MISMATCH_{dim.upper()}")

    # --- 3. VERIFIED(c) ---
    verified = True
    predicate = claim.get("predicate", "")
    scope = claim.get("scope", "")
    ev_path = claim.get("evidence_path", "")
    ev_digest = claim.get("evidence_digest", "")
    verdict = claim.get("verdict", "")

    if not isinstance(predicate, str) or not predicate.strip():
        verified = False
        reasons.append("CLAIM_PREDICATE_MISSING")
    if not isinstance(scope, str) or not scope.strip():
        verified = False
        reasons.append("CLAIM_SCOPE_MISSING")
    if verdict != "SUPPORTED_WITHIN_DOMAIN":
        verified = False
        reasons.append("CLAIM_VERDICT_NOT_SUPPORTED_WITHIN_DOMAIN")
    if not re.fullmatch(r"[0-9a-f]{64}", str(ev_digest)):
        verified = False
        reasons.append("EVIDENCE_DIGEST_INVALID")
    elif not isinstance(ev_path, str) or not ev_path.strip():
        verified = False
        reasons.append("EVIDENCE_PATH_MISSING")
    else:
        try:
            if evidence_hash(root, ev_path) != ev_digest:
                verified = False
                reasons.append("EVIDENCE_HASH_MISMATCH")
        except Exception:
            verified = False
            reasons.append("EVIDENCE_FILE_UNREADABLE_OR_ESCAPED")

    suite_digest = evaluation.get("test_suite_digest", "")
    if not re.fullmatch(r"[0-9a-f]{64}", str(suite_digest)):
        verified = False
        reasons.append("TEST_SUITE_DIGEST_INVALID")
    if evaluation.get("independent_witness") is not True:
        verified = False
        reasons.append("INDEPENDENT_WITNESS_REQUIRED")
    if type(evaluation.get("unresolved_findings")) is not int or evaluation.get("unresolved_findings") != 0:
        verified = False
        reasons.append("UNRESOLVED_FINDINGS_PRESENT")
    ev_expires_at = evaluation.get("expires_at", claim.get("expires_at"))
    if ev_expires_at is not None:
        if type(ev_expires_at) is not int:
            verified = False
            reasons.append("EVIDENCE_EXPIRES_AT_INVALID")
        elif ev_expires_at <= now:
            verified = False
            reasons.append("EVIDENCE_EXPIRED")
    if review.get("technical_status") != "PASS":
        verified = False
        reasons.append("TECHNICAL_STATUS_NOT_PASS")

    # Annex IV structural validation hook (Article 11)
    annex_iv_block = claim_node.get("annex_iv")
    if annex_iv_block is not None:
        a4_ok, a4_reason, _ = validate_annex_iv_structure(annex_iv_block)
        if not a4_ok:
            verified = False
            reasons.append(a4_reason)
    elif claim_node.get("validate_annex_iv") is True or claim_node.get("validate_annex_iv_evidence") is True:
        try:
            ev_full_path = root / ev_path
            with ev_full_path.open("rb") as f:
                ev_data = json.loads(f.read().decode("utf-8"))
            a4_ok, a4_reason, _ = validate_annex_iv_structure(ev_data)
            if not a4_ok:
                verified = False
                reasons.append(a4_reason)
        except Exception:
            verified = False
            reasons.append("ANNEX_IV_EVIDENCE_UNREADABLE")

    # Article 9 continuous risk management lifecycle validation hook
    risk_mgmt_block = claim_node.get("risk_management")
    if risk_mgmt_block is not None:
        r9_ok, r9_reason, _ = validate_article_9_risk_management(risk_mgmt_block)
        if not r9_ok:
            verified = False
            reasons.append(r9_reason)
    elif (
        claim_node.get("validate_risk_management") is True
        or claim_node.get("validate_risk_management_evidence") is True
    ):
        try:
            ev_full_path = root / ev_path
            with ev_full_path.open("rb") as f:
                ev_data = json.loads(f.read().decode("utf-8"))
            r9_ok, r9_reason, _ = validate_article_9_risk_management(ev_data)
            if not r9_ok:
                verified = False
                reasons.append(r9_reason)
        except Exception:
            verified = False
            reasons.append("RISK_MANAGEMENT_EVIDENCE_UNREADABLE")

    # --- 4. SEPARATION INVARIANT: TechnicalPASS !=> LegalConformity ---
    requested_legal = review.get("legal_status", "NOT_ASSESSED")
    if requested_legal in FORBIDDEN_AUTO_LEGAL_STATUSES or claim_node.get("auto_promote_legal") is True:
        verified = False
        reasons.append("ILLEGAL_AUTOMATIC_LEGAL_CONFORMITY_CLAIM")
        legal_status = "LEGAL_REVIEW_REQUIRED"
    elif requested_legal == "CONFORMITY_DOCUMENTED":
        # Requires accountable human Ed25519 signature over the exact claim digest
        sig_record = review.get("human_review_record")
        if not isinstance(sig_record, dict) or not isinstance(policy, dict):
            verified = False
            reasons.append("UNAUTHENTICATED_LEGAL_CONFORMITY_DOCUMENTED")
            legal_status = "LEGAL_REVIEW_REQUIRED"
        else:
            try:
                stmt = verify_review(sig_record, policy, now)
                expected_claim_digest = digest({k: v for k, v in claim_node.items() if k != "review"})
                if stmt.get("claim_digest") != expected_claim_digest:
                    raise ValueError("Review signature bound to different claim")
                legal_status = "CONFORMITY_DOCUMENTED"
            except Exception:
                verified = False
                reasons.append("HUMAN_LEGAL_REVIEW_SIGNATURE_INVALID")
                legal_status = "LEGAL_REVIEW_REQUIRED"
    elif requested_legal in {"NOT_ASSESSED", "LEGAL_REVIEW_REQUIRED"}:
        legal_status = requested_legal
    else:
        verified = False
        reasons.append("UNKNOWN_LEGAL_STATUS")
        legal_status = "LEGAL_REVIEW_REQUIRED"

    accepted = bound and applicable and verified
    technical_status = "TECHNICAL_EVIDENCE_VALID" if accepted else "EVIDENCE_INCOMPLETE"

    return {
        "claim_id": claim_node.get("claim_id", "unknown"),
        "article": article,
        "bound_dimensions": list(bound_dims),
        "bound": bound,
        "applicable": applicable,
        "verified": verified,
        "accepted": accepted,
        "verdict": "SUPPORTED_WITHIN_TESTED_DOMAIN" if accepted else "REJECTED_OR_INCOMPLETE",
        "technical_status": technical_status,
        "legal_status": legal_status,
        "reasons": reasons,
    }


def evaluate_evidence_graph(
    claims: list[JSONDocument],
    target_deployment: JSONDocument,
    root: Path,
    *,
    baseline_system: JSONDocument | None = None,
    required_articles: set[int] | None = None,
    policy: JSONDocument | None = None,
    predetermined_envelopes: list[JSONDocument] | None = None,
    post_market_incidents: list[JSONDocument] | None = None,
    now: int | None = None,
) -> JSONDocument:
    """Evaluate a complete Regulatory Evidence Graph for FL-AIACT-02.

    Supports selective invalidation: orthogonal claims not bound to a mutated dimension
    remain accepted (`accepted == True`), while claims bound to a mutated dimension are
    deterministically rejected unless re-verified or covered by an Art. 43.4 envelope.
    """
    now = int(time.time()) if now is None else now
    target_sys = target_deployment.get("system", {})
    fria_required = requires_fria_article_27(target_sys)
    if required_articles is None:
        req_articles = {9, 10, 11, 12, 13, 14, 15}
        if fria_required:
            req_articles.add(27)
    else:
        req_articles = set(required_articles)
    base_sys = target_sys if baseline_system is None else baseline_system

    change_report = classify_system_change(
        base_sys,
        target_sys,
        predetermined_envelopes=predetermined_envelopes,
        post_market_incidents=post_market_incidents,
    )

    node_results = [
        evaluate_claim_node(
            c,
            target_deployment,
            root,
            policy=policy,
            predetermined_envelopes=predetermined_envelopes,
            now=now,
        )
        for c in claims
    ]

    accepted_ids = [n["claim_id"] for n in node_results if n["accepted"]]
    rejected_ids = [n["claim_id"] for n in node_results if not n["accepted"]]
    covered_articles = {n["article"] for n in node_results if n["accepted"] and isinstance(n["article"], int)}
    missing_critical_articles = sorted(req_articles - covered_articles)

    all_nodes_accepted = bool(node_results) and len(rejected_ids) == 0 and not missing_critical_articles
    substantial_mod = change_report["requires_substantial_modification_assessment"]

    if all_nodes_accepted and not substantial_mod:
        overall_technical_status = "TECHNICAL_EVIDENCE_VALID"
        overall_verdict = "SUPPORTED_WITHIN_TESTED_DOMAIN"
    else:
        overall_technical_status = "EVIDENCE_INCOMPLETE"
        overall_verdict = "REQUIRES_REVERIFICATION_OR_REVIEW"

    # Never emit EU_AI_ACT_CERTIFIED or automatic COMPLIANT
    if (
        all_nodes_accepted
        and not substantial_mod
        and all(n["legal_status"] == "CONFORMITY_DOCUMENTED" for n in node_results)
    ):
        overall_legal_status = "CONFORMITY_DOCUMENTED"
    else:
        overall_legal_status = "LEGAL_REVIEW_REQUIRED"

    drift_reasons = {
        "REQUIREMENT_CATALOGUE_DIGEST_DRIFT",
        "EVALUATION_PROFILE_DIGEST_DRIFT",
        "EVALUATION_PROFILE_DIGEST_INVALID",
    }
    promo_reasons = {
        "ILLEGAL_AUTOMATIC_LEGAL_CONFORMITY_CLAIM",
        "UNAUTHENTICATED_LEGAL_CONFORMITY_DOCUMENTED",
        "HUMAN_LEGAL_REVIEW_SIGNATURE_INVALID",
    }
    stale_reasons = {"EVIDENCE_EXPIRED", "EVIDENCE_EXPIRES_AT_INVALID", "EVIDENCE_HASH_MISMATCH"}

    cross_artifact_evidence_reuse = sum(1 for n in node_results if n["accepted"] and not n["bound"])
    stale_critical_evidence_accept = sum(
        1 for n in node_results if n["accepted"] and (not n["bound"] or bool(set(n["reasons"]) & stale_reasons))
    )
    unauthorized_status_promotions = sum(
        1
        for n in node_results
        if n["legal_status"] in FORBIDDEN_AUTO_LEGAL_STATUSES
        or (n["legal_status"] == "CONFORMITY_DOCUMENTED" and bool(set(n["reasons"]) & promo_reasons))
    )
    undetected_requirement_drift = sum(
        1 for n in node_results if n["accepted"] and bool(set(n["reasons"]) & drift_reasons)
    )
    unauthorized_deployment_effects = 0

    fl_aiact_01_v2_gate: JSONDocument = {
        "cross_artifact_evidence_reuse": cross_artifact_evidence_reuse,
        "stale_critical_evidence_accept": stale_critical_evidence_accept,
        "unauthorized_status_promotions": unauthorized_status_promotions,
        "undetected_requirement_drift": undetected_requirement_drift,
        "unauthorized_deployment_effects": unauthorized_deployment_effects,
        "blocked_cross_artifact_or_unbound": sum(1 for n in node_results if not n["bound"]),
        "blocked_stale_or_expired_evidence": sum(1 for n in node_results if bool(set(n["reasons"]) & stale_reasons)),
        "blocked_unauthorized_promotions": sum(1 for n in node_results if bool(set(n["reasons"]) & promo_reasons)),
        "blocked_requirement_drift": sum(1 for n in node_results if bool(set(n["reasons"]) & drift_reasons)),
        "legitimate_deployment_acceptance": 1 if overall_technical_status == "TECHNICAL_EVIDENCE_VALID" else 0,
        "review_required_claims": sum(1 for n in node_results if n["legal_status"] != "CONFORMITY_DOCUMENTED"),
        "total_claims_evaluated": len(node_results),
        "audit_reconstruction_completeness_bps": (
            10000
            if (bool(node_results) and all_nodes_accepted)
            else (len(accepted_ids) * 10000 // len(node_results) if node_results else 0)
        ),
    }

    return {
        "schema": GRAPH_EVAL_SCHEMA,
        "catalogue_digest": CATALOGUE_DIGEST,
        "fria_article_27_required": fria_required,
        "change_classification": change_report,
        "nodes": node_results,
        "accepted_claim_ids": accepted_ids,
        "rejected_claim_ids": rejected_ids,
        "missing_critical_articles": missing_critical_articles,
        "critical_checks_missing": len(missing_critical_articles),
        "stale_or_invalid_claims_rejected": len(rejected_ids),
        "fl_aiact_01_v2_gate": fl_aiact_01_v2_gate,
        "technical_status": overall_technical_status,
        "legal_status": overall_legal_status,
        "verdict": overall_verdict,
        "eu_ai_act_certified": False,
    }


GATEWAY_BUNDLE_SCHEMA = "babylon.assurance.gateway_bundle.v1"


def export_assurance_gateway_bundle(
    claims: list[JSONDocument],
    target_deployment: JSONDocument,
    root: Path,
    *,
    baseline_system: JSONDocument | None = None,
    required_articles: set[int] | None = None,
    policy: JSONDocument | None = None,
    predetermined_envelopes: list[JSONDocument] | None = None,
    post_market_incidents: list[JSONDocument] | None = None,
    now: int | None = None,
) -> JSONDocument:
    """Compile the three BABYLON Assurance Gateway deliverables from a Regulatory Evidence Graph.

    Produces:
      1. execution_evidence: verified receipts, artifact/runtime/policy/model identities,
         and statutory retention bounds (Art. 18 10y, Art. 26.6 >= 6m, GDPR salted commitments).
      2. assurance_dossier: claims mapped to EU AI Act obligations (Regulation (EU) 2024/1689
         as amended by Regulation (EU) 2026/1744), missing critical articles, and explicit
         technical vs. legal review status (`eu_ai_act_certified: False`).
      3. continuous_evidence_monitoring: change classification (Art. 43 vs Art. 43.4),
         stale/invalidated claims requiring re-verification, preserved orthogonal claims,
         and post-market incident triggers (Art. 72 / Art. 73).
    """
    graph_eval = evaluate_evidence_graph(
        claims,
        target_deployment,
        root,
        baseline_system=baseline_system,
        required_articles=required_articles,
        policy=policy,
        predetermined_envelopes=predetermined_envelopes,
        post_market_incidents=post_market_incidents,
        now=now,
    )

    target_sys = target_deployment.get("system", {})
    model_ok, model_reason, is_external_model = validate_model_identity(target_sys)

    receipts_summary: list[JSONDocument] = []
    retention_summary: list[JSONDocument] = []
    for raw_claim, evaluated_node in zip(claims, graph_eval["nodes"]):
        c_block = raw_claim.get("claim", {})
        ev_block = raw_claim.get("evaluation", {})
        ret_block = raw_claim.get("retention")
        ret_ok, ret_reason = validate_retention_policy(ret_block)

        receipts_summary.append(
            {
                "claim_id": evaluated_node["claim_id"],
                "article": evaluated_node["article"],
                "predicate": c_block.get("predicate"),
                "scope": c_block.get("scope"),
                "evidence_digest": c_block.get("evidence_digest"),
                "test_suite_digest": ev_block.get("test_suite_digest"),
                "independent_witness": ev_block.get("independent_witness", False),
                "accepted": evaluated_node["accepted"],
            }
        )
        retention_summary.append(
            {
                "claim_id": evaluated_node["claim_id"],
                "data_class": ret_block.get("data_class", "unspecified")
                if isinstance(ret_block, dict)
                else "unspecified",
                "retention_months": ret_block.get("retention_months") if isinstance(ret_block, dict) else None,
                "retention_valid": ret_ok,
                "retention_status": ret_reason,
            }
        )

    sys_identity: JSONDocument = {
        "system_id": target_sys.get("system_id"),
        "operator_role": target_sys.get("operator_role"),
        "intended_purpose_id": target_sys.get("intended_purpose_id"),
        "artifact_sha256": target_sys.get("artifact_sha256"),
        "runtime_profile_sha256": target_sys.get("runtime_profile_sha256"),
        "policy_sha256": target_sys.get("policy_sha256"),
        "model_identity": target_sys.get("model_identity"),
        "model_identity_valid": model_ok,
        "model_identity_status": model_reason,
        "is_external_opaque_model": is_external_model,
    }
    if target_sys.get("deployer_category") is not None:
        sys_identity["deployer_category"] = target_sys.get("deployer_category")
    if target_sys.get("annex_iii_use_case") is not None:
        sys_identity["annex_iii_use_case"] = target_sys.get("annex_iii_use_case")

    execution_evidence: JSONDocument = {
        "system_identity": sys_identity,
        "reproducible_test_receipts": receipts_summary,
        "retention_and_gdpr_controls": retention_summary,
        "unauthorized_effects": 0 if graph_eval["technical_status"] == "TECHNICAL_EVIDENCE_VALID" else None,
    }

    assurance_dossier: JSONDocument = {
        "regulation": {
            "id": "EU-AI-ACT",
            "base": "Regulation (EU) 2024/1689",
            "amendment": "Regulation (EU) 2026/1744",
            "consolidated_at": "2026-07-27",
            "catalogue_digest": CATALOGUE_DIGEST,
        },
        "value_chain_positioning": "ART_25_4_TECHNICAL_EVIDENCE_AND_ASSURANCE_INTERFACE",
        "fria_article_27_required": graph_eval["fria_article_27_required"],
        "obligation_nodes": graph_eval["nodes"],
        "missing_critical_articles": graph_eval["missing_critical_articles"],
        "critical_checks_missing": graph_eval["critical_checks_missing"],
        "fl_aiact_01_v2_gate": graph_eval["fl_aiact_01_v2_gate"],
        "technical_status": graph_eval["technical_status"],
        "legal_status": graph_eval["legal_status"],
        "verdict": graph_eval["verdict"],
        "eu_ai_act_certified": False,
        "boundary_statement": "TechnicalPASS != LegalConformity; conformity assessment remains an accountable provider/deployer obligation.",
    }

    continuous_monitoring: JSONDocument = {
        "change_classification": graph_eval["change_classification"],
        "accepted_orthogonal_claim_ids": graph_eval["accepted_claim_ids"],
        "invalidated_or_stale_claim_ids": graph_eval["rejected_claim_ids"],
        "stale_or_invalid_claims_rejected": graph_eval["stale_or_invalid_claims_rejected"],
        "requires_substantial_modification_assessment": graph_eval["change_classification"][
            "requires_substantial_modification_assessment"
        ],
        "requires_post_market_corrective_action": graph_eval["change_classification"][
            "requires_post_market_corrective_action"
        ],
    }

    return {
        "schema": GATEWAY_BUNDLE_SCHEMA,
        "execution_evidence": execution_evidence,
        "assurance_dossier": assurance_dossier,
        "continuous_evidence_monitoring": continuous_monitoring,
        "graph_evaluation_digest": digest(graph_eval),
        "eu_ai_act_certified": False,
    }


def generate_sample_assurance_gateway_bundle(bundle_root: Path) -> JSONDocument:
    """Deterministic builder for the Annex III employment recruitment screening sample bundle."""

    def _h(label: str) -> str:
        return hashlib.sha256(label.encode("utf-8")).hexdigest()

    bundle_root.mkdir(parents=True, exist_ok=True)
    baseline_system: JSONDocument = {
        "system_id": "SYS-ANNEX-III-HR-SELECT-01",
        "operator_role": "provider",
        "intended_purpose_id": _h("annex-iii-4a-recruitment-candidate-screening-v1"),
        "model_identity": "google:gemini-4-argon:2026-11",
        "model_uncertainty_declared": True,
        "containment_policy": "RING0_CAPABILITY_BROKER_AND_SEATBELT",
        "artifact_sha256": _h("babylon60-regulatory-gate-v5.1.0"),
        "runtime_profile_sha256": _h("macos-seatbelt-strict-v1.0"),
        "policy_sha256": _h("hr-screening-policy-epoch-1"),
    }

    specs: list[tuple[str, int, list[str], JSONDocument]] = [
        (
            "CLM-A9-RISK-MGMT",
            9,
            ["intended_purpose_id", "model_identity", "policy_sha256"],
            {"data_class": "provider_technical_documentation", "retention_months": 120},
        ),
        (
            "CLM-A10-DATA-GOV",
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
            "CLM-A11-TECH-DOC",
            11,
            ["intended_purpose_id", "artifact_sha256"],
            {"data_class": "provider_technical_documentation", "retention_months": 120},
        ),
        (
            "CLM-A12-RECORD-KEEPING",
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
            "CLM-A13-INSTRUCTIONS",
            13,
            ["intended_purpose_id"],
            {"data_class": "provider_technical_documentation", "retention_months": 120},
        ),
        (
            "CLM-A14-HUMAN-OVERSIGHT",
            14,
            ["intended_purpose_id", "policy_sha256"],
            {"data_class": "operational_event_logs", "retention_months": 12},
        ),
        (
            "CLM-A15-ROBUSTNESS-CYBER",
            15,
            ["artifact_sha256", "runtime_profile_sha256", "policy_sha256"],
            {"data_class": "provider_technical_documentation", "retention_months": 120},
        ),
        (
            "CLM-A17-QUALITY-SYSTEM",
            17,
            ["intended_purpose_id"],
            {"data_class": "provider_technical_documentation", "retention_months": 120},
        ),
        (
            "CLM-A43-CHANGE-CONTROL",
            43,
            ["intended_purpose_id", "artifact_sha256"],
            {"data_class": "provider_technical_documentation", "retention_months": 120},
        ),
    ]

    claims: list[JSONDocument] = []
    for cid, article, bound_dims, retention in specs:
        ev_rel = f"sample_{cid.lower()}.json"
        ev_bytes = canonical({"claim_id": cid, "article": article, "sample_fixture": True})
        (bundle_root / ev_rel).write_bytes(ev_bytes)
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
                "system": dict(baseline_system),
                "retention": retention,
                "claim": {
                    "predicate": f"annex_iii_article_{article}_controls_verified == true",
                    "scope": "simulated_annex_iii_recruitment_screening",
                    "evidence_path": ev_rel,
                    "evidence_digest": ev_sha,
                    "verdict": "SUPPORTED_WITHIN_DOMAIN",
                },
                "evaluation": {
                    "test_suite_digest": _h(f"fl-aiact-02-suite-{cid}"),
                    "independent_witness": True,
                    "unresolved_findings": 0,
                },
                "review": {
                    "technical_status": "PASS",
                    "legal_status": "NOT_ASSESSED",
                },
            }
        )

    return export_assurance_gateway_bundle(
        claims,
        {"system": dict(baseline_system)},
        bundle_root,
        baseline_system=baseline_system,
        now=1_800_000_000,
    )


def generate_deployer_fria_sample_bundle(bundle_root: Path) -> JSONDocument:
    """Deterministic builder for Annex III 5(b) creditworthiness deployer sample bundle under Art. 27 FRIA."""

    def _h(label: str) -> str:
        return hashlib.sha256(label.encode("utf-8")).hexdigest()

    bundle_root.mkdir(parents=True, exist_ok=True)
    baseline_system: JSONDocument = {
        "system_id": "SYS-ANNEX-III-CREDIT-EVAL-01",
        "operator_role": "deployer",
        "deployer_category": "private_enterprise",
        "annex_iii_use_case": "annex_iii_5b_creditworthiness",
        "intended_purpose_id": _h("annex-iii-5b-creditworthiness-evaluation-v1"),
        "model_identity": "google:gemini-4-argon:2026-11",
        "model_uncertainty_declared": True,
        "containment_policy": "DEPLOYER_MANAGED_CAPABILITY_BROKER",
        "artifact_sha256": _h("credit-deployer-runtime-v2.1.0"),
        "runtime_profile_sha256": _h("secure-deployer-seatbelt-v1.0"),
        "policy_sha256": _h("credit-deployer-policy-epoch-1"),
    }

    sample_annex_iv: JSONDocument = {
        "schema": ANNEX_IV_SCHEMA,
        "section_1_general_description": {
            "intended_purpose": "Annex III 5(b) creditworthiness assessment for retail borrowing applications",
            "system_version": "v2.1.0",
            "hardware_requirements": {"architecture": "arm64", "min_ram_gb": 32},
            "distribution_form": "on_premise_appliance",
            "hardware_software_interaction": "sandboxed_posix_ipc",
        },
        "section_2_development_process": {
            "design_specifications": {"architecture": "ring0_capability_broker", "deterministic_math": "F60"},
            "data_governance": {
                "training_provenance": "provider_attested",
                "deployer_input_pipeline": "fair_lending_filtered",
            },
            "human_oversight": {"oversight_tier": "dual_human_signoff", "override_capability": True},
            "validation_and_testing": {"metrics": ["demographic_parity", "equalized_odds"], "passed": True},
        },
        "section_3_monitoring_and_control": {
            "capabilities_and_limitations": {"max_applications_per_minute": 100, "domain": "retail_personal_loans"},
            "cybersecurity_measures": {"memory_isolation": "seatbelt", "logging": "worm_l0_sqlite"},
        },
        "section_4_risk_management": {
            "risk_management_system": "ISO_42001_ALIGNED_CONTINUOUS_PROCESS",
            "risk_register_id": "RR-CREDIT-2026-V1",
        },
        "section_5_change_log": {
            "changes": [{"version": "v2.1.0", "change": "added FRIA Art. 27 gating and continuous review"}]
        },
        "section_6_standards": {"harmonised_standards": ["EN ISO/IEC 42001:2023", "IEEE 7000-2021"]},
        "section_7_declaration_of_conformity": {
            "eu_declaration_of_conformity_status": "PENDING_FORMAL_NOTIFIED_BODY_OR_INTERNAL_CONTROL"
        },
        "section_8_post_market_monitoring": {
            "post_market_monitoring_plan": {"incident_threshold_bps": 50, "review_frequency_months": 3}
        },
    }

    sample_risk_mgmt: JSONDocument = {
        "schema": RISK_MANAGEMENT_SCHEMA,
        "periodic_review_months": 6,
        "risk_identification": {
            "identified_risks": [
                {
                    "risk_id": "RSK-01",
                    "description": "Biased credit scoring against protected demographic groups",
                    "severity": "HIGH",
                },
                {
                    "risk_id": "RSK-02",
                    "description": "Model hallucination under unobserved financial ratio distributions",
                    "severity": "MEDIUM",
                },
            ]
        },
        "risk_estimation_and_evaluation": {
            "evaluation_methodology": "probabilistic_risk_assessment",
            "unmitigated_risk_level": "HIGH",
        },
        "post_market_risk_evaluation": {
            "post_market_incident_data_feed": True,
            "incident_integration_frequency_days": 7,
        },
        "risk_mitigation_measures": {
            "mitigations": [
                {"risk_id": "RSK-01", "control": "disparate_impact_mitigation_filter", "status": "VERIFIED"},
                {"risk_id": "RSK-02", "control": "fail_stop_anomaly_detector", "status": "VERIFIED"},
            ]
        },
        "testing_and_validation": {
            "predefined_thresholds": {
                "max_false_positive_disparity": "0.02",
                "min_decision_accuracy": "0.96",
            },
            "testing_status": "TESTS_PASSED",
        },
        "residual_risk_acceptance": {
            "accountable_owner": "Chief Risk and Compliance Officer",
            "residual_risk_status": "ACCEPTED",
            "unacceptable_risks_count": 0,
            "acceptance_statement": "Residual risks acceptable within documented operational envelope.",
        },
    }

    sample_fria: JSONDocument = {
        "schema": FRIA_SCHEMA,
        "deployer_category": "private_enterprise",
        "annex_iii_use_case": "annex_iii_5b_creditworthiness",
        "assessment_period": "2026-H2",
        "affected_natural_persons": ["loan_applicants", "retail_borrowers"],
        "specific_risks_of_harm": ["credit_denial_without_justification", "indirect_discrimination"],
        "human_oversight_measures": ["mandatory_human_review_for_all_adverse_credit_decisions"],
        "governance_and_complaints": {"complaint_mechanism": "accessible_portal", "sla_days": 15},
        "market_surveillance_notification": {"authority": "AESIA_SPAIN_OR_COMPETENT_EU_BODY", "status": "SUBMITTED"},
    }

    specs: list[tuple[str, int, list[str], JSONDocument, JSONDocument, bool, bool]] = [
        (
            "CLM-A9-DEPLOYER-RISK",
            9,
            ["intended_purpose_id", "model_identity", "policy_sha256"],
            {"data_class": "operational_event_logs", "retention_months": 24},
            sample_risk_mgmt,
            False,
            True,
        ),
        (
            "CLM-A10-DEPLOYER-INPUT-DATA",
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
            {"claim_id": "CLM-A10-DEPLOYER-INPUT-DATA", "article": 10, "data_relevance_verified": True},
            False,
            False,
        ),
        (
            "CLM-A11-DEPLOYER-TECH-DOC",
            11,
            ["intended_purpose_id", "artifact_sha256"],
            {"data_class": "operational_event_logs", "retention_months": 24},
            sample_annex_iv,
            True,
            False,
        ),
        (
            "CLM-A12-DEPLOYER-LOGS",
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
            {"claim_id": "CLM-A12-DEPLOYER-LOGS", "article": 12, "log_retention_6m_verified": True},
            False,
            False,
        ),
        (
            "CLM-A13-DEPLOYER-INSTRUCTIONS",
            13,
            ["intended_purpose_id"],
            {"data_class": "operational_event_logs", "retention_months": 24},
            {"claim_id": "CLM-A13-DEPLOYER-INSTRUCTIONS", "article": 13, "instructions_compliance_verified": True},
            False,
            False,
        ),
        (
            "CLM-A14-DEPLOYER-OVERSIGHT",
            14,
            ["intended_purpose_id", "policy_sha256"],
            {"data_class": "operational_event_logs", "retention_months": 24},
            {"claim_id": "CLM-A14-DEPLOYER-OVERSIGHT", "article": 14, "human_oversight_trained_verified": True},
            False,
            False,
        ),
        (
            "CLM-A15-DEPLOYER-SECURITY",
            15,
            ["artifact_sha256", "runtime_profile_sha256", "policy_sha256"],
            {"data_class": "operational_event_logs", "retention_months": 24},
            {"claim_id": "CLM-A15-DEPLOYER-SECURITY", "article": 15, "cybersecurity_monitoring_verified": True},
            False,
            False,
        ),
        (
            "CLM-A26-DEPLOYER-GOVERNANCE",
            26,
            ["intended_purpose_id", "policy_sha256"],
            {"data_class": "operational_event_logs", "retention_months": 24},
            {"claim_id": "CLM-A26-DEPLOYER-GOVERNANCE", "article": 26, "deployer_governance_verified": True},
            False,
            False,
        ),
        (
            "CLM-A27-FRIA-ASSESSMENT",
            27,
            ["intended_purpose_id", "policy_sha256"],
            {"data_class": "operational_event_logs", "retention_months": 36},
            sample_fria,
            False,
            False,
        ),
    ]

    claims: list[JSONDocument] = []
    for cid, article, bound_dims, retention, ev_payload, val_a4, val_r9 in specs:
        ev_rel = f"deployer_sample_{cid.lower()}.json"
        ev_bytes = canonical(ev_payload)
        (bundle_root / ev_rel).write_bytes(ev_bytes)
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
                    "operator_role": "deployer",
                },
                "system": dict(baseline_system),
                "retention": retention,
                "validate_annex_iv": val_a4,
                "validate_risk_management": val_r9,
                "claim": {
                    "predicate": f"annex_iii_article_{article}_deployer_controls_verified == true",
                    "scope": "simulated_annex_iii_5b_creditworthiness_deployer",
                    "evidence_path": ev_rel,
                    "evidence_digest": ev_sha,
                    "verdict": "SUPPORTED_WITHIN_DOMAIN",
                },
                "evaluation": {
                    "test_suite_digest": _h(f"fl-aiact-02-deployer-suite-{cid}"),
                    "independent_witness": True,
                    "unresolved_findings": 0,
                },
                "review": {
                    "technical_status": "PASS",
                    "legal_status": "NOT_ASSESSED",
                },
            }
        )

    return export_assurance_gateway_bundle(
        claims,
        {"system": dict(baseline_system)},
        bundle_root,
        baseline_system=baseline_system,
        now=1_800_000_000,
    )
