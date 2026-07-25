from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from babylon60.core.crypto import _check_no_floats


class ZKVerificationError(RuntimeError):
    """Exception raised when ZK attestation verification fails or receives invalid inputs."""

    pass


class NULZKVerifier:
    """
    C5-REAL ZK Verifier Bridge for NUL-ZK Zero-Knowledge Attestations.
    
    Invariants Enforced:
      - INV_C5_33: Safe subprocess argument vectorization without shell=True.
      - INV_C5_18: Absolute ban on IEEE 754 floating-point numbers in consensus & ZK payloads.
    """

    def __init__(self, binary_path: Path | str | None = None) -> None:
        self.binary_path = Path(binary_path) if binary_path else None

    def find_nul_zk_binary(self) -> Path:
        """
        Dynamically resolves the nul_zk executable binary without shell invocation.
        """
        if self.binary_path and self.binary_path.exists() and self.binary_path.is_file():
            return self.binary_path.resolve()

        root_dir = Path(__file__).resolve().parents[2]
        candidates = [
            root_dir / "proof_kernel" / "NUL-ZK" / "target" / "debug" / "nul_zk",
            root_dir / "proof_kernel" / "NUL-ZK" / "target" / "release" / "nul_zk",
        ]
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return candidate.resolve()

        sys_binary = shutil.which("nul_zk")
        if sys_binary:
            return Path(sys_binary).resolve()

        raise ZKVerificationError(
            "INV_C5_33: 'nul_zk' binary not found on system or proof_kernel/NUL-ZK build target path."
        )

    def compile_circuit(self, circuit_file: Path | str) -> dict[str, Any]:
        """
        Compiles a .nul circuit to JSON IR via safe subprocess execution (INV_C5_33).
        Validates output to ensure zero float values (INV_C5_18).
        """
        circuit_path = Path(circuit_file).resolve()
        if not circuit_path.exists() or not circuit_path.is_file():
            raise ZKVerificationError(f"Circuit file does not exist: {circuit_path}")

        nul_zk_bin = self.find_nul_zk_binary()

        # INV_C5_33: Explicit vector command list, shell=False
        cmd = [str(nul_zk_bin), str(circuit_path)]
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                shell=False,
                cwd=str(circuit_path.parent),
            )
        except OSError as exc:
            raise ZKVerificationError(
                f"INV_C5_33: Failed to execute NUL-ZK binary process '{nul_zk_bin}': {exc}"
            ) from exc

        if res.returncode != 0:
            raise ZKVerificationError(
                f"NUL-ZK compilation failed (exit code {res.returncode}): {res.stderr.strip()}"
            )

        json_path = circuit_path.with_suffix(".json")
        if not json_path.exists():
            raise ZKVerificationError(f"Expected compiled JSON IR missing at: {json_path}")

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                compiled_ir = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            raise ZKVerificationError(f"Failed to read compiled JSON IR at {json_path}: {exc}") from exc

        # INV_C5_18: Verify no floating point values in compiled circuit IR
        _check_no_floats(compiled_ir)
        return compiled_ir

    def verify_attestation(self, attestation: dict[str, Any]) -> bool:
        """
        Verifies a NUL-ZK attestation payload.
        
        attestation payload structure:
          - circuit_file (str | Path): path to .nul circuit file
          - public_inputs (dict[str, int]): map of public variable names to int values
          - private_inputs (dict[str, int], optional): map of private variable names to int values
          - compiled_ir (dict, optional): pre-compiled circuit IR
        """
        # INV_C5_18: Reject any payload containing floats
        _check_no_floats(attestation)

        circuit_file = attestation.get("circuit_file") or attestation.get("circuit_path")
        if not circuit_file and "compiled_ir" not in attestation:
            raise ZKVerificationError("Attestation payload missing 'circuit_file' or 'compiled_ir'")

        public_inputs: dict[str, Any] = attestation.get("public_inputs", {})
        private_inputs: dict[str, Any] = attestation.get("private_inputs", {})

        if not isinstance(public_inputs, dict) or not isinstance(private_inputs, dict):
            raise ZKVerificationError("public_inputs and private_inputs must be dictionaries")

        # Validate that input values are integers (no float coercions allowed)
        for var, val in {**public_inputs, **private_inputs}.items():
            if not isinstance(val, int) or isinstance(val, bool):
                raise ZKVerificationError(
                    f"INV_C5_18: Circuit input '{var}' must be an exact integer, got {type(val).__name__}"
                )

        if "compiled_ir" in attestation:
            compiled_ir = attestation["compiled_ir"]
            _check_no_floats(compiled_ir)
        else:
            compiled_ir = self.compile_circuit(str(circuit_file))

        return self.evaluate_circuit(compiled_ir, public_inputs, private_inputs)

    @staticmethod
    def evaluate_circuit(
        compiled_ir: dict[str, Any], public_inputs: dict[str, int], private_inputs: dict[str, int]
    ) -> bool:
        """
        Evaluates the gates of a compiled NUL-ZK circuit against provided inputs.
        """
        env: dict[str, int] = {}
        for var, val in public_inputs.items():
            env[var] = val
        for var, val in private_inputs.items():
            env[var] = val

        gates = compiled_ir.get("gates", [])
        for gate in gates:
            if "Constant" in gate:
                info = gate["Constant"]
                env[info["out"]] = int(info["value"])
            elif "Add" in gate:
                info = gate["Add"]
                if info["lhs"] not in env or info["rhs"] not in env:
                    raise ZKVerificationError(
                        f"Missing variable in evaluation: {info['lhs']} or {info['rhs']}"
                    )
                env[info["out"]] = env[info["lhs"]] + env[info["rhs"]]
            elif "Sub" in gate:
                info = gate["Sub"]
                if info["lhs"] not in env or info["rhs"] not in env:
                    raise ZKVerificationError(
                        f"Missing variable in evaluation: {info['lhs']} or {info['rhs']}"
                    )
                env[info["out"]] = env[info["lhs"]] - env[info["rhs"]]
            elif "Mul" in gate:
                info = gate["Mul"]
                if info["lhs"] not in env or info["rhs"] not in env:
                    raise ZKVerificationError(
                        f"Missing variable in evaluation: {info['lhs']} or {info['rhs']}"
                    )
                env[info["out"]] = env[info["lhs"]] * env[info["rhs"]]
            elif "AssertEq" in gate:
                info = gate["AssertEq"]
                if info["lhs"] not in env or info["rhs"] not in env:
                    raise ZKVerificationError(
                        f"Missing variable in evaluation assertion: {info['lhs']} or {info['rhs']}"
                    )
                if env[info["lhs"]] != env[info["rhs"]]:
                    return False

        return True


def verify_zk_attestation(attestation: dict[str, Any], binary_path: Path | str | None = None) -> bool:
    """Convenience function to verify a NUL-ZK attestation payload."""
    verifier = NULZKVerifier(binary_path=binary_path)
    return verifier.verify_attestation(attestation)


def verify_nul_zk_proof(
    circuit_file: Path | str,
    public_inputs: dict[str, int],
    private_inputs: dict[str, int] | None = None,
    binary_path: Path | str | None = None,
) -> bool:
    """Convenience function to verify a NUL-ZK proof given a circuit file and inputs."""
    attestation = {
        "circuit_file": str(circuit_file),
        "public_inputs": public_inputs,
        "private_inputs": private_inputs or {},
    }
    return verify_zk_attestation(attestation, binary_path=binary_path)
