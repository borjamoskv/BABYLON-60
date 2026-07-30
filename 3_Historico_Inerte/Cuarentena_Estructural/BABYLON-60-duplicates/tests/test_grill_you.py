# C5-REAL EXERGY CERTIFIED
"""
Unit tests for babylon60.commands.grill_you
"""

from babylon60.commands.grill_you import run_grill_you, GrillYouReport


def test_grill_you_execution():
    report = run_grill_you(topic="Test Architecture")
    assert isinstance(report, GrillYouReport)
    assert report.topic == "Test Architecture"
    assert report.exergy_score == 1000.0
    assert len(report.decisions) == 3
    assert len(report.taint_hash) == 64


def test_grill_you_yaml_output():
    report = run_grill_you(topic="AgencyHypervisor")
    yaml_text = report.to_yaml()
    assert "Claim: Auto-entrevista" in yaml_text
    assert "AgencyHypervisor" in yaml_text
    assert "CORTEX_TAINT" in yaml_text
    assert "INV_C5_18" in yaml_text
