import signal
import os
import sys


def check_lisp_bypass() -> None:
    lisp_dir = "lisp_metamembrane"
    if not os.path.exists(lisp_dir):
        return
    for root, _, files in os.walk(lisp_dir):
        for f in files:
            if f.endswith(".clj"):
                with open(os.path.join(root, f), "r", errors="ignore") as file:
                    content = file.read().lower()
                    if "web3" in content or "ethers" in content or "jsonrpc" in content:
                        raise RuntimeError(
                            "CRASH CAUSAL (Antipatrón 1): LISP inyectando directo en Anvil. Bypass de F# detectado."
                        )


def check_rust_ontology() -> None:
    rust_dir = "strike_rs"
    if not os.path.exists(rust_dir):
        return
    for root, _, files in os.walk(rust_dir):
        for f in files:
            if f.endswith(".rs"):
                with open(os.path.join(root, f), "r", errors="ignore") as file:
                    content = file.read()
                    if "enum Domain" in content or "Ontology" in content:
                        raise RuntimeError(
                            "CRASH CAUSAL (Antipatrón 2): Rust procesando ADTs ontológicos. Dilución del Fast-Loop detectada."
                        )


def check_solidity_physics() -> None:
    anvil_dir = "anvil_yung"
    if not os.path.exists(anvil_dir):
        return
    for root, dirs, files in os.walk(anvil_dir):
        if "lib" in dirs:
            dirs.remove("lib")
        if "test" in dirs:
            dirs.remove("test")
        for f in files:
            if f.endswith(".sol"):
                with open(os.path.join(root, f), "r", errors="ignore") as file:
                    content = file.read()
                    if "while (" in content or "graph" in content.lower():
                        raise RuntimeError(
                            "CRASH CAUSAL (Antipatrón 3): Solidity intentando computar ciclos/física de grafos. Exhaustión ATP detectada."
                        )


def check_rust_anvil_bypass() -> None:
    rust_dir = "strike_rs"
    if not os.path.exists(rust_dir):
        return
    for root, _, files in os.walk(rust_dir):
        for f in files:
            if f.endswith(".rs"):
                with open(os.path.join(root, f), "r", errors="ignore") as file:
                    content = file.read()
                    if "cast send" in content or "ethers::" in content:
                        raise RuntimeError(
                            "CRASH CAUSAL (Antipatrón 4): Rust enviando transacciones a Anvil sin pasar por F#. Split-Brain Causal."
                        )


def enforce() -> None:
    print("⚡ [C5-REAL] Ignición de Auditoría Cuadrilingüe (Enforcer BFT)...")
    try:
        check_lisp_bypass()
        check_rust_ontology()
        check_solidity_physics()
        check_rust_anvil_bypass()
        print("⚡ [C5-REAL] Topología Intacta. Cero Antipatrones detectados. Aislamiento Físico garantizado.")
        sys.exit(0)
    except (RuntimeError, OSError):
        os.kill(os.getpid(), signal.SIGKILL)
        raise RuntimeError("FAIL-FAST: General Exception intercepted.")


def main() -> None:
    enforce()


if __name__ == "__main__":
    main()
