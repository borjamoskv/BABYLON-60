"""
REAPER — Notarizer

SHA256 hashing + timestamp for proof-of-prior-art.
Records every submission in the SQLite ledger.
"""
import hashlib
from datetime import datetime, timezone
from pathlib import Path


class Notarizer:
    """Generates cryptographic proof of submission timing."""

    def notarize_file(self, filepath: str) -> dict:
        """Generate SHA256 hash and timestamp for a file."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Not found: {filepath}")

        content = path.read_bytes()
        file_hash = hashlib.sha256(content).hexdigest()
        timestamp = datetime.now(timezone.utc).isoformat()

        # Write .sig sidecar file
        sig_path = path.with_suffix(path.suffix + ".sig")
        sig_content = (
            f"CORTEX-BOUNTY NOTARIZATION\n"
            f"File: {path.name}\n"
            f"SHA256: {file_hash}\n"
            f"Timestamp: {timestamp}\n"
            f"Size: {len(content)} bytes\n"
        )
        sig_path.write_text(sig_content, encoding="utf-8")

        return {
            "file": str(path),
            "sha256": file_hash,
            "timestamp": timestamp,
            "size": len(content),
            "sig_file": str(sig_path),
        }

    def notarize_content(self, content: str) -> dict:
        """Generate hash for arbitrary content."""
        content_bytes = content.encode("utf-8")
        return {
            "sha256": hashlib.sha256(content_bytes).hexdigest(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "size": len(content_bytes),
        }

    def verify(self, filepath: str, expected_hash: str) -> bool:
        """Verify file integrity against expected hash."""
        path = Path(filepath)
        if not path.exists():
            return False
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        return actual == expected_hash
