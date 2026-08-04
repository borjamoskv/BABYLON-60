"""
Unit tests for compliance_exporter and attestation modules (BABYLON-60 v4.0).
"""

import os
import tempfile
from babylon60.compliance_exporter import EUAIActComplianceExporter
from babylon60.attestation import MerkleCausalAnchor


def test_eu_ai_act_compliance_exporter_nominal():
    exporter = EUAIActComplianceExporter(artifact_bundle_path="/tmp/non_existent_bundle")
    cert = exporter.generate_certificate("system_agent_01", "Bank_EU_Operator")

    assert cert["compliance_standard"] == "EU AI Act (Regulation EU 2024/1689)"
    assert cert["system_identifier"] == "system_agent_01"
    assert cert["operator"] == "Bank_EU_Operator"
    assert "Article_9_Risk_Management" in cert["articles_compliance"]
    assert "Article_12_Record_Keeping_Logging" in cert["articles_compliance"]
    assert cert["articles_compliance"]["Article_12_Record_Keeping_Logging"]["status"] == "COMPLIANT"


def test_eu_ai_act_markdown_export():
    exporter = EUAIActComplianceExporter(artifact_bundle_path="/tmp/non_existent_bundle")
    cert = exporter.generate_certificate("system_agent_01", "Bank_EU_Operator")

    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = os.path.join(tmpdir, "compliance_report.md")
        result = exporter.export_markdown_report(cert, report_path)
        assert os.path.exists(result)
        with open(result, "r", encoding="utf-8") as f:
            content = f.read()
            assert "EU AI Act Compliance Certificate" in content
            assert "Art. 12" in content


def test_merkle_causal_anchor_tpm_quote():
    anchor = MerkleCausalAnchor(tpm_pcr_index=10)
    root_hash = "a3f8c1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0"
    quote = anchor.generate_hardware_pcr_quote(root_hash)

    assert quote["pcr_index"] == "10"
    assert quote["hardware_enclave"] == "TPM_2_0_HARDWARE_SEALED"
    assert len(quote["tpm_quote_signature"]) == 64


def test_merkle_causal_anchor_checkpoint():
    anchor = MerkleCausalAnchor()
    root_hash = "a3f8c1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0"
    chk = anchor.generate_notary_checkpoint(root_hash, "ethereum_l2_sepolia")

    assert chk["attestation_status"] == "CHECKPOINT_SEALED"
    assert chk["target_network"] == "ethereum_l2_sepolia"
