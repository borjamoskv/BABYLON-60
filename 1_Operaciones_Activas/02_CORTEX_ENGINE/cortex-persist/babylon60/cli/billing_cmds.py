# C5-REAL EXERGY CERTIFIED
# [C5-REAL] Exergy-Maximized
"""
CORTEX CLI - Billing & Monetization Commands.

Enables the operator or users to easily upgrade their instance,
trigger Stripe checkout flows (PWYW or standard tiers),
and provision premium API keys.
"""

from __future__ import annotations

import httpx
import click
import webbrowser
from rich.console import Console

from babylon60.cli.common import cli
from babylon60.cli.utils import print_error, print_info, print_success

console = Console()

@cli.command()
@click.option("--plan", "-p", default="pwyw", help="Plan name (pwyw, pro, team)")
@click.option("--amount", "-a", default=0.00, type=float, help="Custom amount for PWYW (USD)")
@click.option("--email", "-e", prompt="Billing email", help="Billing email")
@click.option("--remote", "-r", default="http://localhost:8000", help="CORTEX Endpoint URL")
def upgrade(plan: str, amount: float, email: str, remote: str) -> None:
    """Start a checkout session to upgrade your CORTEX plan."""
    print_info(f"Initiating upgrade to plan '{plan}' (Amount: ${amount:.2f})")

    payload = {
        "plan": plan,
        "customer_email": email,
        "amount_usd": amount,
        "recurring": True,
        "success_url": "https://babylon60.com/success",
        "cancel_url": "https://babylon60.com/cancel",
    }

    try:
        with console.status("Contacting CORTEX Billing Gateway..."):
            resp = httpx.post(f"{remote}/v1/stripe/checkout", json=payload, timeout=10.0)

        if resp.status_code != 200:
            print_error(f"Gateway error ({resp.status_code}): {resp.text}")
            raise click.Abort()

        data = resp.json()
        checkout_url = data.get("url")
        session_id = data.get("session_id")

        if checkout_url:
            if session_id == "free_bypass":
                print_success("Bypass granted. Free tier verified. Enjoy CORTEX!")
            else:
                print_success(f"Session {session_id} created successfully!")
                print_info(f"Opening browser to Stripe Checkout: {checkout_url}")
                webbrowser.open(checkout_url)
                print_info("Once paid, your API key will be provisioned by the webhook.")
        else:
            print_error("No checkout URL returned from the gateway.")
            raise click.Abort()

    except httpx.RequestError as e:  # noqa: BLE001
        print_error(f"Network error while connecting to gateway: {e}")
        raise click.Abort()
