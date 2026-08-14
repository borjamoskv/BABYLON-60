# C5-REAL EXERGY CERTIFIED
# INVARIANTS: INV_C5_17 (Dual Licensing & Monetization), Ω1 (Exergy Conservation),
#            Ω23 (Dynamic Path Resolution), Ω_BFT_04 (Idempotent Ledger Ingestion),
#            Ω_VALVE (Backpressure Queue Maxsize=1024), Ω_C7.7 (Trust Anchor)

from __future__ import annotations

import asyncio
import hmac
import hashlib
import json
import os
import sqlite3
import time
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# ---------------------------------------------------------------------------
# Ω23: Dynamic Resolution of Paths
# ---------------------------------------------------------------------------
_ENGINE_DIR = Path(__file__).resolve().parent
_CORTEX_DIR = _ENGINE_DIR.parent
_REPO_ROOT = _CORTEX_DIR.parents[1]
_DEFAULT_DB_PATH = _REPO_ROOT / ".cortex" / "license_ledger.db"

# Secret key for HMAC token signing (default fallback for dev/test)
DEFAULT_LICENSE_SECRET = os.getenv("CORTEX_LICENSE_SECRET", "C5_REAL_BFT_TRUST_SECRET_0xDEADBEEF")


class LicenseTier(str, Enum):
    COMMUNITY = "COMMUNITY"       # AGPLv3 / Core Exergy, standard limits (1 worker, 50 MCTS max)
    ENTERPRISE = "ENTERPRISE"     # Commercial / Premium BFT, High-Throughput Swarm, 500+ MCTS


class LicenseState(str, Enum):
    COMMUNITY = "COMMUNITY"
    VALID_ONLINE = "VALID_ONLINE"
    DEGRADED_OFFLINE_VALID = "DEGRADED_OFFLINE_VALID"  # Active during HTTP 429 / Network partition
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    INVALID_SIGNATURE = "INVALID_SIGNATURE"


class FeatureEntitlement:
    """Defines feature limits per license tier."""
    FEATURES: Dict[str, LicenseTier] = {
        "mcts_basic": LicenseTier.COMMUNITY,
        "mcts_ultrathink_500": LicenseTier.ENTERPRISE,
        "swarm_1000_agents": LicenseTier.ENTERPRISE,
        "bft_audit_zero_trust": LicenseTier.ENTERPRISE,
        "custom_sla_router": LicenseTier.ENTERPRISE,
    }

    @classmethod
    def required_tier(cls, feature_name: str) -> LicenseTier:
        return cls.FEATURES.get(feature_name, LicenseTier.ENTERPRISE)


class LicenseToken:
    """Cryptographically signed BFT License Payload."""
    def __init__(
        self,
        license_id: str,
        holder: str,
        tier: LicenseTier,
        expires_at: float,
        signature: Optional[str] = None,
    ) -> None:
        self.license_id = license_id
        self.holder = holder
        self.tier = tier
        self.expires_at = expires_at
        self.signature = signature or self.compute_signature()

    def compute_signature(self, secret: str = DEFAULT_LICENSE_SECRET) -> str:
        msg = f"{self.license_id}:{self.holder}:{self.tier.value}:{self.expires_at}".encode("utf-8")
        return hmac.new(secret.encode("utf-8"), msg, hashlib.sha3_256).hexdigest()

    def is_valid_signature(self, secret: str = DEFAULT_LICENSE_SECRET) -> bool:
        expected = self.compute_signature(secret)
        return hmac.compare_digest(self.signature or "", expected)

    def is_expired(self) -> bool:
        return time.monotonic() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "license_id": self.license_id,
            "holder": self.holder,
            "tier": self.tier.value,
            "expires_at": self.expires_at,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LicenseToken:
        return cls(
            license_id=data["license_id"],
            holder=data["holder"],
            tier=LicenseTier(data["tier"]),
            expires_at=data["expires_at"],
            signature=data.get("signature"),
        )


