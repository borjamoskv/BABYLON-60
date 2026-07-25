import sys
import webbrowser
from typing import List
from babylon60.core.license_gate import SovereignLicenseGate, Tier, TIER_PRICES, TIER_LIMITS

def print_status():
    gate = SovereignLicenseGate()
    status = gate.get_status()
    print('\n⚡ BABYLON-60 SOVEREIGN EXERGY LICENSE STATUS')
    print('=' * 48)
    print(f'  Active Tier:       {status.tier}')
    print(f'  License Owner:     {status.owner}')
    print(f'  Operations Today:  {status.ops_today} / {status.ops_limit}')
    print(f'  Status Signature:  {status.signature}')
    if status.tier == Tier.COMMUNITY:
        print('\n  ⚠️ Operating on Free Community Tier.')
        print('  Upgrade to Pro/Enterprise for unlimited BFT memory:')
        print('  $ babylon60 buy pro\n')
    else:
        print('\n  ✓ Sovereign Tier Verified. Zero-anergy BFT state active.\n')

def activate_license(key_str: str):
    gate = SovereignLicenseGate()
    print(f'[*] Verifying Sovereign License Key: {key_str[:16]}...')
    if gate.activate_key(key_str):
        status = gate.get_status()
        print(f"[+] SUCCESS: Tier '{status.tier}' activated for {status.owner}!")
    else:
        print('[-] ERROR: Invalid or expired Sovereign License Key.')
        sys.exit(1)

def buy_license(tier_name: str='pro'):
    tier_upper = tier_name.upper()
    target_tier = Tier.PRO_SWARM if 'PRO' in tier_upper else Tier.ENTERPRISE if 'ENT' in tier_upper else Tier.DEVELOPER
    price = TIER_PRICES.get(target_tier, 199)
    url = 'https://babylon60.com/#pricing'
    print(f'\n⚡ Opening Payment Gateway for {target_tier} (€{price}/mes)...')
    print(f'  Direct Link: {url}\n')
    try:
        webbrowser.open(url)
    except (OSError, RuntimeError):
        pass

def print_purchases():
    import json
    from pathlib import Path
    log_path = Path.home() / ".babylon60" / "purchase_notifications.json"
    
    print("\n💰 BABYLON-60 REVENUE & PURCHASES LEDGER")
    print("=" * 48)
    if not log_path.exists():
        print("  Sin ventas registradas aún. Esperando primeras compras...\n")
        return

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            purchases = json.load(f)
        
        total_eur = sum(p.get("amount_eur", 0) for p in purchases)
        print(f"  Ventas Totales:    {len(purchases)}")
        print(f"  Ingresos Totales:  €{total_eur} EUR\n")
        print("  Detalle de Compras:")
        for idx, p in enumerate(purchases[-10:], 1):
            print(f"   {idx}. [{p.get('timestamp')}] {p.get('customer_email')} — €{p.get('amount_eur')} ({p.get('tier')})")
        print("")
    except (json.JSONDecodeError, OSError):
        print("  Error al leer el registro de ventas.\n")

def main(args: List[str]=None):
    if args is None:
        args = sys.argv[1:]
    if not args or args[0] in ('status', '--status'):
        print_status()
    elif args[0] == 'auth':
        if len(args) < 2:
            print('Usage: babylon60 auth <SOVEREIGN_LICENSE_KEY>')
            sys.exit(1)
        activate_license(args[1])
    elif args[0] in ('buy', 'upgrade'):
        tier = args[1] if len(args) > 1 else 'pro'
        buy_license(tier)
    elif args[0] in ('purchases', 'sales', 'revenue'):
        print_purchases()
    else:
        print('Usage: babylon60 [status | auth <KEY> | buy <tier> | purchases]')
if __name__ == '__main__':
    main()