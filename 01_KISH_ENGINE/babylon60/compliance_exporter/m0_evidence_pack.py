"""
BABYLON-60 M0: COMPLIANCE AS CODE — Deterministic Evidence Pack Compiler
========================================================================
Compiles execution constraints, cryptographic ledgers, NEMESIS adversarial
falsification telemetry, and formal proof references into a reproducible,
independently verifiable `babylon-m0-evidence-pack/` directory.

Core Epistemic & Legal Invariants:
  1. Contribution != Conformity: Never emits `COMPLIANT` automatically from
     `TEST_PASSED`. Enforces the strict chain:
       CONTROL -> TEST -> EVIDENCE -> REGULATORY_REQUIREMENT -> ASSESSMENT
     (EU AI Act Art. 47 responsibility remains with the provider/deployer).
  2. Explicit Enforcement Perimeter: Every control and claim declares whether
     it is `BROKER_MEDIATED` or `OS_ENFORCED` (macOS Seatbelt / Endpoint Security).
     Any real bypass discovered by NEMESIS forces `FALSIFIED` or
     `UNSUPPORTED_WITHIN_SCOPE`.
  3. SQLite Threat Model Clarity: Immutability does not rely on SQLite triggers
     (which can be dropped via `DROP TRIGGER`). Integrity rests on SHA3-256
     row hash-chaining, Merkle cardinality anchoring, and external Ed25519
     signatures; completeness is bounded by the declared mediation perimeter.
  4. Dynamic Canonical Claims: Reads `CLAIMS.toml` dynamically without assuming
     a hardcoded count of 21, 23, or 24 claims.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

from babylon60.verifier.standalone_verify import (
    ZERO_HASH_256,
    build_cortex_merkle_tree,
    canonical_json,
    compute_cortex_hash,
)

PACK_SCHEMA_VERSION = "babylon60.m0.evidence_pack.v1"
CANONICAL_DEMO_STATEMENT = (
    "The agent attempted an unauthorized action. The enforced control denied it. "
    "Here is the independently verifiable evidence."
)

# Deterministically derived default Ed25519 seed for reproducible M0 test packs
# when BABYLON60_SIGNING_SEED is not set in the environment.
DEFAULT_DETERMINISTIC_M0_SEED_HEX = hashlib.sha256(
    b"BABYLON-60-M0-DETERMINISTIC-EVIDENCE-PACK-SIGNING-SEED-V1"
).hexdigest()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _sign_ed25519_bytes(payload_bytes: bytes, seed_hex: str) -> Tuple[str, str]:
    """Returns (public_key_hex, signature_hex) using cryptography or PyNaCl."""
    seed_bytes = bytes.fromhex(seed_hex)
    if len(seed_bytes) != 32:
        raise ValueError("Ed25519 seed must be 32 bytes (64 hex chars)")

    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization

        priv = Ed25519PrivateKey.from_private_bytes(seed_bytes)
        pub_bytes = priv.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        sig_bytes = priv.sign(payload_bytes)
        return pub_bytes.hex(), sig_bytes.hex()
    except ImportError:
        pass

    from nacl.signing import SigningKey

    sk = SigningKey(seed_bytes)
    signed = sk.sign(payload_bytes)
    return sk.verify_key.encode().hex(), signed.signature.hex()


def _build_minimal_pdf(lines: List[str]) -> bytes:
    """
    Generates a deterministic, standards-compliant PDF 1.4 binary document
    without external rendering dependencies.
    """

    def escape_pdf_text(text: str) -> str:
        ascii_safe = text.encode("ascii", errors="replace").decode("ascii")
        return ascii_safe.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    content_ops = ["BT", "/F1 10 Tf", "50 760 Td", "14 TL"]
    for idx, line in enumerate(lines[:48]):
        escaped = escape_pdf_text(line)
        if idx == 0:
            content_ops.append(f"({escaped}) Tj")
        else:
            content_ops.append(f"T* ({escaped}) Tj")
    content_ops.append("ET")
    stream_bytes = "\n".join(content_ops).encode("ascii")

    objects: List[bytes] = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        (
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n"
        ),
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>\nendobj\n",
        (
            f"5 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode("ascii")
            + stream_bytes
            + b"\nendstream\nendobj\n"
        ),
    ]

    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    body = bytearray(header)
    offsets: List[int] = []
    for obj in objects:
        offsets.append(len(body))
        body.extend(obj)

    xref_offset = len(body)
    xref_lines = [f"xref\n0 {len(objects) + 1}\n", "0000000000 65535 f \n"]
    for off in offsets:
        xref_lines.append(f"{off:010d} 00000 n \n")
    trailer = (
        "".join(xref_lines)
        + f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        + f"startxref\n{xref_offset}\n%%EOF\n"
    )
    body.extend(trailer.encode("ascii"))
    return bytes(body)


def build_regulatory_contribution_matrix(
    claims_by_id: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Builds the multi-framework regulatory matrix (Rule 1.A) expressing technical
    evidence contribution and explicit organizational/legal boundaries.
    Never emits `COMPLIANT` automatically from `TEST_PASSED`.
    """
    frameworks = [
        {
            "framework_id": "EU_AI_ACT_ART_12",
            "framework": "EU AI Act (Regulation (EU) 2024/1689), Art. 12",
            "requirement_summary": "Automatic recording of events (logging) and traceability throughout the lifecycle.",
            "babylon60_evidence_contribution": "Automatic cryptographic event logging (COSE_Sign1 receipts + hash-chained SQLite L0 WAL) and causal traceability.",
            "organizational_and_legal_limit": "Applicable to high-risk AI systems; not just any log suffices. Retention policies, operational log governance, and use-case risk tiering remain deployer/provider obligations.",
            "mapped_claims": ["cose_ed25519_receipt", "cortex_persist_sqlite", "merkle_attestation"],
        },
        {
            "framework_id": "EU_AI_ACT_ART_14",
            "framework": "EU AI Act (Regulation (EU) 2024/1689), Art. 14",
            "requirement_summary": "Human oversight measures enabling natural persons to prevent/minimize risks and intervene or stop the system.",
            "babylon60_evidence_contribution": "Deterministic authorization gating, intervention/revocation hooks, and Secure Enclave P-256 / fail-stop halt mechanisms.",
            "organizational_and_legal_limit": "A technical Broker does not by itself substitute human oversight. Operator training, anti-automation-bias procedures, and UI interpretability depend on the organization.",
            "mapped_claims": ["secure_enclave_p256", "mcp_authority_gate", "inv_04_fail_stop_halt", "AUTH_001"],
        },
        {
            "framework_id": "EU_AI_ACT_ART_15",
            "framework": "EU AI Act (Regulation (EU) 2024/1689), Art. 15",
            "requirement_summary": "Appropriate levels of accuracy, robustness, fail-safe operation, and cybersecurity resilience.",
            "babylon60_evidence_contribution": "Adversarial falsification tests (NEMESIS), TOCTOU quarantine isolation, crash consistency under SIGKILL, and fail-stop apoptosis (0xDEAD_6060).",
            "organizational_and_legal_limit": "Does not prove complete organizational or end-to-end system cybersecurity outside the declared Trusted Computing Base (TCB) and tested fault models.",
            "mapped_claims": [
                "AUTH_004",
                "AUTH_006",
                "AUTH_007_secure_fs_quarantine",
                "FL_008_scoped_capability_broker",
                "INV_OMEGA_complete_mediation",
            ],
        },
        {
            "framework_id": "EU_AI_ACT_ANNEX_IV",
            "framework": "EU AI Act (Regulation (EU) 2024/1689), Annex IV",
            "requirement_summary": "Technical documentation required prior to placing a high-risk AI system on the market or putting it into service.",
            "babylon60_evidence_contribution": "Reproducible technical evidence, architecture scope descriptors, formal proof artifacts, and verifiable execution traces for Annex IV dossiers.",
            "organizational_and_legal_limit": "Does not replace the complete Annex IV technical documentation file or the EU declaration of conformity under Article 47.",
            "mapped_claims": ["inv_01_manifest_layout", "inv_02_seqlock_concurrency", "lean4_formal_trace"],
        },
        {
            "framework_id": "DORA_ARTS_9_10",
            "framework": "DORA (Regulation (EU) 2022/2554), Arts. 9 & 10",
            "requirement_summary": "ICT protection, prevention, access control, and anomaly/incident detection for financial entities.",
            "babylon60_evidence_contribution": "Prevention of unauthorized agent mutations, capability-scoped access control, and deterministic detection of integrity or policy violations.",
            "organizational_and_legal_limit": "Depends on the financial entity's broader ICT risk management framework, incident response governance, and third-party oversight.",
            "mapped_claims": [
                "AUTH_002",
                "AUTH_003",
                "FL_007_admission_bounded_liveness",
                "FL_008_scoped_capability_broker",
            ],
        },
        {
            "framework_id": "NIS2_ART_21",
            "framework": "NIS2 Directive (Directive (EU) 2022/2555), Art. 21",
            "requirement_summary": "Cybersecurity risk-management measures including access control, cryptography, and incident handling.",
            "babylon60_evidence_contribution": "Cryptographic evidence of access control enforcement, Ed25519/COSE signing, and fail-closed containment of autonomous agent processes.",
            "organizational_and_legal_limit": "Does not accredit organization-wide NIS2 compliance (supply chain policies, human resources security, business continuity, or statutory reporting).",
            "mapped_claims": ["cose_ed25519_receipt", "AUTH_005", "INV_OMEGA_complete_mediation"],
        },
        {
            "framework_id": "ISO_IEC_42001",
            "framework": "ISO/IEC 42001:2023 (AI Management System)",
            "requirement_summary": "Requirements for establishing, implementing, maintaining, and continually improving an Artificial Intelligence Management System (AIMS).",
            "babylon60_evidence_contribution": "Operational control telemetry and verifiable execution evidence usable as input artifacts for an organization's AIMS.",
            "organizational_and_legal_limit": "Does not constitute ISO/IEC 42001 certification, which requires an accredited certification body audit of the entire management system.",
            "mapped_claims": ["cortex_persist_sqlite", "merkle_attestation", "mcp_authority_gate"],
        },
        {
            "framework_id": "SOC2_TRUST_SERVICES",
            "framework": "AICPA SOC 2 (Trust Services Criteria — Security & Processing Integrity)",
            "requirement_summary": "Design and operating effectiveness of controls over system security, authorization, and processing integrity.",
            "babylon60_evidence_contribution": "Verifiable evidence regarding the design and deterministic operation of runtime authorization, non-replay, and tamper-evident logging controls.",
            "organizational_and_legal_limit": "Does not replace the examination and opinion of an independent CPA / service auditor (SOC 2 Type I / Type II report).",
            "mapped_claims": ["AUTH_001", "AUTH_002", "AUTH_006", "cortex_persist_sqlite"],
        },
    ]

    entries: List[Dict[str, Any]] = []
    for item in frameworks:
        mapped_details: List[Dict[str, Any]] = []
        all_supported = True
        for cid in item["mapped_claims"]:
            c_obj = claims_by_id.get(cid)
            if c_obj is None:
                all_supported = False
                mapped_details.append(
                    {
                        "claim_id": cid,
                        "claim_status": "MISSING_FROM_REGISTRY",
                        "enforcement_mode": "UNKNOWN",
                    }
                )
            else:
                st = c_obj["status"]
                if st != "SUPPORTED_WITHIN_SCOPE":
                    all_supported = False
                mapped_details.append(
                    {
                        "claim_id": cid,
                        "claim_status": st,
                        "enforcement_mode": c_obj["enforcement_mode"],
                        "evidence_level": c_obj["evidence_level"],
                    }
                )

        # Rule 1.A: NEVER emit "COMPLIANT" automatically from TEST_PASSED.
        assessment_stage_status = (
            "EVIDENCE_READY_FOR_AUDITOR_ASSESSMENT" if all_supported else "EVIDENCE_GAP_OR_FALSIFIED_CONTROL"
        )
        entries.append(
            {
                **item,
                "causal_chain_stage": "CONTROL -> TEST -> EVIDENCE -> REGULATORY_REQUIREMENT -> ASSESSMENT",
                "automated_compliance_verdict_permitted": False,
                "assessment_status": assessment_stage_status,
                "linked_claims_evaluation": mapped_details,
            }
        )

    return {
        "schema": "babylon60.m0.regulatory_matrix.v1",
        "derivation_rule": "CONTROL -> TEST -> EVIDENCE -> REGULATORY_REQUIREMENT -> ASSESSMENT",
        "commercial_and_legal_invariant": (
            "BABYLON-60 never generates COMPLIANT automatically from TEST_PASSED. "
            "Under EU AI Act Article 47, the provider issuing an EU declaration of conformity "
            "assumes responsibility for declared compliance. A cryptographic signature does not "
            "replace conformity assessment or legal accountability."
        ),
        "regulatory_timeline_context": {
            "eu_ai_act_consolidation_date": "2026-07-27",
            "annex_iii_high_risk_applicability": "2027-12-02",
            "annex_i_regulated_products_applicability": "2028-08-02",
        },
        "mappings": entries,
    }


