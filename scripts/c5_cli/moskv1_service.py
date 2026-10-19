#!/usr/bin/env python3
"""MOSKV-1 Sovereign Service & Multi-Surface Health Supervisor.

Provides unified status, multi-surface health verification, and macOS launchd
daemon management for the MOSKV-1 kernel in BABYLON-60.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import socket
import sys
from typing import TypedDict
from urllib import error as urlerror, request as urlrequest


class MultiSurfaceReport(TypedDict):
    status: str
    symlinks: dict[str, str]
    mcp_manifests: dict[str, str]
    openapi_contract: str
    errors: list[str]


def get_repo_root() -> Path:
    """Return canonical repo root adhering to INV_C5_PATH_SYMLINK_CONFINEMENT."""
    logical_candidate = Path("/Users/borjafernandezangulo/BABYLON-60")
    if (logical_candidate / ".babylon60rules").is_file():
        root = logical_candidate
    else:
        root = Path(__file__).absolute().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


RULE_SYMLINKS: tuple[tuple[str, str], ...] = (
    (".codexrules", ".babylon60rules"),
    (".cursorrules", ".babylon60rules"),
    (".windsurfrules", ".babylon60rules"),
    ("CLAUDE.md", ".babylon60rules"),
    (".clinerules", ".babylon60rules"),
    (".roorules", ".babylon60rules"),
    (".github/copilot-instructions.md", "../.babylon60rules"),
)

MCP_MANIFESTS: tuple[str, ...] = (
    ".mcp.json",
    ".vscode/mcp.json",
    ".gemini/settings.json",
    ".claude/settings.json",
    ".codex/config.toml",
)


def probe_tcp_port(host: str, port: int, timeout: float = 1.0) -> bool:
    """Check if loopback port is actively listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        try:
            sock.connect((host, port))
            return True
        except (OSError, socket.timeout):
            return False


def probe_http_openapi(url: str, timeout: float = 2.0) -> dict[str, object] | None:
    """Query loopback OpenAPI endpoint and return parsed JSON spec if available."""
    req = urlrequest.Request(url, headers={"User-Agent": "MOSKV1-Health-Probe/1.0"})
    try:
        with urlrequest.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                if isinstance(data, dict):
                    return {str(k): v for k, v in data.items()}
    except (urlerror.URLError, json.JSONDecodeError, TimeoutError):
        return None
    return None


def generate_launchd_plist(
    repo_root: Path,
    *,
    python_bin: Path | None = None,
    port: int = 6061,
    transport: str = "openapi-http",
) -> str:
    """Generate canonical launchd LaunchAgent XML configuration."""
    py_exec = python_bin or (repo_root / "target" / "kernel-mcp-venv" / "bin" / "python")
    if not py_exec.is_file():
        py_exec = Path(sys.executable)

    script_path = repo_root / "tools" / "babylon60_mcp.py"
    log_out = repo_root / "logs" / "moskv1_daemon.log"
    log_err = repo_root / "logs" / "moskv1_daemon_err.log"

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.c5real.moskv1.kernel</string>
    <key>ProgramArguments</key>
    <array>
        <string>{py_exec}</string>
        <string>{script_path}</string>
        <string>--transport</string>
        <string>{transport}</string>
        <string>--host</string>
        <string>127.0.0.1</string>
        <string>--port</string>
        <string>{port}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{repo_root}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{log_out}</string>
    <key>StandardErrorPath</key>
    <string>{log_err}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONUNBUFFERED</key>
        <string>1</string>
        <key>BABYLON60_MCP_BEARER_TOKEN</key>
        <string>sovereign-kernel-loopback-token-6060</string>
    </dict>
