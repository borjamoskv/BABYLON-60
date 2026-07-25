import logging
import sys
import webbrowser
from babylon60.core.license_gate import TIER_PRICES, SovereignLicenseGate, Tier

def print_status():
    gate = SovereignLicenseGate()
    status = gate.get_status()
    logging.info('\n⚡ BABYLON-60 SOVEREIGN EXERGY LICENSE STATUS')
    logging.info('=' * 48)
    logging.info(f'  Active Tier:       {status.tier}')
    logging.info(f'  License Owner:     {status.owner}')
    logging.info(f'  Operations Today:  {status.ops_today} / {status.ops_limit}')
    logging.info(f'  Status Signature:  {status.signature}')
    if status.tier == Tier.COMMUNITY:
        logging.info('\n  ⚠️ Operating on Free Community Tier.')
        logging.info('  Upgrade to Pro/Enterprise for unlimited BFT memory:')
        logging.info('  $ babylon60 buy pro\n')
    else:
        logging.info('\n  ✓ Sovereign Tier Verified. Zero-anergy BFT state active.\n')

def activate_license(key_str: str):
    gate = SovereignLicenseGate()
    logging.info(f'[*] Verifying Sovereign License Key: {key_str[:16]}...')
    if gate.activate_key(key_str):
        status = gate.get_status()
        logging.info(f"[+] SUCCESS: Tier '{status.tier}' activated for {status.owner}!")
    else:
        logging.info('[-] ERROR: Invalid or expired Sovereign License Key.')
        sys.exit(1)

def buy_license(tier_name: str='pro'):
    tier_upper = tier_name.upper()
    target_tier = Tier.PRO_SWARM if 'PRO' in tier_upper else Tier.ENTERPRISE if 'ENT' in tier_upper else Tier.DEVELOPER
    price = TIER_PRICES.get(target_tier, 199)
    url = 'https://babylon60.com/#pricing'
    logging.info(f'\n⚡ Opening Payment Gateway for {target_tier} (€{price}/mes)...')
    logging.info(f'  Direct Link: {url}\n')
    try:
        webbrowser.open(url)
    except (OSError, RuntimeError):
        pass

def print_purchases():
    import json
    from pathlib import Path
    log_path = Path.home() / '.babylon60' / 'purchase_notifications.json'
    logging.info('\n💰 BABYLON-60 REVENUE & PURCHASES LEDGER')
    logging.info('=' * 48)
    if not log_path.exists():
        logging.info('  Sin ventas registradas aún. Esperando primeras compras...\n')
        return
    try:
        with open(log_path, encoding='utf-8') as f:
            purchases = json.load(f)
        total_eur = sum((p.get('amount_eur', 0) for p in purchases))
        logging.info(f'  Ventas Totales:    {len(purchases)}')
        logging.info(f'  Ingresos Totales:  €{total_eur} EUR\n')
        logging.info('  Detalle de Compras:')
        for idx, p in enumerate(purchases[-10:], 1):
            logging.info(f"   {idx}. [{p.get('timestamp')}] {p.get('customer_email')} — €{p.get('amount_eur')} ({p.get('tier')})")
        logging.info('')
    except (json.JSONDecodeError, OSError):
        logging.info('  Error al leer el registro de ventas.\n')

def main(args: list[str]=None):
    if args is None:
        args = sys.argv[1:]
    if not args or args[0] in ('status', '--status'):
        print_status()
    elif args[0] == 'auth':
        if len(args) < 2:
            logging.info('Usage: babylon60 auth <SOVEREIGN_LICENSE_KEY>')
            sys.exit(1)
        activate_license(args[1])
    elif args[0] in ('buy', 'upgrade'):
        tier = args[1] if len(args) > 1 else 'pro'
        buy_license(tier)
    elif args[0] in ('purchases', 'sales', 'revenue'):
        print_purchases()
    else:
        logging.info('Usage: babylon60 [status | auth <KEY> | buy <tier> | purchases]')
if __name__ == '__main__':
    main()