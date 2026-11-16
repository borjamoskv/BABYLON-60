"""C0565 regression: the container compiler must satisfy the manifests' rust-version."""

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = ROOT / "deploy" / "Dockerfile"


def _version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


def _required_rust_version() -> tuple[int, ...]:
    manifest = tomllib.loads((ROOT / "Cargo.toml").read_text(encoding="utf-8"))
    return _version(manifest["package"]["rust-version"])


def test_builder_image_satisfies_workspace_rust_version():
    images = re.findall(r"^FROM\s+rust:(\d+(?:\.\d+)+)", DOCKERFILE.read_text(encoding="utf-8"), re.M)
    assert images, "deploy/Dockerfile no declara una imagen rust:<versión> fijada"
    required = _required_rust_version()
    for image in images:
        assert _version(image) >= required, f"rust:{image} no satisface rust-version {required}"


def test_container_build_uses_locked_dependencies():
    builds = [line for line in DOCKERFILE.read_text(encoding="utf-8").splitlines() if "cargo build" in line]
    assert builds, "deploy/Dockerfile no ejecuta cargo build"
    assert all("--locked" in line for line in builds), "cargo build sin --locked en el contenedor"
