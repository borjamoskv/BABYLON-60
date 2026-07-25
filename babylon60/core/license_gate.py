import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SOVEREIGN_KEY_SALT = 'CORTEX_C5_REAL_PAYWALL_SALT_2026'

class Tier:
    COMMUNITY = 'COMMUNITY'
    DEVELOPER = 'DEVELOPER'
    PRO_SWARM = 'PRO_SWARM'
    ENTERPRISE = 'ENTERPRISE'
TIER_LIMITS: dict[str, int] = {Tier.COMMUNITY: 1000, Tier.DEVELOPER: 50000, Tier.PRO_SWARM: 1000000, Tier.ENTERPRISE: 999999999}
TIER_PRICES: dict[str, int] = {Tier.DEVELOPER: 49, Tier.PRO_SWARM: 199, Tier.ENTERPRISE: 999}

@dataclass
class LicenseStatus:
    active: bool
    tier: str
    owner: str
    ops_today: int
    ops_limit: int
    expires_at: int
    signature: str

class SovereignLicenseGate:

    def __init__(self, config_dir: str | None=None) -> None:
        if config_dir:
            self.base_dir = Path(config_dir)
        else:
            self.base_dir = Path.home() / '.babylon60'
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.license_file = self.base_dir / 'license.json'
        self.meter_file = self.base_dir / 'usage_meter.json'

    def generate_license_key(self, owner: str, tier: str, valid_days: int=30) -> str:
        expires_at = int(time.time()) + valid_days * 86400
        payload = f'{owner}:{tier}:{expires_at}:{SOVEREIGN_KEY_SALT}'
        sig = hmac.new(SOVEREIGN_KEY_SALT.encode(), payload.encode(), hashlib.sha256).hexdigest()
        key_dict = {'owner': owner, 'tier': tier, 'expires_at': expires_at, 'sig': sig[:32]}
        encoded = json.dumps(key_dict).encode('utf-8').hex()
        return f'B60-{tier[:3]}-{encoded}'

    def verify_license_key(self, key_str: str) -> dict[str, Any] | None:
        if not key_str.startswith('B60-'):
            return None
        try:
            parts = key_str.split('-', 2)
            if len(parts) < 3:
                return None
            hex_data = parts[2]
            raw_json = bytes.fromhex(hex_data).decode('utf-8')
            data = json.loads(raw_json)
            owner = data['owner']
            tier = data['tier']
            expires_at = int(data['expires_at'])
            sig = data['sig']
            payload = f'{owner}:{tier}:{expires_at}:{SOVEREIGN_KEY_SALT}'
            expected_sig = hmac.new(SOVEREIGN_KEY_SALT.encode(), payload.encode(), hashlib.sha256).hexdigest()[:32]
            if not hmac.compare_digest(sig, expected_sig):
                return None
            if time.time() > expires_at:
                return None
            return {'owner': owner, 'tier': tier, 'expires_at': expires_at, 'valid': True}
        except (ValueError, KeyError, json.JSONDecodeError):
            return None

    def activate_key(self, key_str: str) -> bool:
        verified = self.verify_license_key(key_str)
        if not verified:
            return False
        with open(self.license_file, 'w', encoding='utf-8') as f:
            json.dump({'key': key_str, 'activated_at': int(time.time()), 'details': verified}, f, indent=2)
        return True

    def get_status(self) -> LicenseStatus:
        ops_today = self._get_daily_usage()
        if self.license_file.exists():
            try:
                with open(self.license_file, encoding='utf-8') as f:
                    data = json.load(f)
                key_str = data.get('key', '')
                verified = self.verify_license_key(key_str)
                if verified:
                    tier = verified['tier']
                    limit = TIER_LIMITS.get(tier, TIER_LIMITS[Tier.COMMUNITY])
                    return LicenseStatus(active=True, tier=tier, owner=verified['owner'], ops_today=ops_today, ops_limit=limit, expires_at=verified['expires_at'], signature=data.get('details', {}).get('sig', 'C5-VERIFIED'))
            except (json.JSONDecodeError, KeyError, ValueError, OSError):
                pass
        return LicenseStatus(active=True, tier=Tier.COMMUNITY, owner='anonymous_community', ops_today=ops_today, ops_limit=TIER_LIMITS[Tier.COMMUNITY], expires_at=2147483647, signature='COMMUNITY_FREE')

    def record_operation(self, count: int=1) -> bool:
        status = self.get_status()
        if status.ops_today + count > status.ops_limit:
            raise RuntimeError(f"[PAYWALL] Tier '{status.tier}' limit exceeded ({status.ops_today}/{status.ops_limit} ops/day). Upgrade to Pro/Enterprise: https://babylon60.com/#pricing")
        self._increment_usage(count)
        return True

    def _get_daily_usage(self) -> int:
        today = time.strftime('%Y-%m-%d')
        if not self.meter_file.exists():
            return 0
        try:
            with open(self.meter_file, encoding='utf-8') as f:
                data = json.load(f)
            if data.get('date') == today:
                return int(data.get('ops', 0))
        except (json.JSONDecodeError, KeyError, ValueError, OSError):
            pass
        return 0

    def _increment_usage(self, count: int) -> None:
        today = time.strftime('%Y-%m-%d')
        ops = self._get_daily_usage() + count
        with open(self.meter_file, 'w', encoding='utf-8') as f:
            json.dump({'date': today, 'ops': ops}, f)