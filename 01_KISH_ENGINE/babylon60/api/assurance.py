"""
BABYLON-60 Ergonomic API — Assurance Levels (Sprints 2 & 4).
RFC-B60-2026-01-ADOPTION-ARCHITECTURE (Iceberg Pattern).

Defines graduated assurance levels balancing cryptographic guarantees
against operational latency overhead.
"""

from enum import Enum
from typing import Any, Dict


class AssuranceLevel(str, Enum):
    """
    Assurance Levels for autonomous agents and AI pipelines in BABYLON-60.

    Levels:
    - AL0_TRANSPARENT: In-memory/local SQLite SHA-256 hashing (<0.05ms).
      Zero crypto overhead for development and testing.
    - AL1_STANDARD: Incremental linear hash chain (<0.3ms) for low-risk
      agents (FAQs, basic triage, customer support).
    - AL2_COMPLIANCE: Default level for EU AI Act compliance (Articles 9-15).
      Micro-batching and Ed25519 session signing (<1.0ms amortized).
    - AL3_SOVEREIGN: Maximum per-call cryptography + hardware anchor
      (Secure Enclave / TPM PCRs) for critical infrastructure and defense.
    """

    AL0_TRANSPARENT = "AL0_TRANSPARENT"
    AL1_STANDARD = "AL1_STANDARD"
    AL2_COMPLIANCE = "AL2_COMPLIANCE"
    AL3_SOVEREIGN = "AL3_SOVEREIGN"

    @property
    def target_overhead_ms(self) -> float:
        """Maximum expected runtime overhead in milliseconds."""
        overhead_map = {
            self.AL0_TRANSPARENT: 0.05,
            self.AL1_STANDARD: 0.3,
            self.AL2_COMPLIANCE: 1.0,
            self.AL3_SOVEREIGN: 5.0,
        }
        return overhead_map[self]

    @property
    def requires_signature(self) -> bool:
        """Whether this level requires Ed25519 digital signatures."""
        return self in (self.AL2_COMPLIANCE, self.AL3_SOVEREIGN)

    @property
    def requires_hardware_anchor(self) -> bool:
        """Whether this level requires a physical hardware enclave or PCR anchor."""
        return self == self.AL3_SOVEREIGN

    @property
    def requires_hash_chain(self) -> bool:
        """Whether this level maintains an incremental hash chain across events."""
        return self in (self.AL1_STANDARD, self.AL2_COMPLIANCE, self.AL3_SOVEREIGN)

    @property
    def requires_merkle_batching(self) -> bool:
        """Whether this level aggregates events into balanced Merkle trees."""
        return self in (self.AL2_COMPLIANCE, self.AL3_SOVEREIGN)

    def describe(self) -> Dict[str, Any]:
        """Returns structured metadata describing the assurance properties."""
        descriptions: Dict[AssuranceLevel, Dict[str, Any]] = {
            self.AL0_TRANSPARENT: {
                "level": "AL0_TRANSPARENT",
                "overhead_target": "<0.05ms",
                "hashing": "SHA-256 local",
                "signing": "None",
                "hardware_anchor": False,
                "use_case": "Development, Local Testing, CI/CD",
                "compliance_scope": "Internal Observability",
            },
            self.AL1_STANDARD: {
                "level": "AL1_STANDARD",
                "overhead_target": "<0.3ms",
                "hashing": "Incremental SHA-256 Hash Chain",
                "signing": "None",
                "hardware_anchor": False,
                "use_case": "Low-risk Agents, FAQs, Customer Triage",
                "compliance_scope": "Tamper-Evident History",
            },
            self.AL2_COMPLIANCE: {
                "level": "AL2_COMPLIANCE",
                "overhead_target": "<1.0ms amortized",
                "hashing": "Batch Merkle Trees (SHA-256 / SHA3-256)",
                "signing": "Ed25519 Session Digest",
                "hardware_anchor": False,
                "use_case": "EU AI Act High-Risk Systems (Articles 9-15)",
                "compliance_scope": "Regulatory Self-Assessment & Audit Dossier",
            },
            self.AL3_SOVEREIGN: {
                "level": "AL3_SOVEREIGN",
                "overhead_target": "<5.0ms",
                "hashing": "Per-step SHA3-256 + Balanced Merkle Tree",
                "signing": "Ed25519 Per-call & Session",
                "hardware_anchor": True,
                "use_case": "Critical Infrastructure, Defense, Financial Execution",
                "compliance_scope": "Full Cryptographic Sovereign Ledger",
            },
        }
        return descriptions[self]

    @classmethod
    def parse(cls, value: Any) -> "AssuranceLevel":
        """
        Tolerantly parses a string or enum into a canonical AssuranceLevel.
        Accepts strings like 'al0', 'AL0', 'al2', 'compliance', 'sovereign', etc.
        """
        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise TypeError(f"Expected str or AssuranceLevel, got {type(value).__name__}")

        normalized = value.strip().upper()
        # Direct name match
        for member in cls:
            if member.name == normalized or member.value == normalized:
                return member

        # Shorthand matching
        shorthands: Dict[str, AssuranceLevel] = {
            "AL0": cls.AL0_TRANSPARENT,
            "TRANSPARENT": cls.AL0_TRANSPARENT,
            "DEV": cls.AL0_TRANSPARENT,
            "AL1": cls.AL1_STANDARD,
            "STANDARD": cls.AL1_STANDARD,
            "BASIC": cls.AL1_STANDARD,
            "AL2": cls.AL2_COMPLIANCE,
            "COMPLIANCE": cls.AL2_COMPLIANCE,
            "EU_AI_ACT": cls.AL2_COMPLIANCE,
            "AL3": cls.AL3_SOVEREIGN,
            "SOVEREIGN": cls.AL3_SOVEREIGN,
            "HARDWARE": cls.AL3_SOVEREIGN,
        }
        if normalized in shorthands:
            return shorthands[normalized]

        raise ValueError(f"Unknown AssuranceLevel: '{value}'. Valid: {[m.value for m in cls]}")
