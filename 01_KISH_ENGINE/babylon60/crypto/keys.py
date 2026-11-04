# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized
"""
Substrate for CORTEX Agent Cryptographic Identity & Enterprise Key Management.

Exposes Ed25519 primitives for subagents to generate robust execution proofs
(Zero-Knowledge signatures) over their stochastically derived states before
submitting them to the Sovereign Ledger.
"""

import base64
from collections.abc import Iterator
from contextlib import contextmanager
import hashlib
import json
import logging
import os
import stat
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import NamedTuple, Protocol, TypedDict, cast

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

# from babylon60.crypto.vault import Vault  # purgado por anergía

logger = logging.getLogger("babylon60.crypto.keys")


class KeyringBackend(Protocol):
    def set_password(self, servicename: str, username: str, password: str) -> None: ...
    def get_password(self, servicename: str, username: str) -> str | None: ...
    def delete_password(self, servicename: str, username: str) -> None: ...


keyring: KeyringBackend | None = None
if not os.environ.get("CORTEX_TESTING"):
    try:
        import keyring as _keyring_module

        keyring = _keyring_module
    except ImportError:
        keyring = None


class KeyMetadataRecord(TypedDict, total=False):
    public_key_b64: str
    expires_at: str | None
    revoked: bool


class AgentKeyPair(NamedTuple):
    """The local identity of an autonomous agent."""

    public_key_b64: str
    private_key_b64: str
    expires_at: str | None = None


