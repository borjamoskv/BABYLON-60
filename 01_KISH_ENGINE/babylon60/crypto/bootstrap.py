# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized
"""
CORTEX-PERSIST Bootstrap Module.
Generates Ed25519 identity and auto-signs the GENESIS block.
"""

import logging

import aiosqlite
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

logger = logging.getLogger("babylon60.crypto.bootstrap")


class IdentityBootstrap:
    """Handles autonomous generation of Swarm Identity and Genesis Block."""

    @staticmethod
    def generate_identity() -> tuple[ed25519.Ed25519PrivateKey, str, str]:
        """Generate Ed25519 keypair."""
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        priv_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        pub_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        return private_key, priv_bytes, pub_bytes

    @staticmethod
    async def bootstrap_genesis(conn: aiosqlite.Connection, tenant_id: str = "cortex-swarm-0") -> None:
        """Inject the GENESIS block if cortex_ledger is empty."""
        # Assume cortex_ledger is already created by migration
        async with conn.execute("SELECT COUNT(*) FROM cortex_ledger") as cursor:
            row = await cursor.fetchone()
            count = int(row[0]) if row else 0

        if count > 0:
            return  # Already bootstrapped

        logger.info("Causal-Determinist: Bootstrapping CORTEX-PERSIST Genesis block...")
        private_key, priv_pem, pub_pem = IdentityBootstrap.generate_identity()

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS cortex_identity (
                tenant_id TEXT PRIMARY KEY,
                public_key_pem TEXT NOT NULL,
                private_key_enc TEXT
            )
        """)
        await conn.execute(
            "INSERT INTO cortex_identity (tenant_id, public_key_pem, private_key_enc) VALUES (?, ?, ?)",
            (tenant_id, pub_pem, priv_pem),
        )

        import json
        import time

        from babylon60.crypto.hash_registry import cortex_hash

        timestamp = str(time.time())

        payload_dict = {"type": "GENESIS", "tenant_id": tenant_id, "timestamp": timestamp}
        payload = json.dumps(payload_dict, sort_keys=True, separators=(",", ":")).encode("utf-8")
        payload_hash = cortex_hash(payload)
        signature = private_key.sign(payload).hex()

        await conn.execute(
            """INSERT INTO cortex_ledger
               (lamport_t, agent_id, event_id, event_type, timestamp, prev_hash, payload_hash, signature, payload)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                0,
                tenant_id,
                "EVT_GENESIS",
                "GENESIS",
                timestamp,
                "0000000000000000000000000000000000000000000000000000000000000000",
                payload_hash,
                signature,
                json.dumps(payload_dict),
            ),
        )
        await conn.commit()
        logger.info("Causal-Determinist: Genesis block successfully injected.")
