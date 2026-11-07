"""Isolated C28 cache filesystem and integrity regressions."""

import json
import os

import pytest

from babylon60.transducers.render_exergy_guard import RenderCacheStore, RenderExergyReceipt

HASH = "a" * 64


def receipt():
    return RenderExergyReceipt(HASH, "final", False, True, "", 0.0, None, None, None, None, {})


def populated(tmp_path):
    cache = RenderCacheStore(tmp_path / "cache")
    source = tmp_path / "source.mp4"
    source.write_bytes(b"verified render")
    cache.store(HASH, source, receipt())
    return cache


def test_round_trip_and_unknown_metrics(tmp_path):
    cache = populated(tmp_path)
    dest = tmp_path / "out.mp4"
    result = cache.lookup(HASH, dest)
    assert result is not None and result.verified
    assert result.estimated_joules is None and result.exergy_phi is None
    assert dest.read_bytes() == b"verified render"
    assert (cache.cache_dir.stat().st_mode & 0o777) == 0o700


def test_rejects_precreated_public_cache(tmp_path):
    directory = tmp_path / "cache"
    directory.mkdir(mode=0o755)
    with pytest.raises(PermissionError):
        RenderCacheStore(directory)


def test_rejects_symlink_root(tmp_path):
    target = tmp_path / "target"
    target.mkdir(mode=0o700)
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(OSError):
        RenderCacheStore(link)


@pytest.mark.parametrize("name", ["../outside", "/absolute", "b" * 63, "A" * 64])
def test_invalid_manifest_rejected(tmp_path, name):
    cache = RenderCacheStore(tmp_path / "cache")
    with pytest.raises(ValueError):
        cache.lookup(name, tmp_path / "output")


def test_modified_artifact_is_miss(tmp_path):
    cache = populated(tmp_path)
    cache._artifact_path(HASH).write_bytes(b"tampered")
    output = tmp_path / "out"
    assert cache.lookup(HASH, output) is None
    assert not output.exists()


def test_legacy_forged_receipt_is_miss(tmp_path):
    cache = populated(tmp_path)
    cache._receipt_path(HASH).write_text(json.dumps({"verified": True}))
    assert cache.lookup(HASH, tmp_path / "out") is None


def test_symlink_entry_is_miss_and_store_does_not_follow(tmp_path):
    cache = populated(tmp_path)
    outside = tmp_path / "outside"
    outside.write_bytes(b"preserve")
    artifact = cache._artifact_path(HASH)
    artifact.unlink()
    artifact.symlink_to(outside)
    assert cache.lookup(HASH, tmp_path / "out") is None
    cache.store(HASH, tmp_path / "source.mp4", receipt())
    assert outside.read_bytes() == b"preserve"
    assert not artifact.is_symlink()


def test_destination_symlink_is_replaced_not_followed(tmp_path):
    cache = populated(tmp_path)
    outside = tmp_path / "outside"
    outside.write_bytes(b"preserve")
    destination = tmp_path / "out"
    destination.symlink_to(outside)
    assert cache.lookup(HASH, destination) is not None
    assert outside.read_bytes() == b"preserve"
    assert not destination.is_symlink()


def test_replaced_cache_directory_rejected(tmp_path):
    cache = populated(tmp_path)
    cache.cache_dir.rename(tmp_path / "old")
    cache.cache_dir.mkdir(mode=0o700)
    assert cache.lookup(HASH, tmp_path / "out") is None


def test_fifo_entry_does_not_block(tmp_path):
    cache = populated(tmp_path)
    artifact = cache._artifact_path(HASH)
    artifact.unlink()
    os.mkfifo(artifact, 0o600)
    assert cache.lookup(HASH, tmp_path / "out") is None


def test_symlink_ancestor_rejected(tmp_path):
    actual = tmp_path / "actual"
    actual.mkdir(mode=0o700)
    linked = tmp_path / "linked"
    linked.symlink_to(actual, target_is_directory=True)
    with pytest.raises(OSError):
        RenderCacheStore(linked / "cache")
    assert not (actual / "cache").exists()


def test_destination_parent_symlink_rejected(tmp_path):
    cache = populated(tmp_path)
    actual = tmp_path / "actual"
    actual.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(actual, target_is_directory=True)
    assert cache.lookup(HASH, linked / "out") is None
    assert not (actual / "out").exists()


def test_bad_digest_preserves_existing_destination(tmp_path):
    cache = populated(tmp_path)
    cache._artifact_path(HASH).write_bytes(b"tampered")
    output = tmp_path / "out"
    output.write_bytes(b"preserve")
    assert cache.lookup(HASH, output) is None
    assert output.read_bytes() == b"preserve"
    assert not list(tmp_path.glob(".render-*"))
