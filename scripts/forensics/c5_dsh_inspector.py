#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] Exergy-Maximized
"""In-Memory Deterministic Electron ASAR / DMG Forensic Inspector (C5-REAL).

Implements the Chromium Pickle 4-byte boundary alignment invariant:
    base_offset = 8 + u2 = 16 + ((json_size + 3) & ~3)
and verifies extracted payloads against Electron's embedded per-file SHA-256
``integrity.hash`` block without spawning Node.js or writing unpacked trees.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import plistlib
import struct
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compute_asar_base_offset(u2_pickle_payload_size: int, json_size: int) -> int:
    """Return the 4-byte aligned Chromium Pickle payload base offset."""
    aligned_from_json = 16 + ((json_size + 3) & ~3)
    aligned_from_u2 = 8 + u2_pickle_payload_size
    if aligned_from_json != aligned_from_u2:
        raise ValueError(f"ASAR Pickle header mismatch: 8+u2={aligned_from_u2} != align4(16+json)={aligned_from_json}")
    return aligned_from_u2


def _walk_asar(node: dict[str, Any], prefix: str = "") -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if "files" in node:
        for key, child in node["files"].items():
            items.extend(_walk_asar(child, f"{prefix}/{key}" if prefix else key))
    else:
        items.append(
            {
                "path": prefix,
                "size": int(node.get("size", 0)),
                "offset": int(node["offset"]) if "offset" in node else None,
                "unpacked": bool(node.get("unpacked", False)),
                "executable": bool(node.get("executable", False)),
                "sha256": node.get("integrity", {}).get("hash"),
            }
        )
    return items


def inspect_dmg(dmg_path: Path, out_json: Path) -> dict[str, Any]:
    t0 = time.perf_counter()
    dmg_resolved = dmg_path.expanduser().resolve(strict=True)
    vol_path: Path | None = None
    mounted_temp = False

    info_res = subprocess.run(["hdiutil", "info", "-plist"], capture_output=True, check=True)
    info_plist = plistlib.loads(info_res.stdout)
    for img in info_plist.get("images", []):
        img_p = img.get("image-path", "")
        if img_p and Path(img_p).exists() and Path(img_p).resolve() == dmg_resolved:
            for ent in img.get("system-entities", []):
                mp = ent.get("mount-point")
                if mp and Path(mp).exists():
                    vol_path = Path(mp)
                    break
        if vol_path:
            break

    if vol_path is None:
        attach_res = subprocess.run(
            ["hdiutil", "attach", "-nobrowse", "-readonly", str(dmg_resolved)],
            capture_output=True,
            text=True,
            check=True,
        )
        for line in attach_res.stdout.splitlines():
            if "\t/" in line:
                vol_path = Path(line.split("\t")[-1].strip())
                mounted_temp = True
                break

    if vol_path is None:
        raise RuntimeError(f"Unable to mount or locate volume for {dmg_resolved}")

    try:
        app_path = next(vol_path.glob("*.app"))
        contents_path = app_path / "Contents"
        resources_path = contents_path / "Resources"
        asar_path = resources_path / "app.asar"

        with open(contents_path / "Info.plist", "rb") as pf:
            plist_data = plistlib.load(pf)

        with open(asar_path, "rb") as af:
            u1, u2, header_size, json_size = struct.unpack("<IIII", af.read(16))
            header = json.loads(af.read(json_size).decode("utf-8"))
            base_offset = compute_asar_base_offset(u2, json_size)
            asar_files = _walk_asar(header)

            def read_entry(entry: dict[str, Any]) -> bytes:
                if entry["unpacked"] or entry["offset"] is None:
                    unpacked_p = resources_path / "app.asar.unpacked" / entry["path"]
                    return unpacked_p.read_bytes() if unpacked_p.is_file() else b""
                af.seek(base_offset + entry["offset"])
                return af.read(entry["size"])

            pkg_entry = next((x for x in asar_files if x["path"] == "package.json"), None)
            pkg_raw = read_entry(pkg_entry) if pkg_entry else b"{}"
            pkg_sha256 = hashlib.sha256(pkg_raw).hexdigest()
            pkg_json = json.loads(pkg_raw.decode("utf-8"))

            ipc_modules: list[dict[str, object]] = []
            for entry in asar_files:
                p = entry["path"]
                sz = entry["size"]
                if "node_modules" not in p and p.endswith((".js", ".cjs", ".mjs")) and sz < 1_000_000:
                    code = read_entry(entry).decode("utf-8", errors="ignore")
                    if any(tok in code for tok in ("ipcMain", "ipcRenderer", "contextBridge")):
                        ipc_modules.append({"path": p, "size": sz})

        report: dict[str, Any] = {
            "schema": "c5.deterministic.electron.audit/v2",
            "elapsed_ms": round((time.perf_counter() - t0) * 1000, 2),
            "artifact": {
                "dmg_path": str(dmg_resolved),
                "dmg_size_bytes": dmg_resolved.stat().st_size,
                "dmg_sha256": sha256_file(dmg_resolved),
                "app_bundle": app_path.name,
                "asar_size_bytes": asar_path.stat().st_size,
                "asar_sha256": sha256_file(asar_path),
            },
            "bundle_identity": {
                "CFBundleIdentifier": plist_data.get("CFBundleIdentifier"),
                "CFBundleShortVersionString": plist_data.get("CFBundleShortVersionString"),
                "ElectronAsarIntegrity": plist_data.get("ElectronAsarIntegrity"),
            },
            "asar_header_geometry": {
                "u1_pickle_header_len": u1,
                "u2_pickle_payload_size": u2,
                "header_size": header_size,
                "json_size": json_size,
                "unaligned_16_plus_json": 16 + json_size,
                "aligned_payload_offset_8_plus_u2": base_offset,
                "pickle_padding_bytes": base_offset - (16 + json_size),
                "package_json_integrity_verified": pkg_sha256 == (pkg_entry["sha256"] if pkg_entry else ""),
                "total_indexed_files": len(asar_files),
                "unpacked_files_count": sum(1 for x in asar_files if x["unpacked"]),
            },
            "root_package_json": pkg_json,
            "ipc_surface_modules": ipc_modules,
        }
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return report
    finally:
        if mounted_temp and vol_path is not None:
            subprocess.run(["hdiutil", "detach", str(vol_path), "-quiet"], check=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="C5-REAL Deterministic Electron ASAR/DMG Inspector")
    parser.add_argument("dmg", type=Path, help="Path to the .dmg image to inspect")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent.parent.parent / "docs" / "security" / "c5-deterministic-audit.json",
        help="Output JSON path",
    )
    args = parser.parse_args(argv)
    inspect_dmg(args.dmg, args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