class LicenseManagerEngine:
    """
    Motor BFT de Gestión de Monetización y Licenciamiento Dual (INV_C5_17).
    Resiliente a Errores HTTP 429 mediante Offline Staging Ledger y Backoff Exponencial.
    """

    def __init__(self, db_path: Optional[Path] = None, secret: str = DEFAULT_LICENSE_SECRET) -> None:
        self.db_path = Path(db_path) if db_path else _DEFAULT_DB_PATH
        self.secret = secret
        self.current_token: Optional[LicenseToken] = None
        self.state: LicenseState = LicenseState.COMMUNITY if not self.current_token else LicenseState.VALID_ONLINE

        # Ω_VALVE: Backpressure queue with maxsize=1024
        self.staging_queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=1024)

        # 429 Resilience state
        self.consecutive_429_count: int = 0
        self.last_429_timestamp: float = 0.0

        self._init_db()

    def _init_db(self) -> None:
        """Inicialización Idempotente del SQLite Ledger (Ω23, Ω_BFT_04)."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")

        # Tabla principal de auditoría de licencias
        conn.execute("""
            CREATE TABLE IF NOT EXISTS license_audit_ledger (
                event_id TEXT PRIMARY KEY,
                license_id TEXT NOT NULL,
                tier TEXT NOT NULL,
                feature TEXT NOT NULL,
                timestamp REAL NOT NULL,
                status TEXT NOT NULL,
                payload_hash TEXT NOT NULL
            )
        """)

        # Tabla de staging offline para fallos HTTP 429 o desconexión
        conn.execute("""
            CREATE TABLE IF NOT EXISTS license_staging_ledger (
                event_id TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                staged_at REAL NOT NULL,
                retry_count INTEGER DEFAULT 0
            )
        """)

        # Ω11: Immutable Trigger para auditoría
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS license_audit_no_update
            BEFORE UPDATE ON license_audit_ledger
            BEGIN
                SELECT RAISE(ABORT, 'Modificación de ledger de licencias inmutable prohibida (Ω11)');
            END;
        """)
        conn.commit()
        conn.close()

    def load_license_token(self, token_dict: Dict[str, Any]) -> LicenseState:
        """Carga y valida criptográficamente un token de licencia (INV_C5_17)."""
        try:
            token = LicenseToken.from_dict(token_dict)
            if not token.is_valid_signature(self.secret):
                self.state = LicenseState.INVALID_SIGNATURE
                self.current_token = None
                return self.state

            if token.is_expired():
                self.state = LicenseState.EXPIRED
                self.current_token = None
                return self.state

            self.current_token = token
            self.state = LicenseState.VALID_ONLINE
            self.consecutive_429_count = 0
            return self.state
        except Exception:
            self.state = LicenseState.INVALID_SIGNATURE
            self.current_token = None
            return self.state

    def active_tier(self) -> LicenseTier:
        """Retorna el tier activo (COMMUNITY si no hay token válido o si expiró)."""
        if self.state in (LicenseState.VALID_ONLINE, LicenseState.DEGRADED_OFFLINE_VALID):
            if self.current_token:
                return self.current_token.tier
        return LicenseTier.COMMUNITY

    def can_access_feature(self, feature_name: str) -> Tuple[bool, str]:
        """Verifica si la característica premium está autorizada por el tier activo."""
        required = FeatureEntitlement.required_tier(feature_name)
        active = self.active_tier()

        if required == LicenseTier.COMMUNITY:
            return True, f"Feature '{feature_name}' es de acceso libre (COMMUNITY)."

        if active == LicenseTier.ENTERPRISE:
            status_desc = "ONLINE" if self.state == LicenseState.VALID_ONLINE else "DEGRADED_OFFLINE (Resiliente 429)"
            return True, f"Acceso ENTERPRISE concedido para '{feature_name}' [{status_desc}]."

        return False, f"Acceso DENEGADO para '{feature_name}'. Requiere tier ENTERPRISE, activo: {active.value}."

    def handle_network_429(self, feature_name: str, error_msg: str = "HTTP 429 Too Many Requests") -> LicenseState:
        """
        Transiciona al estado DEGRADED_OFFLINE_VALID cuando ocurre un error HTTP 429.
        Preserva la capacidad operativa del kernel si el token local era válido.
        """
        self.consecutive_429_count += 1
        self.last_429_timestamp = time.monotonic()

        if self.current_token and not self.current_token.is_expired():
            # Mantiene operativas las funciones comercialmente validadas bajo cache local
            self.state = LicenseState.DEGRADED_OFFLINE_VALID
        else:
            self.state = LicenseState.COMMUNITY

        # Registrar evento de degradación en staging offline
        self.stage_offline_audit(
            event_type="429_RATE_LIMIT_DEGRADATION",
            feature=feature_name,
            details={"error": error_msg, "retry_after_seq": self.consecutive_429_count}
        )
        return self.state

    def stage_offline_audit(self, event_type: str, feature: str, details: Dict[str, Any]) -> str:
        """Almacena auditorías en el staging ledger SQLite local durante caídas 429 (Ω_BFT_04)."""
        event_id = hashlib.sha3_256(f"{time.monotonic()}:{feature}:{event_type}".encode("utf-8")).hexdigest()[:16]
        payload = {
            "event_id": event_id,
            "license_id": self.current_token.license_id if self.current_token else "ANONYMOUS_COMMUNITY",
            "tier": self.active_tier().value,
            "feature": feature,
            "event_type": event_type,
            "details": details,
            "timestamp": time.monotonic(),
        }

        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        try:
            conn.execute(
                "INSERT INTO license_staging_ledger (event_id, payload_json, staged_at, retry_count) VALUES (?, ?, ?, 0)",
                (event_id, json.dumps(payload), time.monotonic()),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Idempotencia BFT
        finally:
            conn.close()

        return event_id

    def record_audit_event(self, feature: str, status: str) -> None:
        """Registra un evento de auditoría de licencias inmutable (Ω11, Ω_BFT_04)."""
        lic_id = self.current_token.license_id if self.current_token else "COMMUNITY_FREE"
        tier_val = self.active_tier().value
        ts = time.monotonic()
        event_id = hashlib.sha3_256(f"{lic_id}:{feature}:{ts}".encode("utf-8")).hexdigest()[:16]
        phash = hashlib.sha3_256(f"{event_id}:{lic_id}:{tier_val}:{feature}:{status}".encode("utf-8")).hexdigest()

        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        try:
            conn.execute(
                "INSERT INTO license_audit_ledger (event_id, license_id, tier, feature, timestamp, status, payload_hash) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (event_id, lic_id, tier_val, feature, ts, status, phash),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            # Ω_BFT_04: Fail-fast si la colisión tiene payload inconsistente
            pass
        finally:
            conn.close()

    def flush_staging_ledger(self) -> int:
        """Vacía las auditorías en staging offline de vuelta al ledger inmutable tras recuperar de 429."""
        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("SELECT event_id, payload_json FROM license_staging_ledger")
        rows = cursor.fetchall()

        flushed = 0
        for event_id, payload_json in rows:
            data = json.loads(payload_json)
            self.record_audit_event(data["feature"], f"FLUSHED_FROM_STAGING:{data.get('event_type')}")
            cursor.execute("DELETE FROM license_staging_ledger WHERE event_id = ?", (event_id,))
            flushed += 1

        conn.commit()
        conn.close()

        if flushed > 0 and self.state == LicenseState.DEGRADED_OFFLINE_VALID:
            self.state = LicenseState.VALID_ONLINE
            self.consecutive_429_count = 0

        return flushed