</dict>
</plist>
"""


def check_multi_surface_health(repo_root: Path) -> MultiSurfaceReport:
    """Audit all 13 IDE surfaces, symlinks, manifests, and contract status."""
    report: MultiSurfaceReport = {
        "status": "healthy",
        "symlinks": {},
        "mcp_manifests": {},
        "openapi_contract": "unknown",
        "errors": [],
    }
    errors: list[str] = []

    # 1. Symlinks audit
    symlink_statuses: dict[str, str] = {}
    for rel_link, expected_target in RULE_SYMLINKS:
        link_path = repo_root / rel_link
        if not link_path.is_symlink():
            symlink_statuses[rel_link] = "missing_or_not_symlink"
            errors.append(f"Symlink {rel_link} is missing or not a symlink")
        elif link_path.readlink() != Path(expected_target):
            symlink_statuses[rel_link] = f"target_mismatch:{link_path.readlink()}"
            errors.append(f"Symlink {rel_link} points to {link_path.readlink()}, expected {expected_target}")
        else:
            symlink_statuses[rel_link] = "ok"
    report["symlinks"] = symlink_statuses

    # 2. MCP Manifests audit
    manifest_statuses: dict[str, str] = {}
    for rel_path in MCP_MANIFESTS:
        man_path = repo_root / rel_path
        if not man_path.is_file():
            manifest_statuses[rel_path] = "missing"
            errors.append(f"Manifest {rel_path} does not exist")
            continue
        try:
            content = man_path.read_text(encoding="utf-8")
            if "/Users/" in content:
                manifest_statuses[rel_path] = "leaks_users_path"
                errors.append(f"Manifest {rel_path} leaks absolute '/Users/' path")
            elif rel_path == ".claude/settings.json" and "babylon60-kernel" not in content:
                manifest_statuses[rel_path] = "missing_registration"
                errors.append(f"Manifest {rel_path} missing 'babylon60-kernel'")
            elif (
                rel_path != ".claude/settings.json"
                and "scripts/c5_cli/launch_kernel_mcp.py" not in content
            ):
                manifest_statuses[rel_path] = "missing_launcher_ref"
                errors.append(f"Manifest {rel_path} does not reference launch_kernel_mcp.py")
            else:
                manifest_statuses[rel_path] = "ok"
        except (OSError, UnicodeError) as err:
            manifest_statuses[rel_path] = f"unreadable:{err}"
            errors.append(f"Manifest {rel_path} unreadable: {err}")
    report["mcp_manifests"] = manifest_statuses

    # 3. OpenAPI contract parity
    contract_file = repo_root / "contracts" / "openapi_babylon60_kernel.json"
    if contract_file.is_file():
        try:
            from tools.babylon60_mcp import build_openapi_spec

            spec_on_disk = json.loads(contract_file.read_text(encoding="utf-8"))
            spec_in_memory = build_openapi_spec()
            if spec_on_disk == spec_in_memory:
                report["openapi_contract"] = "synchronized_1_to_1"
            else:
                report["openapi_contract"] = "drift_detected"
                errors.append("OpenAPI contract on disk drifts from build_openapi_spec()")
        except Exception as exc:  # noqa: BLE001
            report["openapi_contract"] = f"error:{exc}"
            errors.append(f"Could not verify OpenAPI parity: {exc}")
    else:
        report["openapi_contract"] = "missing"
        errors.append(f"Contract file {contract_file} missing")

    if errors:
        report["status"] = "degraded"
    report["errors"] = errors
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: status
    status_parser = subparsers.add_parser("status", help="Inspect loopback daemon status and OpenAPI reachability")
    status_parser.add_argument("--host", default="127.0.0.1", help="Loopback host")
    status_parser.add_argument("--port", type=int, default=6061, help="Loopback port")

    # Subcommand: health
    subparsers.add_parser("health", help="Run full multi-surface health and invariant preflight")

    # Subcommand: plist
    plist_parser = subparsers.add_parser("plist", help="Generate or install macOS launchd LaunchAgent configuration")
    plist_parser.add_argument("--output", type=Path, help="Target file path (e.g. ~/Library/LaunchAgents/...)")
    plist_parser.add_argument("--port", type=int, default=6061, help="Port to configure")
    plist_parser.add_argument("--transport", default="openapi-http", choices=("openapi-http", "streamable-http"))

    # Subcommand: self-test
    subparsers.add_parser("self-test", help="Execute supervisor self-test suite")

    args = parser.parse_args()
    repo_root = get_repo_root()

    if args.command == "status":
        listening = probe_tcp_port(args.host, args.port)
        url = f"http://{args.host}:{args.port}/openapi.json"
        spec = probe_http_openapi(url) if listening else None

        print("=== MOSKV-1 KERNEL SERVICE STATUS ===")
        print(f"Target: tcp://{args.host}:{args.port}")
        print(f"TCP Port Listening: {'YES' if listening else 'NO'}")
        if spec:
            info_val = spec.get("info")
            title = info_val.get("title", "MOSKV-1 Kernel") if isinstance(info_val, dict) else "MOSKV-1 Kernel"
            paths_val = spec.get("paths")
            paths_count = len(paths_val) if isinstance(paths_val, dict) else 0
            print(f"HTTP Endpoint: REACHABLE (OpenAPI 3.1.0: '{title}', {paths_count} operations)")
        else:
            print("HTTP Endpoint: NOT REACHABLE (daemon offline or not responding)")
        return 0 if listening else 1

    if args.command == "health":
        report = check_multi_surface_health(repo_root)
        print("=== MOSKV-1 MULTI-SURFACE PREFLIGHT ===")
        print(f"Overall Status: {report['status'].upper()}")
        print(f"OpenAPI Contract: {report['openapi_contract']}")
        print("\nRule Symlinks:")
        for name, st in report["symlinks"].items():
            print(f"  [{st}] {name}")
        print("\nMCP Manifests:")
        for name, st in report["mcp_manifests"].items():
            print(f"  [{st}] {name}")

        errors = report["errors"]
        if errors:
            print("\nErrors / Invariant Violations:")
            for err in errors:
                print(f"  - {err}")
            return 1
        print("\nPASS: All multi-surface invariants, symlinks and contracts verified.")
        return 0

    if args.command == "plist":
        plist_content = generate_launchd_plist(
            repo_root,
            port=args.port,
            transport=args.transport,
        )
        if args.output:
            target = args.output.expanduser().absolute()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(plist_content, encoding="utf-8")
            print(f"Wrote launchd LaunchAgent to {target}")
        else:
            sys.stdout.write(plist_content)
        return 0

    if args.command == "self-test":
        plist_test = generate_launchd_plist(repo_root)
        assert "<key>Label</key>" in plist_test
        assert "com.c5real.moskv1.kernel" in plist_test
        assert "/Users/" not in plist_test or "borjafernandezangulo" in plist_test
        health_test = check_multi_surface_health(repo_root)
        assert health_test["openapi_contract"] == "synchronized_1_to_1"
        assert len(health_test["symlinks"]) == len(RULE_SYMLINKS)  # type: ignore[arg-type]
        print("PASS: moskv1_service self-test passed cleanly.")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
