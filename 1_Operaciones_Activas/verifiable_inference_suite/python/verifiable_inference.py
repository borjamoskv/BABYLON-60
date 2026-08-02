# C5-REAL EXERGY CERTIFIED
"""
Python FFI Bindings for Verifiable Inference Suite Engine.
Provides Python wrappers via ctypes for C SIMD 10-primitives, Landauer energy,
standard part map st(x) noise dissipation, ZK-SNARK BN254 R1CS proof generation/verification,
and LogUp fractional lookup table argument provers.
"""

import ctypes
import os
import sys
import struct
from typing import List, Tuple, Optional, Union


class PrimitiveResults(ctypes.Structure):
    """C-compatible primitive results struct matching primitive_results_t."""
    _fields_ = [
        ("pi_inv", ctypes.c_float),
        ("pi_entr", ctypes.c_float),
        ("pi_zk", ctypes.c_float),
        ("pi_causal", ctypes.c_float),
        ("pi_ll", ctypes.c_float),
        ("pi_st", ctypes.c_float),
        ("pi_pmi", ctypes.c_float),
        ("pi_landauer", ctypes.c_double),
        ("pi_kl", ctypes.c_float),
        ("pi_dedup", ctypes.c_uint64),
    ]

    def to_dict(self) -> dict:
        return {
            "pi_inv": float(self.pi_inv),
            "pi_entr": float(self.pi_entr),
            "pi_zk": float(self.pi_zk),
            "pi_causal": float(self.pi_causal),
            "pi_ll": float(self.pi_ll),
            "pi_st": float(self.pi_st),
            "pi_pmi": float(self.pi_pmi),
            "pi_landauer": float(self.pi_landauer),
            "pi_kl": float(self.pi_kl),
            "pi_dedup": int(self.pi_dedup),
        }

    def __repr__(self) -> str:
        return (
            f"PrimitiveResults(pi_inv={self.pi_inv:.4f}, pi_entr={self.pi_entr:.4f}, "
            f"pi_zk={self.pi_zk:.4f}, pi_causal={self.pi_causal:.4f}, pi_ll={self.pi_ll:.4f}, "
            f"pi_st={self.pi_st:.4f}, pi_pmi={self.pi_pmi:.4f}, pi_landauer={self.pi_landauer:.6e}, "
            f"pi_kl={self.pi_kl:.4f}, pi_dedup={self.pi_dedup})"
        )


