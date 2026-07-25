import logging
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

logger = logging.getLogger('babylon60.crypto.bootstrap')

class IdentityBootstrap:

    @staticmethod
    def generate_identity() -> tuple[ed25519.Ed25519PrivateKey, str, str]:
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        priv_bytes = private_key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption()).decode('utf-8')
        pub_bytes = public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo).decode('utf-8')
        return (private_key, priv_bytes, pub_bytes)

    @staticmethod
    async def bootstrap_genesis(conn: Any, tenant_id: str='cortex-swarm-0') -> None:
        async with conn.execute('SELECT COUNT(*) FROM cortex_ledger') as cursor:
            count = (await cursor.fetchone())[0]
        if count > 0:
            return
        logger.info('C5-REAL: Bootstrapping CORTEX-PERSIST Genesis block...')
        private_key, priv_pem, pub_pem = IdentityBootstrap.generate_identity()
        await conn.execute('\n            CREATE TABLE IF NOT EXISTS cortex_identity (\n                tenant_id TEXT PRIMARY KEY,\n                public_key_pem TEXT NOT NULL,\n                private_key_enc TEXT\n            )\n        ')
        await conn.execute('INSERT INTO cortex_identity (tenant_id, public_key_pem, private_key_enc) VALUES (?, ?, ?)', (tenant_id, pub_pem, priv_pem))
        import time

        from babylon60.crypto.hash_registry import cortex_hash
        from babylon60.crypto.serialization import canonical_serialize
        timestamp = str(int(time.time()))
        payload_dict = {'type': 'GENESIS', 'tenant_id': tenant_id, 'timestamp': timestamp}
        payload = canonical_serialize(payload_dict)
        payload_hash = cortex_hash(payload)
        signature = private_key.sign(payload).hex()
        import json
        await conn.execute('INSERT INTO cortex_ledger\n               (lamport_t, agent_id, event_id, event_type, timestamp, prev_hash, payload_hash, signature, payload)\n               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (0, tenant_id, 'EVT_GENESIS', 'GENESIS', timestamp, '0000000000000000000000000000000000000000000000000000000000000000', payload_hash, signature, json.dumps(payload_dict)))
        await conn.commit()
        logger.info('C5-REAL: Genesis block successfully injected.')