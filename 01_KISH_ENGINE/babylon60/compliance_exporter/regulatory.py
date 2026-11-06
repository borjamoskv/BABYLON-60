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
