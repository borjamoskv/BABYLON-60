#!/usr/bin/env bash
# Run in a disposable Linux ARM64 guest/container with no production credentials.
set -euo pipefail

if [[ "$(uname -s)" != Linux || "$(uname -m)" != aarch64 ]]; then
  echo "This gate requires a running Linux aarch64 system; cross-compilation is insufficient." >&2
  exit 2
fi
for tool in cargo uv python3 protoc lsof elan lake gitleaks node; do
  command -v "$tool" >/dev/null || { echo "Required validation tool missing: $tool" >&2; exit 2; }
done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"
cd "$repo_root"
ELAN_TOOLCHAIN="$(<proof/lean/lean-toolchain)"
export ELAN_TOOLCHAIN
output_dir="${1:?Usage: validate_linux_arm64.sh /absolute/evidence-directory}"
if [[ "$output_dir" != /* ]]; then
  echo "Use an absolute evidence directory outside the source tree." >&2
  exit 2
fi
case "$output_dir/" in "$repo_root/"*) echo "Evidence must remain outside the source tree." >&2; exit 2 ;; esac
mkdir -p "$output_dir"
scratch_dir="$(mktemp -d "$output_dir/linux-arm64-validation.XXXXXX")"
trap 'rm -rf -- "$scratch_dir"' EXIT
mkdir "$scratch_dir/tmp" "$scratch_dir/python"
export TMPDIR="$scratch_dir/tmp"
export CARGO_BUILD_JOBS="${CARGO_BUILD_JOBS:-2}"
export CARGO_INCREMENTAL=0 CARGO_PROFILE_DEV_DEBUG=0 CARGO_PROFILE_TEST_DEBUG=0

# Several integration fixtures execute temporary helpers. Do not weaken a host
# mount: require the disposable build filesystem to permit their execution.
printf '#!/bin/sh\nexit 0\n' > "$scratch_dir/exec-check"
chmod 700 "$scratch_dir/exec-check"
"$scratch_dir/exec-check"
{
  uname -a
  rustc --version
  uv --version
  python3 --version
  protoc --version
  elan --version
  elan run "$ELAN_TOOLCHAIN" lean --version
  gitleaks version
  node --version
  git rev-parse HEAD
  sha256sum Cargo.lock uv.lock
} > "$output_dir/environment.txt"

uv sync --locked --extra dev --extra gemini > "$output_dir/uv-sync.log" 2>&1
uv lock --check > "$output_dir/uv-lock-check.log" 2>&1
(cd proof/lean && lake build) > "$output_dir/lean-build.log" 2>&1
cargo check --workspace --locked > "$output_dir/cargo-check.log" 2>&1
uv run --locked --no-sync cargo test --workspace --locked -- --test-threads=1 > "$output_dir/cargo-test.log" 2>&1
cargo build --locked -p babylon60_root -p babylon-attest --lib --bins > "$output_dir/native-build.log" 2>&1
uv run --locked --no-sync cargo build --locked -p strike_rs --features extension-module >> "$output_dir/native-build.log" 2>&1
extension_suffix="$(uv run --locked --no-sync python -c 'import sysconfig; print(sysconfig.get_config_var("EXT_SUFFIX"))')"
cp target/debug/libstrike_rs.so "$scratch_dir/python/strike_rs$extension_suffix"
export PYTHONPATH="$scratch_dir/python${PYTHONPATH:+:$PYTHONPATH}"
export BABYLON60_DYLIB_PATH="$repo_root/target/debug/libbabylon60.so"
export BABYLON60_REQUIRE_NATIVE=1
export BABYLON60_REQUIRE_LEAN_ENVELOPES=1
export BABYLON_TEST_INSTALL_BUNDLE=1
export BABYLON_TEST_AUTHORITY_BIN="$repo_root/target/debug/babylon_authorityd"
uv run --locked --no-sync pytest -q -o addopts='' --tb=short -rs \
  --junitxml="$output_dir/pytest.xml" > "$output_dir/pytest.log" 2>&1
printf 'Linux ARM64 validation passed; evidence: %s\n' "$output_dir"
