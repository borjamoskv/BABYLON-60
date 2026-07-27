# [C5-REAL] Exergy-Maximized
from __future__ import annotations

import asyncio
from pathlib import Path

from babylon60.guards._seal_printer import SealPrinter

_NOQA_MARKERS = ("# noqa: BLE001", "# noqa:BLE001", "# deliberate boundary")
_EXCLUDE = frozenset(["legion_vectors.py", "legion.py"])


async def run_cobbler_audit(
    cached_files: dict[Path, str],
    printer: SealPrinter,
) -> bool:
    """Run Cobbler's Compliance audit and print results. Returns True if passed."""
    try:
        from babylon60.swarm.legion_vectors import EntropyDemon, Intruder
    except ImportError:
        printer.warn("Cobbler skipped: legion_vectors not importable.")
        return True

    demon = EntropyDemon()
    intruder = Intruder()
    demon_violations: list[str] = []
    intruder_violations: list[str] = []

    engine_parts = ("cortex", "engine")
    engine_files = {
        p: content
        for p, content in cached_files.items()
        if all(part in p.parts for part in engine_parts) and p.name not in _EXCLUDE
    }

    async def _audit(py_file: Path, source: str) -> None:
        cleaned = "\n".join(
            line for line in source.splitlines() if not any(m in line for m in _NOQA_MARKERS)
        )
        demon_hits = await demon.attack(cleaned, context={})
        fragility = [h for h in demon_hits if "Bare `except`" in h]
        if fragility:
            demon_violations.append(f"{py_file.name}: {fragility}")

        intruder_hits = await intruder.attack(source, context={})
        if intruder_hits:
            intruder_violations.append(f"{py_file.name}: {intruder_hits}")

    await asyncio.gather(*(_audit(p, c) for p, c in engine_files.items()))

    passed = True
    if demon_violations:
        printer.fail(f"EntropyDemon fired on engine ({len(demon_violations)} files)")
        for v in demon_violations:
            printer.warn(f"      ↳ {v}")
        passed = False
    else:
        printer.success(f"EntropyDemon: engine clean ({len(engine_files)} files).")

    if intruder_violations:
        printer.fail(f"Intruder found issues ({len(intruder_violations)} files)")
        for v in intruder_violations:
            printer.warn(f"      ↳ {v}")
        passed = False
    else:
        printer.success("Intruder: no eval/exec/os.system in engine.")

    return passed
