#!/usr/bin/env python3
"""Replacement for the historical SHARUR benchmark: bounded byte sampling only.

360 tasks are not 1,296,000 agents. Timings cover sampling/hash work, not semantic
verification or Grok's internal infrastructure. No remote calls or execution of input.
"""

import argparse
import hashlib
import json
import struct
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def inspect_macho(data):
    """Check container/table bounds only. Does not authenticate the application."""
    if len(data) < 32:
        raise ValueError("INVALID_BINARY: truncated header")
    if data[:4] in (b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca"):
        endian = ">" if data[:4] == b"\xca\xfe\xba\xbe" else "<"
        count = struct.unpack_from(endian + "I", data, 4)[0]
        if not 0 < count <= (len(data) - 8) // 20:
            raise ValueError("INVALID_BINARY: fat architecture table")
        for idx in range(count):
            _, _, offset, size, _ = struct.unpack_from(endian + "IIIII", data, 8 + idx * 20)
            if offset < 8 + count * 20 or size < 32 or offset + size > len(data):
                raise ValueError("INVALID_BINARY: slice bounds")
            if data[offset : offset + 4] not in (b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf"):
                raise ValueError("INVALID_BINARY: unsupported slice")
            inspect_macho(data[offset : offset + size])
        return "MACH_O_FAT_STRUCTURAL_ONLY"
    if data[:4] not in (b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf"):
        raise ValueError("INVALID_BINARY: unsupported Mach-O magic")
    endian = "<" if data[:4] == b"\xcf\xfa\xed\xfe" else ">"
    _, _, _, _, count, size, _, _ = struct.unpack_from(endian + "8I", data)
    if count == 0 or size < count * 8 or 32 + size > len(data):
        raise ValueError("INVALID_BINARY: load command table bounds")
    offset = 32
    for _ in range(count):
        if offset + 8 > 32 + size:
            raise ValueError("INVALID_BINARY: truncated command")
        _, command_size = struct.unpack_from(endian + "II", data, offset)
        if command_size < 8 or command_size % 8 or offset + command_size > 32 + size:
            raise ValueError("INVALID_BINARY: command bounds")
        offset += command_size
    if offset != 32 + size:
        raise ValueError("INVALID_BINARY: inconsistent command count")
    return "MACH_O_64_STRUCTURAL_ONLY"


def run_benchmark(binary_path, *, sample_only=False, simulation=False):
    start = time.perf_counter()
    report = {
        "mode": "simulation" if simulation else ("sampling" if sample_only else "verification"),
        "real_verification": False,
        "verified_agents": 0,
        "verification_rate": None,
        "tasks_executed": 0,
        "passed": False,
        "limitations": [
            "APPLICATION_IDENTITY_NOT_VERIFIED",
            "NO_SEMANTIC_VERIFIER",
            "NO_AGENT_EXECUTION",
            "NO_INFRASTRUCTURE_INFERENCE",
        ],
    }
    if sample_only and simulation:
        report.update(status="ERROR", error="Choose one mode")
        return report
    try:
        if simulation:
            if binary_path is not None:
                raise ValueError("Simulation takes no application path")
            data = bytes(range(256)) * 4096
            report["input_origin"] = "synthetic_pattern"
            report["binary_format"] = "SYNTHETIC_BYTES"
        else:
            if binary_path is None:
                raise ValueError("MISSING_EVIDENCE: binary path required")
            data = Path(binary_path).read_bytes()
            report["input_origin"] = str(Path(binary_path).resolve())
            report["binary_format"] = inspect_macho(data)
        if len(data) < 256:
            raise ValueError("INVALID_BINARY: fewer than 256 bytes for sampling")
        report.update(binary_size_bytes=len(data), binary_sha256=hashlib.sha256(data).hexdigest())
        if not (sample_only or simulation):
            report.update(
                status="FAIL_MISSING_EVIDENCE", error="A binary and its header cannot verify Grok or autonomous agents"
            )
            return report

        def sample(task_id):
            offset = (task_id * 16384) % (len(data) - 255)
            chunk = data[offset : offset + 256]
            return {
                "task_id": task_id,
                "offset": offset,
                "sample_bytes": len(chunk),
                "sample_sha256": hashlib.sha256(chunk).hexdigest(),
                "distinct_byte_fraction": len(set(chunk)) / 256.0,
            }

        sampling_start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=64) as pool:
            samples = list(pool.map(sample, range(360)))
        report.update(
            tasks_executed=len(samples),
            worker_limit=64,
            unique_sample_offsets=len({s["offset"] for s in samples}),
            bytes_sampled_with_repetition=sum(s["sample_bytes"] for s in samples),
            sampling_duration_sec=time.perf_counter() - sampling_start,
            total_elapsed_sec=time.perf_counter() - start,
            samples=samples,
            status="SIMULATION_COMPLETED" if simulation else "SAMPLING_COMPLETED",
            passed=True,
        )
    except (OSError, ValueError, struct.error) as exc:
        report.update(status="FAIL_INVALID_INPUT", error=f"{type(exc).__name__}: {exc}")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("binary", nargs="?", type=Path)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--sample-only", action="store_true", help="Inspect local bytes; no semantic verification")
    modes.add_argument("--simulate", action="store_true", help="Sample explicit synthetic data")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = run_benchmark(args.binary, sample_only=args.sample_only, simulation=args.simulate)
    encoded = json.dumps(result, indent=2, allow_nan=False)
    if args.output:
        args.output.write_text(encoded + "\n")
    print(encoded)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