class KeyManager:
    """
    Enterprise Key Management (H1.2).
    Manages Ed25519 keys with rotation, revocation, and expiration support.
    """

    _fallback_keyring: dict[str, dict[str, str]] = {}  # service_name -> {actor_id: private_pem}

    def __init__(self, service_name: str = "cortex_persist_enterprise") -> None:
        self.service_name = service_name
        base_dir = Path(os.environ.get("CORTEX_DB_PATH", "~/.babylon60")).expanduser()
        if base_dir.suffix:
            base_dir = base_dir.parent
        self.db_path = base_dir / "keys" / f"{self.service_name}_metadata.json"
        self._metadata: dict[str, KeyMetadataRecord] = {}
        with self._metadata_transaction():
            pass

    @contextmanager
    def _metadata_transaction(self) -> Iterator[int]:
        """Serialize cooperating local instances, then reload the current metadata."""
        if os.name != "posix":
            raise NotImplementedError("Key metadata locking requires a local POSIX filesystem")
        import fcntl

        self.db_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        directory = os.open(self.db_path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        lock_fd = -1
        try:
            lock_fd = os.open(
                self.db_path.name + ".lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                0o600, dir_fd=directory,
            )
            if not stat.S_ISREG(os.fstat(lock_fd).st_mode):
                raise ValueError("Key metadata lock must be a regular file")
            os.fchmod(lock_fd, 0o600)
            fcntl.flock(lock_fd, fcntl.LOCK_EX)
            self._metadata = self._load_metadata(directory)
            yield directory
        finally:
            if lock_fd >= 0:
                os.close(lock_fd)
            os.close(directory)

    def _load_metadata(self, directory: int) -> dict[str, KeyMetadataRecord]:
        try:
            fd = os.open(self.db_path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        except FileNotFoundError:
            return {}
        with os.fdopen(fd, encoding="utf-8") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ValueError("Key metadata must be a regular file")
            data = json.load(stream)
        if not isinstance(data, dict):
            raise ValueError("Key metadata must be an object")
        for actor_id, record in data.items():
            if not isinstance(actor_id, str) or not isinstance(record, dict):
                raise ValueError("Invalid key metadata record")
            if "revoked" in record and not isinstance(record["revoked"], bool):
                raise ValueError("Invalid key revocation flag")
            if "public_key_b64" in record and not isinstance(record["public_key_b64"], str):
                raise ValueError("Invalid public key metadata")
            if record.get("expires_at") is not None and not isinstance(record["expires_at"], str):
                raise ValueError("Invalid key expiry metadata")
        return cast(dict[str, KeyMetadataRecord], data)

    def _save_metadata(self, directory: int) -> None:
        """Publish a complete synced metadata inode while holding the store lock."""
        temporary = f".key-metadata-{uuid.uuid4().hex}.tmp"
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                os.fchmod(stream.fileno(), 0o600)
                json.dump(self._metadata, stream, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.db_path.name, src_dir_fd=directory, dst_dir_fd=directory)
            os.fsync(directory)
        finally:
            try:
                os.unlink(temporary, dir_fd=directory)
            except FileNotFoundError:
                pass

    def generate_and_store_key(self, actor_id: str, expiration_days: int = 90) -> str:
        """Generates a new keypair, stores private key in keyring, and returns the public key."""
        with self._metadata_transaction() as directory:
            return self._generate_and_store_key(actor_id, expiration_days, directory)

    def _generate_and_store_key(self, actor_id: str, expiration_days: int, directory: int) -> str:
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH,
        )

        try:
            if keyring is not None:
                keyring.set_password(self.service_name, actor_id, private_bytes.decode("utf-8"))
            else:
                raise ImportError("keyring package is not installed")
        except Exception as e:  # noqa: BLE001
            logger.warning("Keyring set_password failed, falling back to in-memory storage: %s", e)
            if self.service_name not in self._fallback_keyring:
                self._fallback_keyring[self.service_name] = {}
            self._fallback_keyring[self.service_name][actor_id] = private_bytes.decode("utf-8")

        expires_at = (datetime.now(timezone.utc) + timedelta(days=expiration_days)).isoformat()
        public_key_b64 = base64.b64encode(public_bytes).decode("ascii")

        self._metadata[actor_id] = {
            "public_key_b64": public_key_b64,
            "expires_at": expires_at,
            "revoked": False,
        }
        self._save_metadata(directory)
        logger.info("Generated Ed25519 key for actor: ***id")
        return public_key_b64

    def get_private_key_b64(self, actor_id: str) -> str | None:
        with self._metadata_transaction():
            return self._get_private_key_b64(actor_id)

    def _get_private_key_b64(self, actor_id: str) -> str | None:
        if actor_id not in self._metadata or self._metadata[actor_id].get("revoked", False) or self._is_expired(actor_id):
            logger.warning("Key for actor ***id")
            return None

        private_pem = self._fallback_keyring.get(self.service_name, {}).get(actor_id)

        if not private_pem:
            try:
                if keyring is not None:
                    private_pem = keyring.get_password(self.service_name, actor_id)
                else:
                    logger.warning("OS Keyring is not available (keyring package is not installed).")
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    "Fallo en OS Keyring (get_password) para actor %s: %s",
                    actor_id,
                    e,
                    exc_info=True,
                )

        if not private_pem:
            return None

        private_key = serialization.load_pem_private_key(private_pem.encode("utf-8"), password=None)
        if not isinstance(private_key, ed25519.Ed25519PrivateKey):
            raise ValueError("Key is not an Ed25519PrivateKey")
        current_public = base64.b64encode(private_key.public_key().public_bytes(
            encoding=serialization.Encoding.OpenSSH, format=serialization.PublicFormat.OpenSSH,
        )).decode("ascii")
        if current_public != self._metadata[actor_id].get("public_key_b64"):
            # Keyring and filesystem are distinct stores: a failed metadata write
            # must not make a replacement private key usable under old metadata.
            return None

        return base64.b64encode(
            private_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption(),
            )
        ).decode("ascii")

    def revoke_key(self, actor_id: str) -> bool:
        """Revokes the key to prevent future signing/verification."""
        with self._metadata_transaction() as directory:
            return self._revoke_key(actor_id, directory)

    def _revoke_key(self, actor_id: str, directory: int) -> bool:
        if actor_id in self._metadata:
            self._metadata[actor_id]["revoked"] = True
            self._save_metadata(directory)
            try:
                if keyring is not None:
                    keyring.delete_password(self.service_name, actor_id)
                else:
                    logger.warning("OS Keyring is not available (keyring package is not installed).")
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    "Fallo en OS Keyring (delete_password) para actor %s: %s",
                    actor_id,
                    e,
                    exc_info=True,
                )
            if self.service_name in self._fallback_keyring:
                self._fallback_keyring[self.service_name].pop(actor_id, None)
            logger.info("Revoked key for actor: ***id")
            return True
        return False

    def get_public_key_b64(self, actor_id: str) -> str | None:
        """Retrieves the public key for the actor."""
        with self._metadata_transaction():
            return self._metadata.get(actor_id, {}).get("public_key_b64")

    def is_revoked(self, actor_id: str) -> bool:
        with self._metadata_transaction():
            return bool(self._metadata.get(actor_id, {}).get("revoked", False))

    def is_expired(self, actor_id: str) -> bool:
        with self._metadata_transaction():
            return self._is_expired(actor_id)

    def _is_expired(self, actor_id: str) -> bool:
        expires_at_str = self._metadata.get(actor_id, {}).get("expires_at")
        if not expires_at_str:
            return False
        expires_at = datetime.fromisoformat(expires_at_str)
        return datetime.now(timezone.utc) > expires_at

    def rotate_key(self, actor_id: str) -> str:
        """Revokes the old key and generates a new one."""
        with self._metadata_transaction() as directory:
            self._revoke_key(actor_id, directory)
            return self._generate_and_store_key(actor_id, 90, directory)


