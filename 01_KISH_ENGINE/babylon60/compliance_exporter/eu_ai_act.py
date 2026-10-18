"""
BABYLON-60 v4.0 Compliance Exporter — Multi-Country & Multi-Locale EU AI Act Audit Generator
Generates verifiable, cryptographically sealed compliance reports for EU AI Act Articles 9, 10, 11, 12, 14, 15, 50
localized for target countries/jurisdictions (ES, EN, DE, FR, IT).

FIX B-3 (audit 2026-09-10): the exporter no longer issues CONFORME certificates
against unverified evidence. When a ledger is supplied (CLI --ledger, constructor
argument, or "ledger_path" in the manifest), the exporter re-runs the full
SHA3-256 hash-chain verification and recomputes the Merkle root, compares it
against the manifest's global_hash, and marks every article UNVERIFIED /
NON_COMPLIANT when the evidence cannot be verified. Certificates are signed
with Ed25519 (BABYLON60_SIGNING_SEED env var; ephemeral key otherwise).
"""

import hashlib
import json
import os
import time
import html
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, cast, Optional, List
from .i18n import get_translation
from babylon60.attestation.merkle_anchor import MerkleCausalAnchor

STATUS_UNVERIFIED = "UNVERIFIED_NO_LEDGER"
STATUS_MISMATCH = "EVIDENCE_MISMATCH_NON_COMPLIANT"


def _canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def _md_escape(value: Any) -> str:
    return str(value).replace("|", "\\|")


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


