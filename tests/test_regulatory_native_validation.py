"""Verify a historical native challenge offline; never invoke biometrics."""

import pytest

from scripts.guards.validate_regulatory_hardware import protected_hash, save


def test_attempt_marker_cannot_be_replaced(tmp_path):
    marker = tmp_path / "policy.validation-attempt.json"
    original = save(marker, {"attempts": 1})
    with pytest.raises(FileExistsError):
        save(marker, {"attempts": 2})
    assert marker.read_bytes() == original


def test_candidate_must_be_protected_regular_file(tmp_path):
    candidate = tmp_path / "helper"
    candidate.write_bytes(b"not executable: metadata-only negative test")
    candidate.chmod(0o666)
    with pytest.raises(ValueError, match="not writable by others"):
        protected_hash(candidate)
    candidate.chmod(0o600)
    link = tmp_path / "link"
    link.symlink_to(candidate)
    with pytest.raises(ValueError, match="without symlinks"):
        protected_hash(link)
