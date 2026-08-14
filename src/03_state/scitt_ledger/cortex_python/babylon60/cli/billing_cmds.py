# C5-REAL EXERGY CERTIFIED
"""GCP Billing & Identity Diagnostic Commands (Axiom Ω5 & Ω9 Compliant)."""
import json
import click
from primitives.bash_primitive import BashCommand
from babylon60.cli.common import cli, console

def _print_billing_account(b_acc: dict):
    is_open = b_acc.get("open", False)
    state_str = "[bold green]OPEN[/bold green]" if is_open else "[bold red]CLOSED/SUSPENDED[/bold red]"
    raw_name = b_acc.get('name', '')
    acc_id = raw_name.replace("billingAccounts/", "")
    display = b_acc.get('displayName', '')
    console.print(f"  • Name: {raw_name} | Display: [bold]{display}[/bold] | Open: {state_str}")
    if not is_open:
        console.print(f"    ├─ Direct Payment Link: [blue]https://console.cloud.google.com/billing/{acc_id}/payment[/blue]")
        console.print(f"    └─ Account Manage Link: [blue]https://console.cloud.google.com/billing/{acc_id}/manage[/blue]")

@cli.command(name="billing")
@click.option("--account", default=None, help="GCP Account email to set as active before checking")
def billing(account: str | None):
    """Diagnose GCP Cloud Identity and Billing Accounts status under Axiom Ω9."""
    console.print("--- [bold cyan]C5-REAL GCP BILLING DIAGNOSTIC PROTOCOL (Ω9)[/bold cyan] ---")

    if account:
        console.print(f"[yellow]■ Setting active gcloud account to:[/yellow] {account}")
        BashCommand(binary="gcloud", args=("config", "set", "account", account), check=False).execute()

    console.print("\n[bold green]■ Checking gcloud Auth List...[/bold green]")
    auth_proc = BashCommand(binary="gcloud", args=("auth", "list", "--format=json"), check=False).execute()
    if auth_proc.returncode == 0 and auth_proc.stdout.strip():
        try:
            accounts = json.loads(auth_proc.stdout)
            for acc in accounts:
                status = "[bold green]ACTIVE[/bold green]" if acc.get("status") == "ACTIVE" else "[dim]INACTIVE[/dim]"
                console.print(f"  • Account: {acc.get('account')} | Status: {status}")
        except Exception:
            console.print(auth_proc.stdout)
    else:
        console.print(f"[bold red]Auth Check Failed:[/bold red] {auth_proc.stderr}")

    console.print("\n[bold green]■ Checking GCP Billing Accounts & Direct Resolution URLs...[/bold green]")
    billing_proc = BashCommand(binary="gcloud", args=("billing", "accounts", "list", "--format=json"), check=False).execute()
    if billing_proc.returncode == 0 and billing_proc.stdout.strip():
        try:
            b_accounts = json.loads(billing_proc.stdout)
            for b_acc in b_accounts:
                _print_billing_account(b_acc)
        except Exception:
            console.print(billing_proc.stdout)
    else:
        console.print(f"[yellow]Billing Check Alert:[/yellow] {billing_proc.stderr.strip()}")
        console.print("[bold red]➜ Invoke /browser on https://console.cloud.google.com/billing per Axiom Ω9[/bold red]")