class VerifiableInferenceEngine:
    """Python wrapper interface for libverifiable_inference_engine C FFI."""

    def __init__(self, lib_path: Optional[str] = None):
        if lib_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            candidates = [
                os.path.join(base_dir, "target", "release", "libverifiable_inference_engine.dylib"),
                os.path.join(base_dir, "target", "release", "libverifiable_inference_engine.so"),
                os.path.join(base_dir, "target", "release", "verifiable_inference_engine.dll"),
            ]
            for candidate in candidates:
                if os.path.exists(candidate):
                    lib_path = candidate
                    break
            if lib_path is None:
                raise FileNotFoundError(
                    "Compiled libverifiable_inference_engine dynamic library not found. "
                    "Run `cargo build --release` first."
                )

        self.lib_path = lib_path
        self._lib = ctypes.CDLL(lib_path)
        self._setup_ffi()

    def _setup_ffi(self):
        # 1. run_verifiable_primitives / execute_10_primitives
        if hasattr(self._lib, "execute_10_primitives"):
            self._execute_10_primitives = self._lib.execute_10_primitives
        else:
            self._execute_10_primitives = self._lib.run_verifiable_primitives

        self._execute_10_primitives.argtypes = [
            ctypes.POINTER(ctypes.c_float),
            ctypes.POINTER(ctypes.c_float),
            ctypes.c_size_t,
            ctypes.POINTER(PrimitiveResults),
        ]
        self._execute_10_primitives.restype = ctypes.c_int

        # 1b. run_batch_primitives_loop
        if hasattr(self._lib, "run_batch_primitives_loop"):
            self._run_batch_primitives_loop = self._lib.run_batch_primitives_loop
            self._run_batch_primitives_loop.argtypes = [
                ctypes.POINTER(ctypes.c_float),
                ctypes.POINTER(ctypes.c_float),
                ctypes.c_size_t,
                ctypes.c_size_t,
                ctypes.POINTER(PrimitiveResults),
            ]
            self._run_batch_primitives_loop.restype = ctypes.c_int
        else:
            self._run_batch_primitives_loop = None

        # 2. calculate_landauer_energy
        if hasattr(self._lib, "calculate_landauer_energy"):
            self._calculate_landauer_energy = self._lib.calculate_landauer_energy
            self._calculate_landauer_energy.argtypes = [
                ctypes.POINTER(ctypes.c_float),
                ctypes.POINTER(ctypes.c_float),
                ctypes.c_size_t,
                ctypes.c_double,
            ]
            self._calculate_landauer_energy.restype = ctypes.c_double
        else:
            self._calculate_landauer_energy = None

        # 3. project_standard_part
        if hasattr(self._lib, "project_standard_part"):
            self._project_standard_part = self._lib.project_standard_part
            self._project_standard_part.argtypes = [
                ctypes.POINTER(ctypes.c_float),
                ctypes.POINTER(ctypes.c_float),
                ctypes.c_size_t,
                ctypes.c_float,
                ctypes.POINTER(ctypes.c_float),
            ]
            self._project_standard_part.restype = ctypes.c_float
        else:
            self._project_standard_part = None

        # 4. prove_and_verify_zk_logup
        self._prove_and_verify_zk_logup = self._lib.prove_and_verify_zk_logup
        self._prove_and_verify_zk_logup.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
        ]
        self._prove_and_verify_zk_logup.restype = ctypes.c_int

        # 5. create_bn254_r1cs_proof
        self._create_bn254_r1cs_proof = self._lib.create_bn254_r1cs_proof
        self._create_bn254_r1cs_proof.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        self._create_bn254_r1cs_proof.restype = ctypes.c_int

        # 6. verify_bn254_r1cs_proof
        self._verify_bn254_r1cs_proof = self._lib.verify_bn254_r1cs_proof
        self._verify_bn254_r1cs_proof.argtypes = [
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_size_t,
        ]
        self._verify_bn254_r1cs_proof.restype = ctypes.c_int

    def execute_10_primitives(
        self,
        input_a: Union[List[float], ctypes.Array],
        input_b: Union[List[float], ctypes.Array],
    ) -> PrimitiveResults:
        """Executes unified 10-primitive SIMD batch pipeline on two vectors."""
        length = len(input_a)
        if len(input_b) != length:
            raise ValueError("Input vectors A and B must have identical length.")
        if length == 0:
            raise ValueError("Vector length must be > 0.")

        if isinstance(input_a, ctypes.Array):
            ptr_a = input_a
        else:
            arr_a = (ctypes.c_float * length)(*input_a)
            ptr_a = arr_a

        if isinstance(input_b, ctypes.Array):
            ptr_b = input_b
        else:
            arr_b = (ctypes.c_float * length)(*input_b)
            ptr_b = arr_b

        results = PrimitiveResults()
        res = self._execute_10_primitives(ptr_a, ptr_b, length, ctypes.byref(results))
        if res != 0:
            raise RuntimeError(f"execute_10_primitives failed with status code {res}")
        return results

    def batch_execute_10_primitives(
        self,
        input_a: Union[List[float], ctypes.Array],
        input_b: Union[List[float], ctypes.Array],
        iterations: int,
    ) -> PrimitiveResults:
        """Executes unified 10-primitive SIMD batch pipeline for `iterations` count."""
        length = len(input_a)
        if len(input_b) != length:
            raise ValueError("Input vectors A and B must have identical length.")
        if length == 0 or iterations <= 0:
            raise ValueError("Vector length and iterations must be > 0.")

        if isinstance(input_a, ctypes.Array):
            ptr_a = input_a
        else:
            arr_a = (ctypes.c_float * length)(*input_a)
            ptr_a = arr_a

        if isinstance(input_b, ctypes.Array):
            ptr_b = input_b
        else:
            arr_b = (ctypes.c_float * length)(*input_b)
            ptr_b = arr_b

        results = PrimitiveResults()
        if self._run_batch_primitives_loop is not None:
            res = self._run_batch_primitives_loop(ptr_a, ptr_b, length, iterations, ctypes.byref(results))
            if res != 0:
                raise RuntimeError(f"run_batch_primitives_loop failed with status code {res}")
        else:
            for _ in range(iterations):
                res = self._execute_10_primitives(ptr_a, ptr_b, length, ctypes.byref(results))
                if res != 0:
                    raise RuntimeError(f"execute_10_primitives failed with status code {res}")
        return results

    def calculate_landauer_energy(
        self,
        input_a: Union[List[float], ctypes.Array],
        input_b: Union[List[float], ctypes.Array],
        temp_kelvin: float = 300.0,
    ) -> float:
        r"""Calculates Landauer thermodynamic energy dissipation: E_min = k_B * T * ln(2) * \sum |A_i - B_i|."""
        length = len(input_a)
        if len(input_b) != length:
            raise ValueError("Input vectors A and B must have identical length.")
        if length == 0:
            return 0.0

        if isinstance(input_a, ctypes.Array):
            ptr_a = input_a
        else:
            arr_a = (ctypes.c_float * length)(*input_a)
            ptr_a = arr_a

        if isinstance(input_b, ctypes.Array):
            ptr_b = input_b
        else:
            arr_b = (ctypes.c_float * length)(*input_b)
            ptr_b = arr_b

        if self._calculate_landauer_energy is not None:
            return float(self._calculate_landauer_energy(ptr_a, ptr_b, length, temp_kelvin))
        else:
            res = self.execute_10_primitives(ptr_a, ptr_b)
            return float(res.pi_landauer)

    def project_standard_part(
        self,
        input_a: Union[List[float], ctypes.Array],
        input_b: Optional[Union[List[float], ctypes.Array]] = None,
        eps: float = 1e-6,
    ) -> Tuple[float, List[float]]:
        r"""Projects standard part map st(x) dissipating infinitesimal noise \epsilon \in \mu(0)."""
        length = len(input_a)
        if length == 0:
            return 0.0, []

        if isinstance(input_a, ctypes.Array):
            ptr_a = input_a
        else:
            arr_a = (ctypes.c_float * length)(*input_a)
            ptr_a = arr_a

        if input_b is None:
            arr_b = (ctypes.c_float * length)()
            ptr_b = arr_b
        elif isinstance(input_b, ctypes.Array):
            ptr_b = input_b
        else:
            arr_b = (ctypes.c_float * length)(*input_b)
            ptr_b = arr_b

        out_st = (ctypes.c_float * length)()
        if self._project_standard_part is not None:
            norm_st = self._project_standard_part(ptr_a, ptr_b, length, eps, out_st)
        else:
            res = self.execute_10_primitives(ptr_a, ptr_b)
            norm_st = res.pi_st
            for i in range(length):
                out_st[i] = input_a[i] if abs(input_a[i]) >= eps else 0.0

        return float(norm_st), [float(x) for x in out_st]

    def create_bn254_r1cs_proof(
        self,
        num_vars: int,
        num_pub: int,
        witness: List[int],
    ) -> bytes:
        """Generates BN254 R1CS ZK-SNARK proof from witness array."""
        num_witness = len(witness)
        payload = struct.pack("<III", num_vars, num_pub, num_witness)
        payload += b"".join(struct.pack("<Q", int(w)) for w in witness)

        payload_bytes = (ctypes.c_uint8 * len(payload)).from_buffer_copy(payload)
        proof_buf = (ctypes.c_uint8 * 4096)()
        out_len = ctypes.c_size_t(0)

        res = self._create_bn254_r1cs_proof(
            payload_bytes,
            len(payload),
            proof_buf,
            len(proof_buf),
            ctypes.byref(out_len),
        )
        if res != 0:
            raise RuntimeError(f"create_bn254_r1cs_proof failed with error code {res}")

        return bytes(proof_buf[: out_len.value])

    def verify_bn254_r1cs_proof(
        self,
        proof_bytes: bytes,
        public_inputs: Optional[List[int]] = None,
    ) -> bool:
        """Verifies BN254 R1CS ZK-SNARK proof."""
        if not proof_bytes:
            return False

        proof_arr = (ctypes.c_uint8 * len(proof_bytes)).from_buffer_copy(proof_bytes)
        pub_arr = None
        pub_len = 0
        if public_inputs:
            pub_payload = b"".join(struct.pack("<Q", int(p)) for p in public_inputs)
            pub_arr = (ctypes.c_uint8 * len(pub_payload)).from_buffer_copy(pub_payload)
            pub_len = len(pub_payload)

        res = self._verify_bn254_r1cs_proof(
            proof_arr,
            len(proof_bytes),
            pub_arr if pub_arr else None,
            pub_len,
        )
        return res == 0

    def prove_and_verify_zk_logup(
        self,
        table: List[int],
        lookups: List[int],
    ) -> bool:
        """Proves and verifies LogUp fractional lookup table argument."""
        payload = struct.pack("<I", len(table))
        payload += b"".join(struct.pack("<Q", int(t)) for t in table)
        payload += struct.pack("<I", len(lookups))
        payload += b"".join(struct.pack("<Q", int(l)) for l in lookups)

        payload_bytes = (ctypes.c_uint8 * len(payload)).from_buffer_copy(payload)
        res = self._prove_and_verify_zk_logup(payload_bytes, len(payload))
        return res == 0

    def run_teff_transition(
        self,
        tool_name: str,
        param: bytes = b"",
        est_tokens: int = 100,
        est_cost_usd: float = 0.0001,
    ) -> "TeffResult":
        """Executes full Teff end-to-end transition pipeline via Rust FFI."""
        if hasattr(self._lib, "run_teff_transition"):
            self._run_teff_transition = self._lib.run_teff_transition
            self._run_teff_transition.argtypes = [
                ctypes.c_char_p,
                ctypes.POINTER(ctypes.c_uint8),
                ctypes.c_size_t,
                ctypes.c_size_t,
                ctypes.c_double,
                ctypes.POINTER(TeffResult),
            ]
            self._run_teff_transition.restype = ctypes.c_int

            tool_b = tool_name.encode("utf-8")
            param_arr = (ctypes.c_uint8 * len(param)).from_buffer_copy(param) if param else None
            out_res = TeffResult()

            res = self._run_teff_transition(
                tool_b,
                param_arr if param_arr else None,
                len(param),
                est_tokens,
                est_cost_usd,
                ctypes.byref(out_res),
            )
            if res != 0:
                raise RuntimeError(f"run_teff_transition failed with status code {res}")
            return out_res
        else:
            raise NotImplementedError("run_teff_transition symbol not exported in loaded FFI library")


