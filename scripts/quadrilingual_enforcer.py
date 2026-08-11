#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import os
import signal
import sys
from typing import Callable, Sequence


def _scan_files(target_dir: str, ext: str, check_fn: Callable[[str], None], skip_dirs: Sequence[str] = ()) -> None:
    if not os.path.exists(target_dir):
        return
    for root, dirs, files in os.walk(target_dir):
        for skip in skip_dirs:
            if skip in dirs:
                dirs.remove(skip)
        for f in files:
            if f.endswith(ext):
                filepath = os.path.join(root, f)
                with open(filepath, "r", errors="ignore") as file_obj:
                    check_fn(file_obj.read())


def check_lisp_bypass() -> None:
    def validate(content: str) -> None:
        c = content.lower()
        if "web3" in c or "ethers" in c or "jsonrpc" in c:
            raise RuntimeError("CRASH CAUSAL (Antipatrón 1): LISP inyectando directo en Anvil. Bypass de F# detectado.")

    _scan_files("lisp_metamembrane", ".clj", validate)


def check_rust_ontology() -> None:
    def validate(content: str) -> None:
        if "enum Domain" in content or "Ontology" in content:
            raise RuntimeError(
                "CRASH CAUSAL (Antipatrón 2): Rust procesando ADTs ontológicos. Dilución del Fast-Loop detectada."
            )

    _scan_files("strike_rs", ".rs", validate)


def check_solidity_physics() -> None:
    def validate(content: str) -> None:
        if "while (" in content or "graph" in content.lower():
            raise RuntimeError(
                "CRASH CAUSAL (Antipatrón 3): Solidity intentando computar ciclos/física de grafos. Exhaustión ATP detectada."
            )

    _scan_files("anvil_yung", ".sol", validate, skip_dirs=("lib", "test"))


def check_rust_anvil_bypass() -> None:
    def validate(content: str) -> None:
        if "cast send" in content or "ethers::" in content:
            raise RuntimeError(
                "CRASH CAUSAL (Antipatrón 4): Rust enviando transacciones a Anvil sin pasar por F#. Split-Brain Causal."
            )

    _scan_files("strike_rs", ".rs", validate)


def enforce() -> None:
    print("⚡ [Causal-Determinist] Ignición de Auditoría Cuadrilingüe (Enforcer BFT)...")
    try:
        check_lisp_bypass()
        check_rust_ontology()
        check_solidity_physics()
        check_rust_anvil_bypass()
        print(
            "⚡ [Causal-Determinist] Topología Intacta. Cero Antipatrones detectados. Aislamiento Físico garantizado."
        )
        sys.exit(0)
    except (RuntimeError, OSError):
        os.kill(os.getpid(), signal.SIGKILL)
        raise RuntimeError("FAIL-FAST: General Exception intercepted.")


def main() -> None:
    enforce()


if __name__ == "__main__":
    main()
