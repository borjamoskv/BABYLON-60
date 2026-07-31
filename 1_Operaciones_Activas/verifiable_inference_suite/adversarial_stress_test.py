# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import sys
import time
import math
import ctypes
from python.verifiable_inference import VerifiableInferenceEngine, PrimitiveResults

def run_adversarial_suite():
    print("=== ADVERSARIAL STRESS SUITE FOR VERIFIABLE INFERENCE ENGINE ===")
    engine = VerifiableInferenceEngine()

    # Test 1: Landauer Energy Extremes
    print("[1] Testing Landauer Energy Edge Cases...")
    kb = 1.380649e-23
    ln2 = math.log(2.0)

    # Zero difference
    vec_a = [10.0] * 100
    vec_b = [10.0] * 100
    e_zero = engine.calculate_landauer_energy(vec_a, vec_b, 300.0)
    assert abs(e_zero) < 1e-15, f"Expected 0 Landauer energy, got {e_zero}"

    # 0 Kelvin (should return 0 energy dissiptation)
    e_0k = engine.calculate_landauer_energy([1.0, 2.0], [3.0, 4.0], 0.0)
    assert abs(e_0k) < 1e-15, f"Expected 0 Landauer energy at 0K, got {e_0k}"
    print("  -> Landauer edge cases PASSED.")

    # Test 2: Standard Part st(x) Noise Dissipation Boundary Values
    print("[2] Testing Standard Part st(x) Noise Dissipation Boundaries...")
    eps = 1e-4
    input_vec = [100.0, 1e-5, -1e-5, 0.0001, -0.0001, 0.00009, -0.00009]
    norm_st, out_st = engine.project_standard_part(input_vec, None, eps)

    # Values < eps in magnitude should be 0.0, values >= eps preserved
    expected = [100.0, 0.0, 0.0, 0.0001, -0.0001, 0.0, 0.0]
    for orig, res, exp in zip(input_vec, out_st, expected):
        assert abs(res - exp) < 1e-7, f"st(x) mismatch for {orig}: got {res}, expected {exp}"
    print("  -> Standard Part st(x) boundary cases PASSED.")

    # Test 3: BN254 R1CS Proof Adversarial Inputs
    print("[3] Testing BN254 R1CS ZK-SNARK Corrupted Proof Rejection...")
    valid_proof = engine.create_bn254_r1cs_proof(4, 2, [1, 15, 3, 5])
    assert engine.verify_bn254_r1cs_proof(valid_proof), "Valid proof failed verification!"

    # Corrupt single byte
    corrupted_bytes = bytearray(valid_proof)
    corrupted_bytes[10] ^= 0xFF
    assert not engine.verify_bn254_r1cs_proof(bytes(corrupted_bytes)), "Corrupted proof was accepted!"

    # Truncated proof
    truncated = valid_proof[:10]
    assert not engine.verify_bn254_r1cs_proof(truncated), "Truncated proof was accepted!"

    # Empty proof
    assert not engine.verify_bn254_r1cs_proof(b""), "Empty proof was accepted!"
    print("  -> BN254 R1CS adversarial tests PASSED.")

    # Test 4: LogUp Fractional Lookup Argument Edge Cases
    print("[4] Testing LogUp Fractional Lookup Argument Edge Cases...")
    table = [1, 2, 3, 4, 5]

    # Empty lookups
    assert engine.prove_and_verify_zk_logup(table, []), "Empty lookups should be valid!"

    # Duplicate valid lookups
    assert engine.prove_and_verify_zk_logup(table, [3, 3, 3, 3, 1, 1, 5, 5]), "Duplicate valid lookups failed!"

    # Out of bounds element
    assert not engine.prove_and_verify_zk_logup(table, [1, 2, 99]), "Out-of-bounds lookup was accepted!"
    print("  -> LogUp argument edge cases PASSED.")

    # Test 5: High-Performance SIMD Batch Throughput Check
    print("[5] Stressing 10,000,000 SIMD batch iterations for throughput check...")
    N = 256
    arr_a = (ctypes.c_float * N)(*[float(i) for i in range(N)])
    arr_b = (ctypes.c_float * N)(*[float(i + 1) for i in range(N)])

    t0 = time.perf_counter()
    res = engine.batch_execute_10_primitives(arr_a, arr_b, 10_000_000)
    t1 = time.perf_counter()

    elapsed = t1 - t0
    total_ops = 10_000_000 * N * 10
    ops_sec = total_ops / elapsed
    print(f"  -> Executed {total_ops:,} primitive ops in {elapsed:.4f}s ({ops_sec:,.2f} ops/sec)")
    assert ops_sec > 400_000_000, f"Throughput below 400M ops/sec: {ops_sec}"
    print("  -> High-Performance SIMD Batch Throughput PASSED.")

    print("\nALL ADVERSARIAL STRESS TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_adversarial_suite()