class TeffResult(ctypes.Structure):
    """C-compatible result struct for Teff transition execution."""
    _fields_ = [
        ("success", ctypes.c_int),
        ("wall_clock_ms", ctypes.c_uint64),
        ("gkat_latency_us", ctypes.c_uint64),
        ("sandbox_latency_us", ctypes.c_uint64),
        ("scitt_latency_us", ctypes.c_uint64),
        ("total_overhead_us", ctypes.c_uint64),
        ("canonical_hash", ctypes.c_uint8 * 32),
        ("scitt_statement_digest", ctypes.c_uint8 * 32),
        ("scitt_merkle_root", ctypes.c_uint8 * 32),
    ]

    def to_dict(self) -> dict:
        return {
            "success": bool(self.success),
            "wall_clock_ms": int(self.wall_clock_ms),
            "gkat_latency_us": int(self.gkat_latency_us),
            "sandbox_latency_us": int(self.sandbox_latency_us),
            "scitt_latency_us": int(self.scitt_latency_us),
            "total_overhead_us": int(self.total_overhead_us),
            "canonical_hash": bytes(self.canonical_hash).hex(),
            "scitt_statement_digest": bytes(self.scitt_statement_digest).hex(),
            "scitt_merkle_root": bytes(self.scitt_merkle_root).hex(),
        }