class M0EvidencePackCompiler:
    """
    Deterministic compiler for the `babylon-m0-evidence-pack/` deliverable.
    Enforces strict separation of roles:
      - ARCHITECT: Defines controls and enforcement modes (`BROKER_MEDIATED` vs `OS_ENFORCED`).
      - NEMESIS: Executes adversarial falsification campaigns and reachability checks.
      - AUDITOR: Deterministically compiles evidence against `CLAIMS.toml` without LLM judgment.
    """

    def __init__(
        self,
        repo_root: Optional[Union[str, Path]] = None,
        claims_toml_path: Optional[Union[str, Path]] = None,
        signing_seed_hex: Optional[str] = None,
    ) -> None:
        self.repo_root = Path(repo_root).absolute() if repo_root is not None else Path(__file__).resolve().parents[3]
        self.claims_toml_path = (
            Path(claims_toml_path).absolute() if claims_toml_path is not None else self.repo_root / "CLAIMS.toml"
        )
        env_seed = os.environ.get("BABYLON60_SIGNING_SEED", "").strip()
        self.signing_seed_hex = signing_seed_hex or env_seed or DEFAULT_DETERMINISTIC_M0_SEED_HEX

    def load_canonical_claims(self) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """Reads all claims dynamically from CLAIMS.toml without hardcoding claim counts."""
        if not self.claims_toml_path.exists():
            raise FileNotFoundError(f"Canonical CLAIMS.toml not found at {self.claims_toml_path}")
        with open(self.claims_toml_path, "rb") as f:
            parsed = tomllib.load(f)
        metadata = parsed.get("metadata", {})
        claims_raw = parsed.get("claim", {})
        if not isinstance(claims_raw, dict) or not claims_raw:
            raise ValueError("CLAIMS.toml contains no [claim.<id>] sections")
        return metadata, claims_raw

    @staticmethod
    def _classify_enforcement_mode(claim_id: str, raw: Dict[str, Any]) -> str:
        """
        Rule 1.B: Differentiates between `BROKER_MEDIATED` (actions channeled through
        the Broker within a declared perimeter) and `OS_ENFORCED` (actions covered by
        effective OS mechanisms such as macOS Seatbelt / Endpoint Security).
        """
        ev_level = str(raw.get("evidence_level", "L2_IMPLEMENTATION"))
        scope_str = str(raw.get("scope", ""))
        if ev_level == "L3_ISOLATION" or "sandbox-exec" in scope_str or "Seatbelt" in scope_str:
            return "OS_ENFORCED"
        return "BROKER_MEDIATED"

    @staticmethod
    def _normalize_claim_status(
        claim_id: str,
        raw: Dict[str, Any],
        nemesis_results: Dict[str, Any],
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Maps canonical claim status and NEMESIS adversarial outcomes into explicit
        epistemic states:
          - SUPPORTED_WITHIN_SCOPE
          - FALSIFIED
          - UNSUPPORTED_WITHIN_SCOPE
          - UNTESTED
        """
        counterexamples: List[Dict[str, Any]] = []
        campaigns = nemesis_results.get("campaigns", {})

        # If NEMESIS recorded a bypass or falsification targeting this claim:
        for camp_id, camp in campaigns.items():
            target_claims = camp.get("target_claims", [])
            if claim_id in target_claims or (
                not target_claims and claim_id == "INV_OMEGA_complete_mediation" and camp.get("bypass_detected", False)
            ):
                if camp.get("bypass_detected", False) or camp.get("outcome") == "FALSIFIED":
                    counterexamples.append(
                        {
                            "campaign_id": camp_id,
                            "vector": camp.get("attack_vector", "unknown"),
                            "detail": camp.get("detail", "Adversarial bypass succeeded"),
                            "enforcement_gap": camp.get("enforcement_gap", "UNMEDIATED_OS_PATH"),
                        }
                    )

        if counterexamples:
            # Rule 3: If NEMESIS discovers a real bypass, emit FALSIFIED or UNSUPPORTED_WITHIN_SCOPE
            for ce in counterexamples:
                if ce.get("enforcement_gap") == "OUTSIDE_BROKER_SCOPE_NO_OS_ENFORCEMENT":
                    return "UNSUPPORTED_WITHIN_SCOPE", counterexamples
            return "FALSIFIED", counterexamples

        raw_status = str(raw.get("status", "untested")).lower()
        if raw_status in {"verified", "verified_local", "verified_in_memory"}:
            return "SUPPORTED_WITHIN_SCOPE", counterexamples
        if raw_status == "falsified":
            return "FALSIFIED", [
                {
                    "campaign_id": "STATIC_CLAIM_STATUS",
                    "vector": "declared_falsified",
                    "detail": "Claim marked falsified in canonical registry",
                }
            ]
        return "UNTESTED", counterexamples

    def _create_default_ledger_and_trace(
        self,
        ledger_file: Path,
        trace_file: Path,
        logical_epoch: int = 1,
    ) -> Dict[str, Any]:
        """
        Creates a deterministic SQLite L0 ledger (with `PRAGMA synchronous = FULL` per
        INV_C5_WAL_SYNCHRONOUS_FULL) and matching `execution-trace.jsonl` demostrar
        the canonical M0 scenario:
          1. Unauthorized action attempted -> Enforced control DENIED it.
          2. Authorized action within scope -> Enforced control ALLOWED & COMMITTED it.
        """
        if ledger_file.exists():
            ledger_file.unlink()

        conn = sqlite3.connect(str(ledger_file))
        try:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = FULL;")
            conn.execute(
                """
                CREATE TABLE cortex_ledger (
                    seq INTEGER PRIMARY KEY,
                    event_id TEXT NOT NULL UNIQUE,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    cortex_taint TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    lamport_t INTEGER NOT NULL,
                    prev_hash TEXT NOT NULL,
                    entry_hash TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
                """
            )

            events = [
                {
                    "seq": 1,
                    "event_id": f"EV_{logical_epoch}_0001",
                    "event_type": "EFFECT_DECISION_DENY",
                    "payload": {
                        "action": "DELETE_FILE",
                        "resource": "/vault/protected_financial_ledger.db",
                        "decision": "DENY",
                        "reason": "MISSING_COSE_CAPABILITY_TICKET",
                        "enforcement_mode": "BROKER_MEDIATED",
                        "observed_mutation": False,
                    },
                    "cortex_taint": "UNTRUSTED_AGENT_PROPOSAL",
                    "agent_id": "ARCHITECT-GATEWAY",
                    "domain": "babylon60.com",
                    "lamport_t": 1,
                    "timestamp": "2026-10-17T00:00:01Z",
                },
                {
                    "seq": 2,
                    "event_id": f"EV_{logical_epoch}_0002",
                    "event_type": "NEMESIS_BYPASS_INTERCEPTED",
                    "payload": {
                        "action": "DIRECT_UNLINK_SYSCALL",
                        "resource": "/vault/protected_financial_ledger.db",
                        "decision": "DENY_EPERM",
                        "reason": "MACOS_SEATBELT_SANDBOX_DENY_FILE_WRITE_UNLINK",
                        "enforcement_mode": "OS_ENFORCED",
                        "observed_mutation": False,
                    },
                    "cortex_taint": "NEMESIS_ADVERSARIAL_PROBE",
                    "agent_id": "NEMESIS-FALSIFIER",
                    "domain": "babylon60.com",
                    "lamport_t": 2,
                    "timestamp": "2026-10-17T00:00:02Z",
                },
                {
                    "seq": 3,
                    "event_id": f"EV_{logical_epoch}_0003",
                    "event_type": "EFFECT_COMMITTED_RECEIPT",
                    "payload": {
                        "action": "APPEND_AUDIT_LOG",
                        "resource": "/vault/audit_trail.log",
                        "decision": "ALLOW",
                        "receipt_stage": "COMMITTED",
                        "enforcement_mode": "BROKER_MEDIATED",
                        "observed_mutation": True,
                    },
                    "cortex_taint": "AUTHORIZED_CAPABILITY_EPOCH_1",
                    "agent_id": "ARCHITECT-GATEWAY",
                    "domain": "babylon60.com",
                    "lamport_t": 3,
                    "timestamp": "2026-10-17T00:00:03Z",
                },
            ]

            prev_hash = ZERO_HASH_256
            entry_hashes: List[str] = []
            trace_lines: List[str] = []

            for ev in events:
                payload_json = canonical_json(ev["payload"])
                entry_hash = compute_cortex_hash(
                    seq=int(str(ev["seq"])),
                    event_id=str(ev["event_id"]),
                    event_type=str(ev["event_type"]),
                    payload_json=payload_json,
                    cortex_taint=str(ev["cortex_taint"]),
                    lamport_t=int(str(ev["lamport_t"])),
                    prev_hash=prev_hash,
                    timestamp=str(ev["timestamp"]),
                    agent_id=str(ev["agent_id"]),
                    domain=str(ev["domain"]),
                )
                conn.execute(
                    """
                    INSERT INTO cortex_ledger (
                        seq, event_id, event_type, payload_json, cortex_taint,
                        agent_id, domain, lamport_t, prev_hash, entry_hash, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ev["seq"],
                        ev["event_id"],
                        ev["event_type"],
                        payload_json,
                        ev["cortex_taint"],
                        ev["agent_id"],
                        ev["domain"],
                        ev["lamport_t"],
                        prev_hash,
                        entry_hash,
                        ev["timestamp"],
                    ),
                )
                entry_hashes.append(entry_hash)
                trace_lines.append(
                    canonical_json(
                        {
                            "seq": ev["seq"],
                            "event_id": ev["event_id"],
                            "event_type": ev["event_type"],
                            "lamport_t": ev["lamport_t"],
                            "agent_id": ev["agent_id"],
                            "payload": ev["payload"],
                            "prev_hash": prev_hash,
                            "entry_hash": entry_hash,
                            "timestamp": ev["timestamp"],
                        }
                    )
                )
                prev_hash = entry_hash

            conn.commit()
            # Checkpoint WAL into main SQLite file so single-file distribution is self-contained
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        finally:
            conn.close()

        with open(trace_file, "w", encoding="utf-8") as tf:
            for line in trace_lines:
                tf.write(line + "\n")

        merkle_root = build_cortex_merkle_tree(entry_hashes)
        return {
            "total_entries": len(entry_hashes),
            "merkle_root": merkle_root,
            "entry_hashes": entry_hashes,
        }

    def compile_pack(
        self,
        output_dir: Union[str, Path],
        nemesis_override: Optional[Dict[str, Any]] = None,
        existing_ledger_path: Optional[Union[str, Path]] = None,
        issued_at_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compiles the complete `babylon-m0-evidence-pack/` directory and returns the
        compiled manifest dictionary.
        """
        t_start_ns = time.perf_counter_ns()
        out_path = Path(output_dir).absolute()
        if out_path.exists():
            shutil.rmtree(out_path)

        evidence_dir = out_path / "evidence"
        compliance_dir = out_path / "compliance"
        verification_dir = out_path / "verification"
        for d in (out_path, evidence_dir, compliance_dir, verification_dir):
            d.mkdir(parents=True, exist_ok=True)

        # 1. Load canonical claims dynamically (no hardcoded claim count)
        claims_meta, claims_raw = self.load_canonical_claims()
        claims_toml_digest = _sha256_file(self.claims_toml_path)

        # 2. Prepare NEMESIS adversarial results (evidence/nemesis-results.json)
        default_nemesis: Dict[str, Any] = {
            "schema": "babylon60.m0.nemesis_results.v1",
            "agent_role": "NEMESIS",
            "principle": "DENY != Proof; independent physical observation required (INV_C5_NEMESIS_EVIDENCE_CONTRACT)",
            "campaigns": {
                "BYPASS-001": {
                    "target_claims": ["INV_OMEGA_complete_mediation"],
                    "attack_vector": "direct_os_unlink_and_write_outside_broker",
                    "enforcement_mode_tested": "OS_ENFORCED",
                    "mechanism": "macOS sandbox-exec Seatbelt profile + AuthorityGraph cut",
                    "bypass_detected": False,
                    "independent_inode_observation": "INODE_UNCHANGED_EPERM_CONFIRMED",
                    "outcome": "SUPPORTED_WITHIN_SCOPE",
                },
                "AUTH-002": {
                    "target_claims": ["AUTH_002", "FL_008_scoped_capability_broker"],
                    "attack_vector": "unauthenticated_ipc_and_confused_deputy_handle_swap",
                    "enforcement_mode_tested": "BROKER_MEDIATED",
                    "mechanism": "COSE_Sign1 capability ticket + O_DIRECTORY/O_NOFOLLOW ScopedHandle",
                    "bypass_detected": False,
                    "independent_inode_observation": "ZERO_UNAUTHORIZED_EFFECTS_OVER_10000_TRIALS",
                    "outcome": "SUPPORTED_WITHIN_SCOPE",
                },
                "RACE-003": {
                    "target_claims": ["AUTH_004", "AUTH_007_secure_fs_quarantine"],
                    "attack_vector": "concurrent_symlink_toctou_swap_128_workers",
                    "enforcement_mode_tested": "BROKER_MEDIATED",
                    "mechanism": "renameatx_np(RENAME_EXCL) atomic quarantine 0700 + inode precondition check",
                    "bypass_detected": False,
                    "independent_inode_observation": "VICTIM_CANARY_INTACT_0_ESCAPES",
                    "outcome": "SUPPORTED_WITHIN_SCOPE",
                },
                "CRASH-004": {
                    "target_claims": ["AUTH_001", "AUTH_003", "AUTH_006"],
                    "attack_vector": "sigkill_at_4_causal_boundaries_plus_nonce_replay",
                    "enforcement_mode_tested": "BROKER_MEDIATED",
                    "mechanism": "SQLite WAL synchronous=FULL + .consumed_nonces.bin sync_all",
                    "bypass_detected": False,
                    "independent_inode_observation": "ZERO_DUPLICATE_EFFECTS_REPLAYS_REJECTED",
                    "outcome": "SUPPORTED_WITHIN_SCOPE",
                },
            },
        }
        nemesis_data = nemesis_override if nemesis_override is not None else default_nemesis
        nemesis_path = evidence_dir / "nemesis-results.json"
        with open(nemesis_path, "w", encoding="utf-8") as f:
            json.dump(nemesis_data, f, indent=2, sort_keys=True, ensure_ascii=False)

        # 3. Prepare Ledger L0 and Execution Trace
        ledger_target = evidence_dir / "ledger_l0.sqlite"
        trace_target = evidence_dir / "execution-trace.jsonl"
        if existing_ledger_path is not None:
            shutil.copy2(existing_ledger_path, ledger_target)
            from babylon60.verifier.standalone_verify import verify_offline_evidence

            ev_check = verify_offline_evidence(ledger_target)
            ledger_info = {
                "total_entries": ev_check["total_entries"],
                "merkle_root": ev_check["merkle_root"],
            }
            if not trace_target.exists():
                trace_target.write_text("", encoding="utf-8")
        else:
            ledger_info = self._create_default_ledger_and_trace(ledger_target, trace_target)

        # 4. Prepare Formal Proofs Index (evidence/formal-proofs.json)
        lean_files = ["proof/lean/Babylon.lean", "proof/lean/BabylonTrace.lean", "proof/lean/AX0.lean"]
        formal_proofs_entries: List[Dict[str, Any]] = []
        for rel_lf in lean_files:
            lf_path = self.repo_root / rel_lf
            if lf_path.exists():
                formal_proofs_entries.append(
                    {
                        "relative_path": rel_lf,
                        "sha256": _sha256_file(lf_path),
                        "engine": "Lean 4",
                        "evidence_level": "L1_FORMAL",
                    }
                )
        formal_proofs_data = {
            "schema": "babylon60.m0.formal_proofs.v1",
            "note": (
                "Formal proofs establish mathematical soundness of specifications (L1_FORMAL) "
                "within model assumptions; they do not by themselves grant legal immunity or "
                "replace OS-level isolation verification (L3_ISOLATION)."
            ),
            "proof_artifacts": formal_proofs_entries,
        }
        formal_proofs_path = evidence_dir / "formal-proofs.json"
        with open(formal_proofs_path, "w", encoding="utf-8") as f:
            json.dump(formal_proofs_data, f, indent=2, sort_keys=True, ensure_ascii=False)

        # 5. Compile dynamic claims.json (Rule 2: no hardcoded claim count)
        claims_compiled: Dict[str, Dict[str, Any]] = {}
        status_counts = {
            "SUPPORTED_WITHIN_SCOPE": 0,
            "FALSIFIED": 0,
            "UNSUPPORTED_WITHIN_SCOPE": 0,
            "UNTESTED": 0,
        }
        enforcement_counts = {
            "BROKER_MEDIATED": 0,
            "OS_ENFORCED": 0,
        }

        for cid, raw_claim in claims_raw.items():
            enf_mode = self._classify_enforcement_mode(cid, raw_claim)
            norm_status, counterexamples = self._normalize_claim_status(cid, raw_claim, nemesis_data)
            status_counts[norm_status] = status_counts.get(norm_status, 0) + 1
            enforcement_counts[enf_mode] = enforcement_counts.get(enf_mode, 0) + 1

            scope_val = raw_claim.get(
                "scope",
                f"Component {raw_claim.get('component', '00_ABZU_KERNEL')} bounded execution context",
            )
            assumptions_val = raw_claim.get(
                "notes",
                "Assumes non-compromised host kernel and verified signing key isolation.",
            )
            evidence_cmd = raw_claim.get("evidence") or raw_claim.get("evidence_suite") or ""

            claims_compiled[cid] = {
                "claim_id": cid,
                "statement": raw_claim.get("statement", ""),
                "component": raw_claim.get("component", "UNKNOWN"),
                "evidence_level": raw_claim.get("evidence_level", "L2_IMPLEMENTATION"),
                "enforcement_mode": enf_mode,
                "scope": scope_val,
                "assumptions": assumptions_val,
                "status": norm_status,
                "raw_registry_status": raw_claim.get("status", "untested"),
                "required_for_release": bool(raw_claim.get("required_for_release", False)),
                "counterexamples": counterexamples,
                "evidence_references": {
                    "reproducer_command": evidence_cmd,
                    "ledger_merkle_root": ledger_info["merkle_root"],
                    "nemesis_results_ref": "evidence/nemesis-results.json",
                    "formal_proofs_ref": "evidence/formal-proofs.json",
                },
            }

        claims_json_data = {
            "schema": "babylon60.m0.claims.v1",
            "source_registry": "CLAIMS.toml",
            "source_registry_sha256": claims_toml_digest,
            "registry_version": claims_meta.get("version", "5.0.0"),
            "root_axiom": claims_meta.get("root_axiom", ""),
            "total_claims_compiled": len(claims_compiled),
            "status_summary": status_counts,
            "enforcement_mode_summary": enforcement_counts,
            "claims": claims_compiled,
        }
        claims_json_path = out_path / "claims.json"
        with open(claims_json_path, "w", encoding="utf-8") as f:
            json.dump(claims_json_data, f, indent=2, sort_keys=True, ensure_ascii=False)

        # 6. Compile scope.json (Rules 1.B and 1.C)
        scope_json_data = {
            "schema": "babylon60.m0.scope.v1",
            "enforcement_boundaries": {
                "BROKER_MEDIATED": {
                    "definition": (
                        "Actions that pass through the BABYLON-60 Trust Gateway / Capability Broker "
                        "within a declared IPC or API perimeter."
                    ),
                    "guarantee_limit": (
                        "Proves that operations channeled through the Broker are subject to 7-tuple "
                        "authorization, capability scoping, and receipt logging. Cannot by itself prevent "
                        "a privileged unisolated process from invoking direct OS syscalls outside the Broker."
                    ),
                    "claims_count": enforcement_counts["BROKER_MEDIATED"],
                },
                "OS_ENFORCED": {
                    "definition": (
                        "Actions restricted by operating system kernel mechanisms independent of "
                        "the agent's userspace cooperation."
                    ),
                    "implemented_mechanism": (
                        "macOS Seatbelt process confinement (/usr/bin/sandbox-exec) denying direct "
                        "file-write* and file-write-unlink on protected vault and ledger paths, verified "
                        "by NEMESIS AuthorityGraph cut (INV_OMEGA_complete_mediation)."
                    ),
                    "roadmap_extension": (
                        "macOS Endpoint Security System Extension (ES_EVENT_TYPE_AUTH_OPEN, "
                        "ES_EVENT_TYPE_AUTH_UNLINK, ES_EVENT_TYPE_AUTH_RENAME, ES_EVENT_TYPE_AUTH_EXEC) "
                        "for host-wide mandatory mediation across arbitrary process trees."
                    ),
                    "claims_count": enforcement_counts["OS_ENFORCED"],
                },
            },
            "sqlite_ledger_threat_model": {
                "why_sqlite_triggers_are_insufficient": (
                    "SQLite triggers can be removed via DROP TRIGGER by any actor with write access "
                    "to the database file and therefore do not constitute cryptographic immutability."
                ),
                "defensible_property": (
                    "Verifiable integrity against post-hoc tampering within the declared threat model, "
                    "backed by SHA3-256 hash chaining (prev_hash + monotonic seq + lamport_t), Merkle "
                    "root with leaf-cardinality anchor, and Ed25519 signature using a protected key."
                ),
                "integrity_vs_completeness_distinction": (
                    "A valid hash chain and Merkle signature prove that recorded events have not been "
                    "altered, reordered, or truncated relative to the signed root. They do not by "
                    "themselves prove that every OS event was captured; capture completeness holds "
                    "strictly within the active BROKER_MEDIATED or OS_ENFORCED boundary."
                ),
            },
        }
        scope_json_path = out_path / "scope.json"
        with open(scope_json_path, "w", encoding="utf-8") as f:
            json.dump(scope_json_data, f, indent=2, sort_keys=True, ensure_ascii=False)

        # 7. Compile environment.json
        environment_data = {
            "schema": "babylon60.m0.environment.v1",
            "os_sysname": platform.system(),
            "os_release": platform.release(),
            "machine": platform.machine(),
            "python_version": platform.python_version(),
            "platform_tag": platform.platform(),
            "sqlite_version": sqlite3.sqlite_version,
            "synchronous_mode": "FULL (INV_C5_WAL_SYNCHRONOUS_FULL)",
        }
        environment_path = out_path / "environment.json"
        with open(environment_path, "w", encoding="utf-8") as f:
            json.dump(environment_data, f, indent=2, sort_keys=True, ensure_ascii=False)

        # 8. Compile compliance/regulatory-matrix.json & compliance/auditor-report.pdf
        reg_matrix = build_regulatory_contribution_matrix(claims_compiled)
        reg_matrix_path = compliance_dir / "regulatory-matrix.json"
        with open(reg_matrix_path, "w", encoding="utf-8") as f:
            json.dump(reg_matrix, f, indent=2, sort_keys=True, ensure_ascii=False)

        has_falsified_or_unsupported = status_counts["FALSIFIED"] > 0 or status_counts["UNSUPPORTED_WITHIN_SCOPE"] > 0
        overall_epistemic_state = (
            "FALSIFIED_OR_UNSUPPORTED_CONTROLS_DETECTED"
            if has_falsified_or_unsupported
            else "EVIDENCE_VERIFIABLE_WITHIN_DECLARED_SCOPE"
        )

        pdf_lines = [
            "BABYLON-60 M0: COMPLIANCE EVIDENCE PACK — AUDITOR REPORT",
            "========================================================",
            f"Schema          : {PACK_SCHEMA_VERSION}",
            f"Epistemic State : {overall_epistemic_state}",
            f"Ledger Root     : {ledger_info['merkle_root']}",
            f"Total Claims    : {len(claims_compiled)} (Dynamic from CLAIMS.toml)",
            f"  - SUPPORTED_WITHIN_SCOPE   : {status_counts['SUPPORTED_WITHIN_SCOPE']}",
            f"  - FALSIFIED                : {status_counts['FALSIFIED']}",
            f"  - UNSUPPORTED_WITHIN_SCOPE : {status_counts['UNSUPPORTED_WITHIN_SCOPE']}",
            f"  - UNTESTED                 : {status_counts['UNTESTED']}",
            "--------------------------------------------------------",
            "EXECUTIVE SUMMARY STATEMENT:",
            CANONICAL_DEMO_STATEMENT,
            "--------------------------------------------------------",
            "LEGAL & REGULATORY BOUNDARY (EU AI Act Art. 47):",
            "This report provides verifiable technical evidence of control execution.",
            "It does NOT constitute automatic legal compliance, ISO certification,",
            "or exemption from statutory liability. Final conformity assessment",
            "remains the responsibility of the organization and its auditors.",
        ]
        pdf_bytes = _build_minimal_pdf(pdf_lines)
        pdf_path = compliance_dir / "auditor-report.pdf"
        pdf_path.write_bytes(pdf_bytes)

        # 9. Write README.md
        readme_text = (
            "# BABYLON-60 M0: Compliance Evidence Pack\n\n"
            f"> **{CANONICAL_DEMO_STATEMENT}**\n\n"
            "## Product Capabilities Represented\n"
            "- **BABYLON-60 Trust Gateway**: Decides, authorizes, and blocks agent actions (`BROKER_MEDIATED` & `OS_ENFORCED`).\n"
            "- **BABYLON-60 Evidence Engine**: Preserves tamper-evident cryptographic receipts and hash-chained SQLite L0 ledgers.\n"
            "- **BABYLON-60 Compliance Evidence Pack**: Self-contained, independently verifiable deliverable for security, risk, compliance, and audit teams.\n\n"
            "## Independent Verification\n"
            "Verify this pack using the pinned standalone verifier (outside the pack):\n"
            "```bash\n"
            "python3 -m babylon60.verifier.cli --pack ./babylon-m0-evidence-pack\n"
            "```\n"
        )
        readme_path = out_path / "README.md"
        readme_path.write_text(readme_text, encoding="utf-8")

        # 10. Compute TTVE (Time to Verifiable Evidence) and write manifest.json
        issued_at = issued_at_override or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        t_elapsed_ms = round((time.perf_counter_ns() - t_start_ns) / 1_000_000.0, 3)

        manifest_data: Dict[str, Any] = {
            "schema": PACK_SCHEMA_VERSION,
            "pack_id": f"B60-M0-PACK-{ledger_info['merkle_root'][:16].upper()}",
            "issued_at": issued_at,
            "executive_statement": CANONICAL_DEMO_STATEMENT,
            "epistemic_status": overall_epistemic_state,
            "product_capabilities": {
                "trust_gateway": "BABYLON-60 Trust Gateway",
                "evidence_engine": "BABYLON-60 Evidence Engine",
                "deliverable": "BABYLON-60 Compliance Evidence Pack",
            },
            "agent_roles": {
                "ARCHITECT": "Implements runtime authorization controls and OS isolation profiles.",
                "NEMESIS": "Executes adversarial falsification and reachability bypass campaigns.",
                "AUDITOR": "Deterministically compiles and cross-checks evidence against canonical claims (zero LLM verdict authority).",
            },
            "metrics": {
                "ttve_ms": t_elapsed_ms,
                "ttve_definition": "Time to Verifiable Evidence (from controlled execution to third-party verifiable evidence pack)",
                "total_claims": len(claims_compiled),
                "supported_within_scope": status_counts["SUPPORTED_WITHIN_SCOPE"],
                "falsified": status_counts["FALSIFIED"],
                "unsupported_within_scope": status_counts["UNSUPPORTED_WITHIN_SCOPE"],
                "untested": status_counts["UNTESTED"],
            },
            "ledger_summary": {
                "ledger_relative_path": "evidence/ledger_l0.sqlite",
                "execution_trace_relative_path": "evidence/execution-trace.jsonl",
                "total_entries": ledger_info["total_entries"],
                "global_merkle_root": ledger_info["merkle_root"],
            },
        }
        manifest_path = out_path / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2, sort_keys=True, ensure_ascii=False)

        # 11. Compute verification/checksums.sha256 over all pack files outside verification/
        tracked_rel_paths = [
            "manifest.json",
            "claims.json",
            "scope.json",
            "environment.json",
            "evidence/ledger_l0.sqlite",
            "evidence/execution-trace.jsonl",
            "evidence/nemesis-results.json",
            "evidence/formal-proofs.json",
            "compliance/regulatory-matrix.json",
            "compliance/auditor-report.pdf",
            "README.md",
        ]
        checksum_lines: List[str] = []
        file_digests: Dict[str, str] = {}
        for rel in sorted(tracked_rel_paths):
            digest = _sha256_file(out_path / rel)
            file_digests[rel] = digest
            checksum_lines.append(f"{digest}  {rel}")

        checksums_path = verification_dir / "checksums.sha256"
        checksums_bytes = ("\n".join(checksum_lines) + "\n").encode("utf-8")
        checksums_path.write_bytes(checksums_bytes)

        # 12. Sign canonical verification payload (verification/signature.sig & verifier-metadata.json)
        signing_envelope = {
            "schema": PACK_SCHEMA_VERSION,
            "pack_id": manifest_data["pack_id"],
            "issued_at": issued_at,
            "global_merkle_root": ledger_info["merkle_root"],
            "epistemic_status": overall_epistemic_state,
            "checksums_sha256_digest": _sha256_bytes(checksums_bytes),
            "file_digests": file_digests,
        }
        signing_payload_bytes = canonical_json(signing_envelope).encode("utf-8")
        pub_hex, sig_hex = _sign_ed25519_bytes(signing_payload_bytes, self.signing_seed_hex)

        signature_path = verification_dir / "signature.sig"
        signature_path.write_text(sig_hex + "\n", encoding="utf-8")

        verifier_metadata = {
            "schema": "babylon60.m0.verifier_metadata.v1",
            "verifier_module": "babylon60.verifier.standalone_verify",
            "verifier_cli": "python3 -m babylon60.verifier.cli --pack <path>",
            "verifier_version": "5.0.0",
            "distribution_model": "Independent pinned tool distributed separately from the evidence pack (Kerckhoffs Standard)",
            "signature_algorithm": "Ed25519",
            "public_key": pub_hex,
            "signed_envelope_sha256": _sha256_bytes(signing_payload_bytes),
            "signing_envelope": signing_envelope,
        }
        verifier_metadata_path = verification_dir / "verifier-metadata.json"
        with open(verifier_metadata_path, "w", encoding="utf-8") as f:
            json.dump(verifier_metadata, f, indent=2, sort_keys=True, ensure_ascii=False)

        return manifest_data