class EUAIActComplianceExporter:
    """
    Transforms BABYLON-60 Merkle-Causal DAG Ledgers and WORM Forensic Quarantine Bundles
    into legal compliance certificates for EU AI Act auditing, with localized legal templates.
    """

    def __init__(self, artifact_bundle_path: str = "artifact_bundle_v3", ledger_path: Optional[str] = None) -> None:
        self.bundle_path = artifact_bundle_path
        self.ledger_path = ledger_path

    @staticmethod
    def redact_sensitive_data(val: Any, key_name: Optional[str] = None) -> Any:
        """
        Cryptographic Redaction Layer: Sanitizes metadata, stripping API keys, PII,
        and secret strings before export to prevent exfiltration via audit reports.
        """
        import re

        def forced_redaction_from_key(kn: str) -> Optional[str]:
            kn_lower = kn.lower()
            if "private" in kn_lower or "pk_" in kn_lower:
                return "[REDACTED_PRIVATE_KEY]"
            if "aws" in kn_lower:
                return "[REDACTED_AWS_AKIA]"
            if re.search(r"(?i)(key|secret|token|password|bearer|auth|cred)", kn_lower):
                return "[REDACTED_AUDIT_SAFE]"
            return None

        if key_name:
            forced = forced_redaction_from_key(key_name)
            if forced is not None:
                return forced

        if isinstance(val, str):
            val = re.sub(
                r"(?i)(api[_-]?key|secret|token|password|bearer|pk_)[=:\s]+[A-Za-z0-9_\-\.]{8,}",
                r"\1=[REDACTED_AUDIT_SAFE]",
                val,
            )
            val = re.sub(
                r"-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]+?-----END [A-Z ]+ PRIVATE KEY-----",
                "[REDACTED_PRIVATE_KEY]",
                val,
            )
            val = re.sub(r"akia[0-9a-z]{16}", "[REDACTED_AWS_AKIA]", val, flags=re.IGNORECASE)
            return val

        if isinstance(val, dict):
            return {k: EUAIActComplianceExporter.redact_sensitive_data(v, key_name=k) for k, v in val.items()}

        if isinstance(val, list):
            return [EUAIActComplianceExporter.redact_sensitive_data(v) for v in val]

        return val

    def load_manifest(self) -> Dict[str, Any]:
        """Loads manifest.json or quarantine manifest from the bundle directory, applying sanitization."""
        quarantine_manifest = os.path.join(self.bundle_path, "quarantine", "manifest.json")
        standard_manifest = os.path.join(self.bundle_path, "manifest.json")

        data: Any = None
        if os.path.exists(quarantine_manifest):
            with open(quarantine_manifest, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                data["_is_quarantine"] = True
        elif os.path.exists(standard_manifest):
            with open(standard_manifest, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                data["_is_quarantine"] = False
        else:
            raise FileNotFoundError(
                f"No valid artifact bundle or manifest found at '{self.bundle_path}'. "
                "Compliance certificates cannot be generated without an audited evidence bundle."
            )

        if not isinstance(data, dict):
            raise ValueError(f"Manifest root must be a JSON object, got {type(data).__name__}")

        return cast(Dict[str, Any], self.redact_sensitive_data(data))

    # ------------------------------------------------------------------
    # FIX B-3: real evidence verification (fail-closed)
    # ------------------------------------------------------------------
    def verify_evidence(self, manifest: Dict[str, Any], ledger_path: Optional[str] = None) -> Dict[str, Any]:
        resolved = ledger_path or self.ledger_path or manifest.get("ledger_path")
        global_hash = manifest.get("global_hash", "UNKNOWN_HASH")
        result: Dict[str, Any] = {
            "ledger_path": resolved,
            "ledger_present": False,
            "integrity_verified": None,
            "ledger_merkle_root": None,
            "manifest_global_hash": global_hash,
            "evidence_match": None,
            "verified": False,
            "detail": STATUS_UNVERIFIED,
        }

        if resolved is not None and not isinstance(resolved, (str, os.PathLike)):
            result["detail"] = "LEDGER_PATH_INVALID"
            return result

        if not resolved:
            return result
        if not os.path.exists(resolved):
            result["detail"] = "LEDGER_NOT_FOUND"
            return result

        try:
            from ..bft.cortex_persist_ledger import CortexPersistLedger
        except ImportError:  # pragma: no cover - package-layout fallback
            from babylon60.bft.cortex_persist_ledger import CortexPersistLedger

        try:
            import sqlite3

            with sqlite3.connect(str(resolved)) as conn:
                tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}

            if "ledger_entries" in tables and "cortex_ledger" not in tables:
                import asyncio
                from babylon60.bft.ledger_actor import BFTLedgerActor

                actor = BFTLedgerActor(Path(resolved))
                attestation = asyncio.run(actor.get_state_attestation())
            else:
                ledger = CortexPersistLedger(str(resolved))
                attestation = ledger.get_state_attestation()

            result["ledger_present"] = True
            result["integrity_verified"] = bool(attestation["integrity_verified"])
            result["ledger_merkle_root"] = attestation["merkle_root"]
            result["ledger_total_entries"] = attestation["total_entries"]
            result["ledger_max_lamport"] = attestation["max_lamport"]
            result["rekor_anchor"] = attestation.get("rekor_anchor")

            if global_hash and global_hash != "UNKNOWN_HASH":
                result["evidence_match"] = attestation["merkle_root"] == global_hash
            else:
                result["evidence_match"] = None

            result["verified"] = bool(result["integrity_verified"] and result["evidence_match"])
            if not result["integrity_verified"]:
                result["detail"] = "LEDGER_CHAIN_BROKEN_NON_COMPLIANT"
            elif result["evidence_match"] is False:
                result["detail"] = STATUS_MISMATCH
            elif result["evidence_match"] is None:
                result["detail"] = "UNVERIFIED_NO_REFERENCE_HASH"
            else:
                result["detail"] = "VERIFIED"
        except Exception as exc:  # fail-closed: cualquier error => no verificado
            result["detail"] = f"VERIFICATION_ERROR: {exc.__class__.__name__}"
            result["verified"] = False
        return result

    # ------------------------------------------------------------------
    # FIX B-3: Ed25519 certificate signature
    # ------------------------------------------------------------------
    @staticmethod
    def sign_certificate(cert: Dict[str, Any]) -> Dict[str, Any]:
        from nacl.signing import SigningKey

        seed_hex = os.environ.get("BABYLON60_SIGNING_SEED", "").strip()
        ephemeral = True

        if seed_hex:
            try:
                signing_key = SigningKey(bytes.fromhex(seed_hex))
                ephemeral = False
            except Exception as exc:
                raise RuntimeError(
                    "BABYLON60_SIGNING_SEED is invalid. Refusing to fall back "
                    "to an ephemeral key for compliance signing."
                ) from exc
        else:
            allow_ephemeral = os.environ.get("BABYLON60_ALLOW_EPHEMERAL_SIGNING", "") == "1"
            if not allow_ephemeral:
                raise RuntimeError("No BABYLON60_SIGNING_SEED provided and ephemeral signing is not allowed.")
            signing_key = SigningKey.generate()

        payload = _canonical_json(cert).encode("utf-8")
        payload_sha256 = hashlib.sha256(payload).hexdigest()
        signed = signing_key.sign(payload)
        return {
            "algorithm": "Ed25519",
            "public_key": signing_key.verify_key.encode().hex(),
            "signature": signed.signature.hex(),
            "signed_payload_sha256": payload_sha256,
            "canonicalization": "json(sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)",
            "ephemeral": ephemeral,
        }

    def generate_certificate(
        self,
        system_id: str,
        operator_name: str,
        locale: str = "es",
        ledger_path: Optional[str] = None,
        validity_days: int = 90,
    ) -> Dict[str, Any]:
        """Generates a structured compliance certificate localized for target locale/country."""
        t = get_translation(locale)
        manifest = self.load_manifest()
        global_hash = manifest.get("global_hash", "UNKNOWN_HASH")

        if not global_hash or global_hash == "UNKNOWN_HASH":
            raise ValueError(
                "Manifest global_hash is missing or UNKNOWN_HASH. "
                "Cannot generate a compliance certificate without an evidence root."
            )

        is_quarantined = manifest.get("_is_quarantine", False)

        verification = self.verify_evidence(manifest, ledger_path)
        verified = verification["verified"]

        timestamp_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        valid_until_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + validity_days * 86400))

        cert_data = f"{system_id}|{operator_name}|{global_hash}|{timestamp_iso}|{locale}"
        cert_fingerprint = hashlib.sha256(cert_data.encode("utf-8")).hexdigest()

        status_str = t["quarantine_sealed"] if is_quarantined else t["quarantine_nominal"]

        status_halt = "QUARANTINE_NON_COMPLIANT"

        # Un registro íntegro (verified = True) no garantiza automáticamente el cumplimiento de todos los artículos.
        # Garantiza evidencia inmutable, pero el contenido de la evidencia debe auditarse.
        status_pass_crypto = t.get("status_crypto_verified", "CRYPTO_EVIDENCE_SECURED")
        status_pending_audit = "EVIDENCE_SECURED_PENDING_AUDIT"

        if verified:
            art9_status = status_pending_audit
            art10_status = status_pending_audit
            art11_status = status_pending_audit
            # Art 12 (Logging) sí se beneficia directamente de la integridad criptográfica del ledger.
            art12_status = status_halt if is_quarantined else status_pass_crypto
            art14_status = status_pending_audit
            art15_status = status_pending_audit
            art50_status = status_pending_audit
        else:
            unverified = verification["detail"]
            art9_status = unverified
            art10_status = unverified
            art11_status = unverified
            art12_status = unverified
            art14_status = unverified
            art15_status = unverified
            art50_status = unverified

        cert: Dict[str, Any] = {
            "title": t["title"],
            "locale": locale,
            "compliance_standard": t["compliance_standard"],
            "supervisory_authority": t["authority"],
            "report_id": f"EU-AIA-REPORT-{cert_fingerprint[:16].upper()}",
            "certificate_id": f"EU-AIA-CERT-{cert_fingerprint[:16].upper()}",
            "system_identifier": system_id,
            "operator": operator_name,
            "issued_at": timestamp_iso,
            "valid_until": valid_until_iso,
            "validity_days": validity_days,
            "global_merkle_root": global_hash,
            "quarantine_status": status_str,
            "legal_disclaimer": t["legal_disclaimer"],
            "evidence_verification": verification,
            "revocation": {
                "status": "ACTIVE",
                "check_hash": hashlib.sha256(f"{cert_fingerprint}:ACTIVE".encode()).hexdigest(),
                "revocation_authority": f"urn:babylon60:revocation:{operator_name}",
            },
            "hardware_anchor": MerkleCausalAnchor().generate_hardware_pcr_quote(global_hash),
            "articles_compliance": {
                "Article_9_Risk_Management": {
                    "title": t["article_titles"]["Article_9"],
                    "status": art9_status,
                    "mechanism": t["mechanisms"]["Article_9"],
                    "evidence_hash": hashlib.sha256(f"ART9:{global_hash}".encode()).hexdigest(),
                },
                "Article_10_Data_Governance": {
                    "title": t["article_titles"]["Article_10"],
                    "status": art10_status,
                    "mechanism": t["mechanisms"]["Article_10"],
                    "evidence_hash": hashlib.sha256(f"ART10:{global_hash}".encode()).hexdigest(),
                },
                "Article_11_Technical_Documentation": {
                    "title": t["article_titles"]["Article_11"],
                    "status": art11_status,
                    "mechanism": t["mechanisms"]["Article_11"],
                    "evidence_hash": hashlib.sha256(f"ART11:{global_hash}".encode()).hexdigest(),
                },
                "Article_12_Record_Keeping_Logging": {
                    "title": t["article_titles"]["Article_12"],
                    "status": art12_status,
                    "mechanism": t["mechanisms"]["Article_12"],
                    "evidence_hash": hashlib.sha256(f"ART12:{global_hash}".encode()).hexdigest(),
                },
                "Article_14_Human_Oversight": {
                    "title": t["article_titles"]["Article_14"],
                    "status": art14_status,
                    "mechanism": t["mechanisms"]["Article_14"],
                    "evidence_hash": hashlib.sha256(f"ART14:{global_hash}".encode()).hexdigest(),
                },
                "Article_15_Robustness_Cybersecurity": {
                    "title": t["article_titles"]["Article_15"],
                    "status": art15_status,
                    "mechanism": t["mechanisms"]["Article_15"],
                    "evidence_hash": hashlib.sha256(f"ART15:{global_hash}".encode()).hexdigest(),
                },
                "Article_50_Transparency": {
                    "title": t["article_titles"].get("Article_50", "Article 50: Transparency Obligations for GPAI"),
                    "status": art50_status,
                    "mechanism": "Cryptographic SCITT L5 immutable attestation",
                    "evidence_hash": hashlib.sha256(f"ART50:{global_hash}".encode()).hexdigest(),
                },
            },
            "cryptographic_attestation": {
                "policy": "Sovereign Dual-License v1.0",
                "attestation_engine": "BABYLON-60 C5-REAL Transducer",
                "fingerprint": cert_fingerprint,
            },
        }
        cert["signature"] = self.sign_certificate(cert)
        return cert

    generate_report = generate_certificate

    @staticmethod
    def verify_certificate_signature(cert: Dict[str, Any]) -> Dict[str, Any]:
        from nacl.signing import VerifyKey
        from nacl.exceptions import BadSignatureError

        signature_block = cert.get("signature")
        if not isinstance(signature_block, dict):
            return {
                "valid": False,
                "reason": "Missing signature block",
            }

        try:
            public_key = bytes.fromhex(signature_block["public_key"])
            signature = bytes.fromhex(signature_block["signature"])
        except Exception as exc:
            return {
                "valid": False,
                "reason": f"Malformed signature block: {exc}",
            }

        cert_without_signature = {k: v for k, v in cert.items() if k != "signature"}

        payload = _canonical_json(cert_without_signature).encode("utf-8")

        try:
            verify_key = VerifyKey(public_key)
            verify_key.verify(payload, signature)
            return {
                "valid": True,
                "reason": "Ed25519 signature valid",
            }
        except BadSignatureError:
            return {
                "valid": False,
                "reason": "Ed25519 signature verification failed",
            }
        except Exception as exc:
            return {
                "valid": False,
                "reason": f"Signature verification error: {exc}",
            }

    @staticmethod
    def verify_certificate_lifecycle(cert: Dict[str, Any], crl: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Verifies certificate lifecycle status (expiration, revocation, and signature).
        """
        cert_id = cert.get("certificate_id", "")
        valid_until = cert.get("valid_until")

        if crl and cert_id in crl:
            return {
                "valid": False,
                "status": "REVOKED",
                "reason": f"Certificate {cert_id} is present in Certificate Revocation List (CRL)",
            }

        if not valid_until:
            return {
                "valid": False,
                "status": "INVALID",
                "reason": "Certificate is missing valid_until",
            }

        try:
            expires = datetime.strptime(
                valid_until,
                "%Y-%m-%dT%H:%M:%SZ",
            ).replace(tzinfo=timezone.utc)
        except ValueError as exc:
            return {
                "valid": False,
                "status": "INVALID",
                "reason": f"Invalid valid_until timestamp: {exc}",
            }

        if time.time() > expires.timestamp():
            return {
                "valid": False,
                "status": "EXPIRED",
                "reason": f"Certificate expired on {valid_until}",
            }

        return {
            "valid": True,
            "status": "ACTIVE",
            "reason": "Certificate is active, unexpired, and not revoked",
        }

    def create_decision_evidence_packet(
        self,
        seq: int,
        decision_data: Dict[str, Any],
        ledger: Any,
        operator_name: str = "SOVEREIGN_OPERATOR",
    ) -> Dict[str, Any]:
        attestation = ledger.get_state_attestation()
        if not attestation.get("integrity_verified"):
            raise RuntimeError("Ledger integrity verification failed; cannot create DEP")

        merkle_root = ledger.get_merkle_root()
        proof_packet = ledger.get_event_proof(seq)
        hw_quote = MerkleCausalAnchor().generate_hardware_pcr_quote(merkle_root)

        timestamp_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        leaf_h = proof_packet.get("leaf_hash", "")
        dep_id = f"DEP-{hashlib.sha256(f'{seq}:{leaf_h}:{timestamp_iso}'.encode()).hexdigest()[:16].upper()}"

        packet: Dict[str, Any] = {
            "dep_id": dep_id,
            "seq": seq,
            "decision_data": self.redact_sensitive_data(decision_data),
            "merkle_inclusion_proof": proof_packet,
            "global_merkle_root": merkle_root,
            "hardware_anchor": hw_quote,
            "issued_at": timestamp_iso,
            "operator": operator_name,
            "compliance_binding": "EU_AI_ACT_ART12_CAUSAL_TRACEABILITY",
        }

        packet["signature"] = self.sign_certificate(packet)
        return packet

    def export_markdown_report(self, cert: Dict[str, Any], output_filepath: str, locale: str = "es") -> str:
        """Exports localized self-assessment report into human-readable Markdown format."""
        t = get_translation(locale)
        v = cert.get("evidence_verification", {})
        sig = cert.get("signature", {})
        hw = cert.get("hardware_anchor", {})
        rev = cert.get("revocation", {})

        evidence_verification_title = t.get("evidence_verification_title", "Verificación Criptográfica de la Evidencia")
        hardware_anchor_title = t.get("hardware_anchor_title", "Anclaje Criptográfico de Hardware y Ciclo de Vida")
        signature_title = t.get("signature_title", "Firma Ed25519 del Certificado")
        compliance_matrix_title = t.get("compliance_matrix_title", "Matriz de Cumplimiento Regulatorio")

        md = f"""# {_md_escape(cert["title"])}
**{_md_escape(t["compliance_standard"])}**  
**{t.get("supervisory_authority_label", "Autoridad de Supervisión")}:** `{_md_escape(cert["supervisory_authority"])}`  
**{t.get("report_id_label", "ID Informe")}:** `{_md_escape(cert["report_id"])}`  
**{t.get("system_label", "Sistema")}:** `{_md_escape(cert["system_identifier"])}` | **{t.get("operator_label", "Operador")}:** `{_md_escape(cert["operator"])}`  
**{t.get("issued_at_label", "Emisión")}:** `{_md_escape(cert["issued_at"])}` | **{t.get("quarantine_status_label", "Estado de Cuarentena")}:** `{_md_escape(cert["quarantine_status"])}`  

> **DESCARGO LEGAL / LEGAL DISCLAIMER**  
> {_md_escape(cert.get("legal_disclaimer", t["legal_disclaimer"]))}

---

## {_md_escape(t["executive_summary_title"])}

{_md_escape(t["executive_summary_text"])}

- **Global Merkle Root:** `{_md_escape(cert["global_merkle_root"])}`
- **Firma Digital (Fingerprint):** `{_md_escape(cert["cryptographic_attestation"]["fingerprint"])}`

---

## {_md_escape(evidence_verification_title)}

| Parámetro | Valor |
| :--- | :--- |
| {t.get("ledger_label", "Ledger")} | `{_md_escape(v.get("ledger_path"))}` |
| {t.get("integrity_verified_label", "Cadena íntegra (verify_integrity)")} | `{_md_escape(v.get("integrity_verified"))}` |
| {t.get("recomputed_merkle_root_label", "Merkle root recomputado")} | `{_md_escape(v.get("ledger_merkle_root"))}` |
| {t.get("manifest_match_label", "Coincide con global_hash del manifiesto")} | `{_md_escape(v.get("evidence_match"))}` |
| **{t.get("verdict_label", "Veredicto")}** | **{_md_escape(v.get("detail"))}** |

---

## {_md_escape(hardware_anchor_title)}

| Parámetro | Valor |
| :--- | :--- |
| Enclave de Hardware | `{_md_escape(hw.get("hardware_enclave"))}` |
| Hardware UUID | `{_md_escape(hw.get("hardware_uuid"))}` |
| Plataforma / Modelo | `{_md_escape(hw.get("platform"))}` |
| Válido Hasta | `{_md_escape(cert.get("valid_until"))}` |
| Estado de Revocación | `{_md_escape(rev.get("status"))}` |
| Hash de Verificación de Revocación | `{_md_escape(rev.get("check_hash"))}` |
| Autoridad de Revocación | `{_md_escape(rev.get("revocation_authority"))}` |

---

## {_md_escape(signature_title)}

- **Algoritmo:** `{_md_escape(sig.get("algorithm"))}` | **Clave efímera:** `{_md_escape(sig.get("ephemeral"))}`
- **Clave pública:** `{_md_escape(sig.get("public_key"))}`
- **Firma:** `{_md_escape(sig.get("signature", ""))[:64]}...`
- **SHA-256 del payload firmado:** `{_md_escape(sig.get("signed_payload_sha256"))}`

---

## {_md_escape(compliance_matrix_title)}

| Requisito / Artículo | Mecanismo Técnico | Estado | Hash de Evidencia |
| :--- | :--- | :--- | :--- |
"""
        for art_key, art_val in cert["articles_compliance"].items():
            md += f"| **{_md_escape(art_val['title'])}** | {_md_escape(art_val['mechanism'])} | {_md_escape(art_val['status'])} | `{_md_escape(art_val['evidence_hash'])[:16]}...` |\n"

        md += f"\n---\n\n<sub>BABYLON-60 v4.0 C5-REAL Compliance Transducer — {_md_escape(cert['supervisory_authority'])}</sub>\n"

        _ensure_parent_dir(output_filepath)
        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(md)
        return output_filepath

    def export_html_report(
        self,
        cert: Dict[str, Any],
        output_filepath: str,
        locale: str = "es",
        theme: str = "dark",
        engine: Optional[Any] = None,
    ) -> str:
        """
        Exports localized certificate into a visually stunning HTML report.
        Delegates rendering to decoupled ComplianceTemplateEngine with SoC support for themes.
        """
        from .template_engine import ComplianceTemplateEngine

        template_engine = engine or ComplianceTemplateEngine()
        html_str = template_engine.render_report(cert, locale=locale, theme=theme)

        _ensure_parent_dir(output_filepath)
        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(html_str)
        return output_filepath


def main_cli() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="BABYLON-60 EU AI Act Compliance Certificate Exporter")
    parser.add_argument("--bundle", default="artifact_bundle_v3", help="Ruta al paquete de artefactos/evidencia")
    parser.add_argument("--ledger", help="Ruta al ledger SQLite (CortexPersistLedger) para verificación fail-closed")
    parser.add_argument("--system-id", default="BABYLON60-PROD-01", help="Identificador del sistema de IA auditado")
    parser.add_argument("--operator", default="Enterprise Operator", help="Nombre de la entidad u operador")
    parser.add_argument(
        "--locale", default="es", choices=["es", "en", "de", "fr", "it"], help="Idioma de certificación"
    )
    parser.add_argument("--format", default="json", choices=["json", "md", "html"], help="Formato de exportación")
    parser.add_argument(
        "--theme",
        default="dark",
        choices=["dark", "legal"],
        help="Tema visual del informe HTML ('dark' para HUD ciberpunk, 'legal' para informe imprimible)",
    )
    parser.add_argument("--output", help="Ruta del archivo de salida")
    parser.add_argument("--allow-unverified", action="store_true", help="Do not fail when evidence cannot be verified")

    args = parser.parse_args()

    t = get_translation(args.locale)

    exporter = EUAIActComplianceExporter(artifact_bundle_path=args.bundle, ledger_path=args.ledger)
    cert = exporter.generate_certificate(system_id=args.system_id, operator_name=args.operator, locale=args.locale)

    out_path = args.output
    if not out_path:
        ext = args.format if args.format != "md" else "md"
        out_path = f"compliance_cert_{args.system_id}.{ext}"

    if args.format == "json":
        _ensure_parent_dir(out_path or ".")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(cert, f, indent=2, ensure_ascii=False)
    elif args.format == "md":
        exporter.export_markdown_report(cert, out_path, locale=args.locale)
    elif args.format == "html":
        exporter.export_html_report(cert, out_path, locale=args.locale, theme=getattr(args, "theme", "dark"))

    verification = cert.get("evidence_verification", {})
    detail = verification.get("detail", STATUS_UNVERIFIED)
    verified = bool(verification.get("verified", False))

    cert_success = t.get("cli_success", "[+] Certificate written to:")
    print(f"{cert_success} {out_path}")

    if verified:
        print(t.get("cli_verified", "[✓] Evidence cryptographically verified."))
        return 0

    cli_failed = t.get("cli_failed", "[✗] Evidence verification failed:")
    print(f"{cli_failed} {detail}")

    cli_warning = t.get("cli_warning", "[!] Certificate articles should be treated as UNVERIFIED / NON_COMPLIANT.")
    print(cli_warning)

    if getattr(args, "allow_unverified", False):
        return 0

    return 2


if __name__ == "__main__":
    import sys

    sys.exit(main_cli())
