import base64
import hashlib
import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import NamedTuple
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
from babylon60.utils.base60 import bytes_to_base60
logger = logging.getLogger('babylon60.crypto.identity')
ARGON2_MEMORY_COST = 65536
ARGON2_TIME_COST = 3
ARGON2_PARALLELISM = 4
ARGON2_HASH_LEN = 32
_NONCE_LENGTH = 12

class IdentityPayload(NamedTuple):
    public_key_b64: str
    private_key_b64: str
    seed_bytes: bytes

class L0IdentityForge:

    def __init__(self, storage_dir: str | Path | None=None) -> None:
        if storage_dir is None:
            base = Path(os.environ.get('CORTEX_DB_PATH', '~/.babylon60')).expanduser()
            if base.suffix:
                base = base.parent
            self.storage_dir = base / 'identity'
        else:
            self.storage_dir = Path(storage_dir).expanduser()
        self.seed_path = self.storage_dir / 'master_seed.enc'

    def _derive_kek(self, passphrase: str, salt: bytes) -> bytes:
        kdf = Argon2id(salt=salt, length=ARGON2_HASH_LEN, iterations=ARGON2_TIME_COST, lanes=ARGON2_PARALLELISM, memory_cost=ARGON2_MEMORY_COST)
        return kdf.derive(passphrase.encode('utf-8'))

    def forge_identity(self, passphrase: str) -> IdentityPayload:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        seed = os.urandom(32)
        salt = os.urandom(16)
        kek = self._derive_kek(passphrase, salt)
        aesgcm = AESGCM(kek)
        nonce = os.urandom(_NONCE_LENGTH)
        ciphertext = aesgcm.encrypt(nonce, seed, None)
        payload = {'salt_b64': base64.b64encode(salt).decode('ascii'), 'nonce_b64': base64.b64encode(nonce).decode('ascii'), 'ciphertext_b64': base64.b64encode(ciphertext).decode('ascii')}
        self.seed_path.touch(mode=384, exist_ok=True)
        with open(self.seed_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f)
        self.seed_path.chmod(384)
        logger.info('L0 Identity Forged and encrypted via Argon2id.')
        return self._generate_keypair_from_seed(seed)

    def load_identity(self, passphrase: str) -> IdentityPayload:
        if not self.seed_path.exists():
            raise FileNotFoundError('Master seed not found. Cannot load identity.')
        with open(self.seed_path, encoding='utf-8') as f:
            payload = json.load(f)
        salt = base64.b64decode(payload['salt_b64'])
        nonce = base64.b64decode(payload['nonce_b64'])
        ciphertext = base64.b64decode(payload['ciphertext_b64'])
        kek = self._derive_kek(passphrase, salt)
        aesgcm = AESGCM(kek)
        try:
            seed = aesgcm.decrypt(nonce, ciphertext, None)
            return self._generate_keypair_from_seed(seed)
        except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError) as e:
            logger.error('Failed to decrypt master seed. Incorrect passphrase or corrupted file.')
            raise ValueError('Identity Decryption Failed') from e

    def _generate_keypair_from_seed(self, seed: bytes) -> IdentityPayload:
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
        public_key = private_key.public_key()
        priv_bytes = private_key.private_bytes(encoding=serialization.Encoding.Raw, format=serialization.PrivateFormat.Raw, encryption_algorithm=serialization.NoEncryption())
        pub_bytes = public_key.public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
        return IdentityPayload(public_key_b64=base64.b64encode(pub_bytes).decode('ascii'), private_key_b64=base64.b64encode(priv_bytes).decode('ascii'), seed_bytes=seed)

class StateRootAccumulator:

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_latest_root(self) -> tuple[int, bytes]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT lamport, root FROM state_root ORDER BY lamport DESC LIMIT 1')
        row = cursor.fetchone()
        if row:
            return (row[0], row[1])
        return (0, b'')

    def append_event(self, lamport_tick: int, event_hash: bytes, private_key_b64: str) -> bytes:
        latest_lamport, prev_root = self.get_latest_root()
        if lamport_tick <= latest_lamport:
            raise ValueError('Lamport tick must be strictly monotonically increasing.')
        hasher = hashlib.sha256()
        hasher.update(prev_root)
        hasher.update(event_hash)
        hasher.update(str(lamport_tick).encode('utf-8'))
        new_root = hasher.digest()
        priv_bytes = base64.b64decode(private_key_b64)
        priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)
        signature = priv_key.sign(new_root)
        self.conn.execute('\n            INSERT INTO state_root (lamport, event_hash, root, signature)\n            VALUES (?, ?, ?, ?)\n            ', (lamport_tick, event_hash, new_root, signature))
        logger.debug(f'Appended event to state root at tick {lamport_tick}')
        return new_root

    def verify_chain(self, public_key_b64: str) -> bool:
        pub_bytes = base64.b64decode(public_key_b64)
        pub_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
        cursor = self.conn.cursor()
        cursor.execute('SELECT lamport, event_hash, root, signature FROM state_root ORDER BY lamport ASC')
        rows = cursor.fetchall()
        prev_root = b''
        for row in rows:
            lamport, event_hash, root, signature = row
            hasher = hashlib.sha256()
            hasher.update(prev_root)
            hasher.update(event_hash)
            hasher.update(str(lamport).encode('utf-8'))
            expected_root = hasher.digest()
            if root != expected_root:
                logger.error(f'Chain broken at tick {lamport}. Tampering detected!')
                return False
            try:
                pub_key.verify(signature, root)
            except InvalidSignature:
                logger.error(f'Invalid signature at tick {lamport}. Cryptographic forgery detected!')
                return False
            prev_root = root
        return True

class IdentityAnchorManager:

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def is_anchored(self) -> bool:
        cursor = self.conn.cursor()
        cursor.execute('SELECT 1 FROM identity_anchor LIMIT 1')
        return cursor.fetchone() is not None

    def anchor_genesis(self, payload: IdentityPayload) -> str:
        if self.is_anchored():
            raise ValueError('Ledger is already anchored to an identity.')
        pub_bytes = base64.b64decode(payload.public_key_b64)
        priv_bytes = base64.b64decode(payload.private_key_b64)
        node_id = bytes_to_base60(hashlib.sha256(pub_bytes).digest())
        lamport = 0
        priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)
        msg = node_id.encode('utf-8') + pub_bytes + str(lamport).encode('utf-8')
        self_signature = priv_key.sign(msg)
        self.conn.execute('\n            INSERT INTO identity_anchor (node_id, pubkey_ed25519, created_at_lamport, self_signature)\n            VALUES (?, ?, ?, ?)\n            ', (node_id, pub_bytes, lamport, self_signature))
        logger.info(f'Genesis Anchored. Node ID: {node_id}')
        return node_id