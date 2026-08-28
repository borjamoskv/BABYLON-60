# C5-REAL EXERGY CERTIFIED
"""Unit tests for cortex_persist.cli.billing_cmds (Axiom Ω5 & Ω9)."""
from click.testing import CliRunner
from babylon60.cli.billing_cmds import billing

def test_billing_cmd_execution():
    """Verify that the billing CLI command invokes and produces Brutalist output."""
    runner = CliRunner()
    result = runner.invoke(billing)
    assert result.exit_code == 0
    assert "C5-REAL GCP BILLING DIAGNOSTIC PROTOCOL" in result.output
    assert "Checking gcloud Auth List" in result.output
    assert "Checking GCP Billing Accounts" in result.output

def test_billing_cmd_with_account_option():
    """Verify that --account option executes without error."""
    runner = CliRunner()
    result = runner.invoke(billing, ["--account", "borjabilbo84@gmail.com"])
    assert result.exit_code == 0
    assert "borjabilbo84@gmail.com" in result.output
