#!/usr/bin/env python3
"""Telemetría térmica de silicio en Apple Silicon / Darwin (C5-REAL).

Consulta el estado térmico real del sustrato físico para alimentar el campo
`[ RÉGIMEN TÉRMICO ]` de la firma canónica MOSKV-1.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys


def get_cpu_brand() -> str:
    try:
        res = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "Apple Silicon"


def get_thermal_pressure() -> str:
    try:
        res = subprocess.run(
            ["pmset", "-g", "therm"],
            capture_output=True,
            text=True,
            check=True,
        )
        out = res.stdout.lower()
        if "warning" in out and "no thermal warning" not in out:
            return "Throttling / Alerta térmica"
        return "presión térmica normal"
    except Exception:
        return "normal"


def get_thermal_telemetry() -> dict[str, str]:
    brand = get_cpu_brand()
    pressure = get_thermal_pressure()
    status = "Nominal" if "normal" in pressure else "Degradado"
    summary = f"{status} ({brand}, {pressure})"
    return {
        "status": status,
        "cpu": brand,
        "pressure": pressure,
        "summary": summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emitir telemetría en JSON")
    args = parser.parse_args()

    data = get_thermal_telemetry()
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(data["summary"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