class Signer:
    """Enterprise Signer (H1.1). Handles Ed25519 cryptographic signing."""

    @staticmethod
    def sign_payload(private_key_b64: str, payload_hash: str, timestamp: str) -> str:
        """
        Signs the deterministically combined hash and timestamp.
        Returns the signature as a base64 string.
        """
        priv_bytes = base64.b64decode(private_key_b64)
        try:
            priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)
        except ValueError:
            loaded_key = serialization.load_pem_private_key(priv_bytes, password=None)
            if not isinstance(loaded_key, ed25519.Ed25519PrivateKey):
                raise ValueError("Key must be an Ed25519PrivateKey")
            priv_key = loaded_key

        message = f"{payload_hash}:{timestamp}".encode()
        sig_bytes = priv_key.sign(message)
        return base64.b64encode(sig_bytes).decode("ascii")

    @staticmethod
    def sign_raw_content(private_key_b64: str, content: str) -> str:
        """Legacy compatibility for direct raw content signing."""
        priv_bytes = base64.b64decode(private_key_b64)
        try:
            priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)
        except ValueError:
            loaded_key = serialization.load_pem_private_key(priv_bytes, password=None)
            if not isinstance(loaded_key, ed25519.Ed25519PrivateKey):
                raise ValueError("Key must be an Ed25519PrivateKey")
            priv_key = loaded_key
        content_hash = hashlib.sha256(content.encode("utf-8")).digest()
        sig_bytes = priv_key.sign(content_hash)
        return base64.b64encode(sig_bytes).decode("utf-8")


class Verifier:
    """Enterprise Verifier (H1.1). Handles Ed25519 cryptographic verification."""

    @staticmethod
    def verify_signature(public_key_b64: str, payload_hash: str, timestamp: str, signature_b64: str) -> bool:
        try:
            pub_bytes = base64.b64decode(public_key_b64)
            try:
                public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
            except ValueError:
                loaded_key = serialization.load_ssh_public_key(pub_bytes)
                if not isinstance(loaded_key, ed25519.Ed25519PublicKey):
                    return False
                public_key = loaded_key

            signature = base64.b64decode(signature_b64)
            if len(signature) != 64:
                logger.error("Invalid signature length: %s bytes (expected 64)", len(signature))
                return False

            raw_pub_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
            if len(raw_pub_bytes) != 32:
                logger.error("Invalid public key length: %s bytes (expected 32)", len(raw_pub_bytes))
                return False

            message = f"{payload_hash}:{timestamp}".encode()
            public_key.verify(signature, message)
            return True
        except (InvalidSignature, ValueError, TypeError) as e:
            logger.error("Verification failed: %s", e)
            return False

    @staticmethod
    def verify_raw_content(content: str, public_key_b64: str, signature_b64: str) -> bool:
        """Legacy compatibility."""
        try:
            pub_bytes = base64.b64decode(public_key_b64)
            try:
                public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
            except ValueError:
                loaded_key = serialization.load_ssh_public_key(pub_bytes)
                if not isinstance(loaded_key, ed25519.Ed25519PublicKey):
                    return False
                public_key = loaded_key

            signature = base64.b64decode(signature_b64)
            if len(signature) != 64:
                return False

            raw_pub_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
            if len(raw_pub_bytes) != 32:
                return False

            content_hash = hashlib.sha256(content.encode("utf-8")).digest()
            public_key.verify(signature, content_hash)
            return True
        except (InvalidSignature, ValueError, TypeError):
            return False


