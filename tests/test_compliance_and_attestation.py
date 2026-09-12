"""
Unit tests for compliance_exporter and attestation modules (BABYLON-60 v4.0).
"""

import os
import tempfile
from babylon60.compliance_exporter import EUAIActComplianceExporter
from babylon60.attestation import MerkleCausalAnchor


def test_eu_ai_act_compliance_exporter_locales() -> None:
    import pytest

    exporter_fail = EUAIActComplianceExporter(artifact_bundle_path="/tmp/non_existent_bundle_12345")
    with pytest.raises(FileNotFoundError):
        exporter_fail.generate_certificate("system_agent_01", "Bank_EU_Operator")

    import json
    from babylon60.bft.cortex_persist_ledger import CortexPersistLedger, CortexEvent

    with tempfile.TemporaryDirectory() as bundle_dir:
        ledger_file = os.path.join(bundle_dir, "ledger.db")
        ledger = CortexPersistLedger(ledger_file)
        event = CortexEvent(
            agent_id="system_agent_01",
            event_type="INIT",
            payload={"action": "audit"},
            cortex_taint="T0",
            domain="compliance",
        )
        ledger.append_event(event)
        root = ledger.get_merkle_root()

        manifest_path = os.path.join(bundle_dir, "manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump({"global_hash": root, "ledger_path": ledger_file}, f)

        exporter = EUAIActComplianceExporter(artifact_bundle_path=bundle_dir, ledger_path=ledger_file)
        locales = ["es", "en", "de", "fr", "it"]
        for loc in locales:
            cert = exporter.generate_certificate("system_agent_01", "Bank_EU_Operator", locale=loc)
            assert cert["locale"] == loc
            assert "Article_9_Risk_Management" in cert["articles_compliance"]
            assert cert["articles_compliance"]["Article_9_Risk_Management"]["status"] in [
                "CONFORME",
                "COMPLIANT",
                "KONFORM",
            ]

        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = os.path.join(tmpdir, f"compliance_report_{loc}.md")
            result = exporter.export_markdown_report(cert, report_path, locale=loc)
            assert os.path.exists(result)
            with open(result, "r", encoding="utf-8") as f:
                content = f.read()
                assert len(content) > 100


def test_merkle_causal_anchor_tpm_quote() -> None:
    anchor = MerkleCausalAnchor(tpm_pcr_index=10)
    root_hash = "a3f8c1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0"
    quote = anchor.generate_hardware_pcr_quote(root_hash)

    assert quote["pcr_index"] == "10"
    assert quote["hardware_enclave"].startswith("TPM_2_0_HARDWARE_SEALED")
    assert len(quote["tpm_quote_signature"]) == 64


def test_merkle_causal_anchor_checkpoint() -> None:
    anchor = MerkleCausalAnchor()
    root_hash = "a3f8c1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0"
    chk = anchor.generate_notary_checkpoint(root_hash, "ethereum_l2_sepolia")

    assert chk["attestation_status"] == "CHECKPOINT_SEALED"
    assert chk["target_network"] == "ethereum_l2_sepolia"
