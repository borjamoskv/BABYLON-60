"""
BABYLON-60 v4.0 Compliance Exporter — Multi-Country & Multi-Locale EU AI Act Audit Generator
Generates verifiable, cryptographically sealed compliance reports for EU AI Act Articles 9, 10, 11, 12, 14
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
from typing import Any, Dict, cast, Optional, List
from .i18n import get_translation
from babylon60.attestation.merkle_anchor import MerkleCausalAnchor

STATUS_UNVERIFIED = "UNVERIFIED_NO_LEDGER"
STATUS_MISMATCH = "EVIDENCE_MISMATCH_NON_COMPLIANT"


def _canonical_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


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

        if key_name and isinstance(val, str):
            kn_lower = key_name.lower()
            if "private" in kn_lower or "pk_" in kn_lower:
                return "[REDACTED_PRIVATE_KEY]"
            if "aws" in kn_lower:
                return "[REDACTED_AWS_AKIA]"
            if re.search(r"(?i)(key|secret|token|password|bearer|auth|cred)", kn_lower):
                return "[REDACTED_AUDIT_SAFE]"

        if isinstance(val, str):
            # Redact API keys, bearer tokens, secret patterns, and private keys inline
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
        elif isinstance(val, dict):
            return {k: EUAIActComplianceExporter.redact_sensitive_data(v, key_name=k) for k, v in val.items()}
        elif isinstance(val, list):
            return [EUAIActComplianceExporter.redact_sensitive_data(v) for v in val]
        return val

    def load_manifest(self) -> Dict[str, Any]:
        """Loads manifest.json or quarantine manifest from the bundle directory, applying sanitization."""
        quarantine_manifest = os.path.join(self.bundle_path, "quarantine", "manifest.json")
        standard_manifest = os.path.join(self.bundle_path, "manifest.json")

        data: Dict[str, Any] = {}
        if os.path.exists(quarantine_manifest):
            with open(quarantine_manifest, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["_is_quarantine"] = True
        elif os.path.exists(standard_manifest):
            with open(standard_manifest, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["_is_quarantine"] = False
        else:
            raise FileNotFoundError(
                f"No valid artifact bundle or manifest found at '{self.bundle_path}'. "
                "Compliance certificates cannot be generated without an audited evidence bundle."
            )
        return cast(dict[str, object], self.redact_sensitive_data(data))

    # ------------------------------------------------------------------
    # FIX B-3: real evidence verification (fail-closed)
    # ------------------------------------------------------------------
    def verify_evidence(self, manifest: Dict[str, Any], ledger_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Re-runs the cryptographic verification of the underlying ledger and binds
        the certificate to the ACTUAL state of the evidence:

        1. Loads the CortexPersistLedger at ``ledger_path``.
        2. Recomputes the full SHA3-256 hash chain (``verify_integrity``).
        3. Recomputes the Merkle root and compares it against the manifest's
           ``global_hash``.

        The certificate is only eligible for CONFORME/COMPLIANT article statuses
        when ``verified`` is True. Any failure (missing ledger, broken chain,
        Merkle mismatch, exception) yields ``verified == False`` and the calling
        certificate degrades every article to UNVERIFIED / NON_COMPLIANT.
        """
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
            ledger = CortexPersistLedger(resolved)
            attestation = ledger.get_state_attestation()
            result["ledger_present"] = True
            result["integrity_verified"] = bool(attestation["integrity_verified"])
            result["ledger_merkle_root"] = attestation["merkle_root"]
            result["ledger_total_entries"] = attestation["total_entries"]
            result["ledger_max_lamport"] = attestation["max_lamport"]

            if global_hash and global_hash != "UNKNOWN_HASH":
                result["evidence_match"] = attestation["merkle_root"] == global_hash
            else:
                # Sin hash de referencia no hay binding posible: no verificable.
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
        """
        Signs the canonical-JSON serialization of the certificate with Ed25519.

        Key resolution:
          - ``BABYLON60_SIGNING_SEED`` (64 hex chars = 32-byte seed) → stable key.
          - Otherwise an ephemeral key is generated and flagged ``ephemeral: true``
            (suitable for demos/tests, NOT for production attestation).
        """
        from nacl.signing import SigningKey

        seed_hex = os.environ.get("BABYLON60_SIGNING_SEED", "").strip()
        ephemeral = True
        if seed_hex:
            try:
                signing_key = SigningKey(bytes.fromhex(seed_hex))
                ephemeral = False
            except Exception:
                signing_key = SigningKey.generate()
        else:
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
        is_quarantined = manifest.get("_is_quarantine", False)

        verification = self.verify_evidence(manifest, ledger_path)
        verified = verification["verified"]

        timestamp_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        valid_until_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + validity_days * 86400))

        # Compute certificate fingerprint
        cert_data = f"{system_id}|{operator_name}|{global_hash}|{timestamp_iso}|{locale}"
        cert_fingerprint = hashlib.sha256(cert_data.encode("utf-8")).hexdigest()

        status_str = t["quarantine_sealed"] if is_quarantined else t["quarantine_nominal"]

        status_pass = t["status_pass"]
        status_halt = "CRITICAL_HALT_NON_COMPLIANT" if not is_quarantined else "QUARANTINE_NON_COMPLIANT"

        # FIX B-3: los artículos solo pasan a CONFORME si la evidencia fue
        # verificada criptográficamente contra el ledger real.
        if verified:
            art9_status = status_pass if not is_quarantined else status_halt
            art12_status = status_pass if not is_quarantined else status_halt
            art10_status = status_pass
            art11_status = status_pass
            art14_status = status_pass
        else:
            unverified = verification["detail"]
            art9_status = unverified
            art10_status = unverified
            art11_status = unverified
            art12_status = unverified
            art14_status = unverified

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
    def verify_certificate_lifecycle(cert: Dict[str, Any], crl: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Verifies certificate lifecycle status (expiration and revocation).
        Returns: { 'valid': bool, 'status': str, 'reason': str }
        """
        cert_id = cert.get("certificate_id", "")
        valid_until = cert.get("valid_until")

        # 1. Check revocation list
        if crl and cert_id in crl:
            return {
                "valid": False,
                "status": "REVOKED",
                "reason": f"Certificate {cert_id} is present in Certificate Revocation List (CRL)",
            }

        # 2. Check expiration date
        if valid_until:
            try:
                exp_ts = time.mktime(time.strptime(valid_until, "%Y-%m-%dT%H:%M:%SZ"))
                if time.time() > exp_ts:
                    return {
                        "valid": False,
                        "status": "EXPIRED",
                        "reason": f"Certificate expired on {valid_until}",
                    }
            except Exception as e:
                import logging

                logging.error(f"Ignored error parsing expiration date: {e}")

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
        """
        Generates a Decision-Evidence Packet (DEP) conforming to Causal Evidentiary
        Governance (CEG / arXiv:2609.01040), cryptographically binding a specific
        agent action to the ledger root via an O(log N) Merkle inclusion proof.
        """
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

        md = f"""# {cert["title"]}
**{t["compliance_standard"]}**  
**Autoridad de Supervisión:** `{cert["supervisory_authority"]}`  
**ID Informe:** `{cert["report_id"]}`  
**Sistema:** `{cert["system_identifier"]}` | **Operador:** `{cert["operator"]}`  
**Emisión:** `{cert["issued_at"]}` | **Estado de Cuarentena:** `{cert["quarantine_status"]}`  

> **DESCARGO LEGAL / LEGAL DISCLAIMER**  
> {cert.get("legal_disclaimer", t["legal_disclaimer"])}

---

## {t["executive_summary_title"]}

{t["executive_summary_text"]}

- **Global Merkle Root:** `{cert["global_merkle_root"]}`
- **Firma Digital (Fingerprint):** `{cert["cryptographic_attestation"]["fingerprint"]}`

---

## Verificación Criptográfica de la Evidencia

| Parámetro | Valor |
| :--- | :--- |
| Ledger | `{v.get("ledger_path")}` |
| Cadena íntegra (verify_integrity) | `{v.get("integrity_verified")}` |
| Merkle root recomputado | `{v.get("ledger_merkle_root")}` |
| Coincide con global_hash del manifiesto | `{v.get("evidence_match")}` |
| **Veredicto** | **{v.get("detail")}** |

---

## Anclaje Criptográfico de Hardware y Ciclo de Vida

| Parámetro | Valor |
| :--- | :--- |
| Enclave de Hardware | `{hw.get("hardware_enclave")}` |
| Hardware UUID | `{hw.get("hardware_uuid")}` |
| Plataforma / Modelo | `{hw.get("platform")}` |
| Válido Hasta (Expiración 90d) | `{cert.get("valid_until")}` |
| Estado de Revocación | `{rev.get("status")}` |
| Hash de Verificación de Revocación | `{rev.get("check_hash")}` |
| Autoridad de Revocación | `{rev.get("revocation_authority")}` |

---

## Firma Ed25519 del Certificado

- **Algoritmo:** `{sig.get("algorithm")}` | **Clave efímera:** `{sig.get("ephemeral")}`
- **Clave pública:** `{sig.get("public_key")}`
- **Firma:** `{sig.get("signature", "")[:64]}...`
- **SHA-256 del payload firmado:** `{sig.get("signed_payload_sha256")}`

---

## Matriz de Cumplimiento Regulatorio

| Requisito / Artículo | Mecanismo Técnico BABYLON-60 v4.0 | Estado | Hash de Evidencia |
| :--- | :--- | :--- | :--- |
| **{cert["articles_compliance"]["Article_9_Risk_Management"]["title"]}** | {cert["articles_compliance"]["Article_9_Risk_Management"]["mechanism"]} | {cert["articles_compliance"]["Article_9_Risk_Management"]["status"]} | `{cert["articles_compliance"]["Article_9_Risk_Management"]["evidence_hash"][:16]}...` |
| **{cert["articles_compliance"]["Article_10_Data_Governance"]["title"]}** | {cert["articles_compliance"]["Article_10_Data_Governance"]["mechanism"]} | {cert["articles_compliance"]["Article_10_Data_Governance"]["status"]} | `{cert["articles_compliance"]["Article_10_Data_Governance"]["evidence_hash"][:16]}...` |
| **{cert["articles_compliance"]["Article_11_Technical_Documentation"]["title"]}** | {cert["articles_compliance"]["Article_11_Technical_Documentation"]["mechanism"]} | {cert["articles_compliance"]["Article_11_Technical_Documentation"]["status"]} | `{cert["articles_compliance"]["Article_11_Technical_Documentation"]["evidence_hash"][:16]}...` |
| **{cert["articles_compliance"]["Article_12_Record_Keeping_Logging"]["title"]}** | {cert["articles_compliance"]["Article_12_Record_Keeping_Logging"]["mechanism"]} | {cert["articles_compliance"]["Article_12_Record_Keeping_Logging"]["status"]} | `{cert["articles_compliance"]["Article_12_Record_Keeping_Logging"]["evidence_hash"][:16]}...` |
| **{cert["articles_compliance"]["Article_14_Human_Oversight"]["title"]}** | {cert["articles_compliance"]["Article_14_Human_Oversight"]["mechanism"]} | {cert["articles_compliance"]["Article_14_Human_Oversight"]["status"]} | `{cert["articles_compliance"]["Article_14_Human_Oversight"]["evidence_hash"][:16]}...` |

---

<sub>BABYLON-60 v4.0 C5-REAL Compliance Transducer — {cert["supervisory_authority"]}</sub>
"""
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(md)
        return output_filepath

    def export_html_report(self, cert: Dict[str, Any], output_filepath: str, locale: str = "es") -> str:
        """Exports localized certificate into a visually stunning, printable HTML report."""
        t = get_translation(locale)
        v = cert.get("evidence_verification", {})
        sig = cert.get("signature", {})

        rows = ""
        for art_key, art_val in cert["articles_compliance"].items():
            status_str = str(art_val["status"])
            status_badge = (
                '<span class="badge badge-success">✅ ' + status_str + "</span>"
                if "PASS" in status_str
                or "CUMPLIDO" in status_str
                or status_str == "CONFORME"
                or status_str == "COMPLIANT"
                else '<span class="badge badge-danger">❌ ' + status_str + "</span>"
            )
            rows += f"""
            <tr>
                <td><strong>{art_val["title"]}</strong></td>
                <td>{art_val["mechanism"]}</td>
                <td>{status_badge}</td>
                <td><code>{art_val["evidence_hash"][:16]}...</code></td>
            </tr>
            """

        verdict = str(v.get("detail", "UNVERIFIED"))
        verdict_ok = verdict == "VERIFIED"
        verdict_badge = (
            f'<span class="badge badge-success">✅ {verdict}</span>'
            if verdict_ok
            else f'<span class="badge badge-danger">❌ {verdict}</span>'
        )

        html = f"""<!DOCTYPE html>
<html lang="{locale}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{cert["title"]} - {cert["certificate_id"]}</title>
    <style>
        :root {{
            --bg-color: #0b0f19;
            --card-bg: rgba(18, 26, 43, 0.85);
            --accent: #00F0FF;
            --text: #e2e8f0;
            --muted: #94a3b8;
            --success: #10b981;
            --danger: #ef4444;
            --border: rgba(255, 255, 255, 0.1);
        }}
        body {{
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background-color: var(--bg-color);
            color: var(--text);
            margin: 0;
            padding: 2rem;
            line-height: 1.6;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 2.5rem;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
        }}
        .header {{
            border-bottom: 1px solid var(--border);
            padding-bottom: 1.5rem;
            margin-bottom: 2rem;
        }}
        h1 {{
            color: #fff;
            margin: 0 0 0.5rem 0;
            font-size: 1.8rem;
            letter-spacing: -0.025em;
        }}
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            font-weight: 600;
        }}
        .badge-success {{ background: rgba(16, 185, 129, 0.2); color: var(--success); border: 1px solid var(--success); }}
        .badge-danger {{ background: rgba(239, 68, 68, 0.2); color: var(--danger); border: 1px solid var(--danger); }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        .card {{
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
        }}
        .card-title {{ font-size: 0.8rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }}
        .card-value {{ font-size: 1rem; font-weight: 600; color: #fff; margin-top: 0.25rem; font-family: monospace; word-break: break-all; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}
        th, td {{
            text-align: left;
            padding: 0.75rem 1rem;
            border-bottom: 1px solid var(--border);
        }}
        th {{ background: rgba(255, 255, 255, 0.05); color: var(--muted); font-size: 0.85rem; text-transform: uppercase; }}
        code {{ background: rgba(0, 240, 255, 0.1); color: var(--accent); padding: 0.2rem 0.4rem; border-radius: 4px; font-family: monospace; }}
        .footer {{
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
            font-size: 0.8rem;
            color: var(--muted);
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📜 {cert["title"]}</h1>
            <p style="color: var(--accent); font-weight: 600; margin: 0;">{t["compliance_standard"]}</p>
        </div>

        <div class="grid">
            <div class="card">
                <div class="card-title">ID Certificado</div>
                <div class="card-value">{cert["certificate_id"]}</div>
            </div>
            <div class="card">
                <div class="card-title">Sistema Auditado</div>
                <div class="card-value">{cert["system_identifier"]}</div>
            </div>
            <div class="card">
                <div class="card-title">Operador / Entidad</div>
                <div class="card-value">{cert["operator"]}</div>
            </div>
            <div class="card">
                <div class="card-title">Fecha Emisión</div>
                <div class="card-value">{cert["issued_at"]}</div>
            </div>
        </div>

        <h2>Executive Summary</h2>
        <p>{t["executive_summary_text"]}</p>
        <p><strong>Global Merkle Root:</strong> <code>{cert["global_merkle_root"]}</code></p>
        <p><strong>Cryptographic Fingerprint:</strong> <code>{cert["cryptographic_attestation"]["fingerprint"]}</code></p>

        <h2 style="margin-top: 2rem;">Verificación de la Evidencia</h2>
        <table>
            <tbody>
                <tr><td><strong>Ledger</strong></td><td><code>{v.get("ledger_path")}</code></td></tr>
                <tr><td><strong>Cadena íntegra</strong></td><td><code>{v.get("integrity_verified")}</code></td></tr>
                <tr><td><strong>Merkle recomputado</strong></td><td><code>{v.get("ledger_merkle_root")}</code></td></tr>
                <tr><td><strong>Coincide con manifiesto</strong></td><td><code>{v.get("evidence_match")}</code></td></tr>
                <tr><td><strong>Veredicto</strong></td><td>{verdict_badge}</td></tr>
            </tbody>
        </table>

        <h2 style="margin-top: 2rem;">Firma Ed25519</h2>
        <table>
            <tbody>
                <tr><td><strong>Algoritmo</strong></td><td><code>{sig.get("algorithm")}</code> (efímera: <code>{sig.get("ephemeral")}</code>)</td></tr>
                <tr><td><strong>Clave pública</strong></td><td><code>{sig.get("public_key")}</code></td></tr>
                <tr><td><strong>SHA-256 payload</strong></td><td><code>{sig.get("signed_payload_sha256")}</code></td></tr>
            </tbody>
        </table>

        <h2 style="margin-top: 2rem;">Matriz de Cumplimiento Normativo EU AI Act</h2>
        <table>
            <thead>
                <tr>
                    <th>Artículo / Requisito</th>
                    <th>Mecanismo Técnico BABYLON-60</th>
                    <th>Estado</th>
                    <th>Evidencia Hash</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>

        <div class="footer">
            BABYLON-60 v4.0 C5-REAL Compliance Transducer — {cert["supervisory_authority"]}
        </div>
    </div>
</body>
</html>
"""
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        with open(output_filepath, "w", encoding="utf-8") as f:
            f.write(html)
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
    parser.add_argument("--output", help="Ruta del archivo de salida")

    args = parser.parse_args()

    exporter = EUAIActComplianceExporter(artifact_bundle_path=args.bundle, ledger_path=args.ledger)
    cert = exporter.generate_certificate(system_id=args.system_id, operator_name=args.operator, locale=args.locale)

    out_path = args.output
    if not out_path:
        ext = args.format if args.format != "md" else "md"
        out_path = f"compliance_cert_{args.system_id}.{ext}"

    if args.format == "json":
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(cert, f, indent=2, ensure_ascii=False)
    elif args.format == "md":
        exporter.export_markdown_report(cert, out_path, locale=args.locale)
    elif args.format == "html":
        exporter.export_html_report(cert, out_path, locale=args.locale)

    verification = cert.get("evidence_verification", {})
    detail = verification.get("detail", STATUS_UNVERIFIED)
    print(f"[+] Certificado EU AI Act generado con éxito en: {out_path}")
    if detail == "VERIFIED":
        print("[✓] Evidencia VERIFICADA criptográficamente contra el ledger (fail-closed).")
        return 0
    if verification.get("ledger_present"):
        print(f"[✗] FALLO DE VERIFICACIÓN DE EVIDENCIA: {detail}. Certificado emitido como NO CONFORME.")
        return 2
    print(f"[!] AVISO: evidencia NO verificada ({detail}). Los artículos figuran como UNVERIFIED.")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main_cli())