class Secp256k1Signer:
    """Enterprise Signer compatibility for SECP256K1 using native C/Rust bindings."""

    @staticmethod
    def sign_raw_content(private_key_b64: str, content: str) -> str:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec

        priv_bytes = base64.b64decode(private_key_b64)

        try:
            priv_key = serialization.load_pem_private_key(priv_bytes, password=None)
            if not isinstance(priv_key, ec.EllipticCurvePrivateKey):
                raise ValueError("Key must be an EllipticCurvePrivateKey")
        except ValueError:
            # Fallback for raw bytes
            priv_value = int.from_bytes(priv_bytes, "big")
            priv_key = ec.derive_private_key(priv_value, ec.SECP256K1())

        content_hash = hashlib.sha256(content.encode("utf-8")).digest()
        sig_bytes = priv_key.sign(content_hash, ec.ECDSA(hashes.SHA256()))
        return base64.b64encode(sig_bytes).decode("utf-8")


class Secp256k1Verifier:
    """Enterprise Verifier compatibility for SECP256K1 using native C/Rust bindings."""

    @staticmethod
    def verify_raw_content(content: str, public_key_b64: str, signature_b64: str) -> bool:
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import ec

        try:
            pub_bytes = base64.b64decode(public_key_b64)
            try:
                public_key = serialization.load_pem_public_key(pub_bytes)
            except ValueError:
                try:
                    public_key = serialization.load_ssh_public_key(pub_bytes)
                except ValueError:
                    # Raw representation: uncompressed points 0x04 + x + y
                    public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), pub_bytes)

            if not isinstance(public_key, ec.EllipticCurvePublicKey):
                return False

            signature = base64.b64decode(signature_b64)
            content_hash = hashlib.sha256(content.encode("utf-8")).digest()

            public_key.verify(signature, content_hash, ec.ECDSA(hashes.SHA256()))
            return True
        except (InvalidSignature, ValueError, TypeError) as e:
            logger.error("SECP256K1 Verification failed: %s", e)
            return False


class ZKSwarmIdentity:
    """Legacy compatibility for ZK-Swarm Identity."""

    @staticmethod
    def generate_keypair() -> AgentKeyPair:
        km = KeyManager("zk_swarm_temp")
        actor_id = "temp_" + os.urandom(4).hex()
        pub = km.generate_and_store_key(actor_id)
        priv = km.get_private_key_b64(actor_id)
        if priv is None:
            raise RuntimeError(f"Failed to retrieve generated key for {actor_id}")
        return AgentKeyPair(public_key_b64=pub, private_key_b64=priv or "")

    @staticmethod
    def sign_payload(content: str, private_key_b64: str) -> str:
        return Signer.sign_raw_content(private_key_b64, content)

    @staticmethod
    def verify_payload(content: str, public_key_b64: str, signature_b64: str) -> bool:
        return Verifier.verify_raw_content(content, public_key_b64, signature_b64)


class KeyLifecycleManager:
    """Legacy Compatibility."""

    def __init__(self, storage_path: str | Path | None = None, vault: object = None) -> None:
        self.km = KeyManager()

    def get_or_create_identity(self) -> AgentKeyPair:
        return ZKSwarmIdentity.generate_keypair()

    def rotate_keys(self) -> AgentKeyPair:
        return ZKSwarmIdentity.generate_keypair()
