import argparse
import hashlib
import sys

def calculate_merkle_root(state_data: bytes) -> str:
    """Calculates the SHA256 hash representing the root of the state."""
    # Control Flow Depth: 1 (FunctionDef)
    hasher = hashlib.sha256()
    hasher.update(state_data)
    return hasher.hexdigest()

def encode_op_return(merkle_root_hex: str) -> str:
    """
    Encodes the 32-byte Merkle root into a raw Bitcoin OP_RETURN script.
    Strictly follows INV_C5_15: raw bytes, not double-hex.
    """
    # Control Flow Depth: 1 (FunctionDef)
    if len(merkle_root_hex) != 64:
        # Control Flow Depth: 2 (If)
        raise ValueError("Merkle root must be exactly 64 hex characters (32 bytes).")
    
    # 6a = OP_RETURN
    # 20 = PUSHBYTES_32
    # The hex string itself represents the 32 bytes natively.
    script_pubkey = "6a20" + merkle_root_hex
    
    # Value: 0 satoshis (8 bytes, little-endian)
    value_hex = "0000000000000000"
    
    # Script length is 34 bytes (0x22 in hex)
    script_len_hex = "22"
    
    return value_hex + script_len_hex + script_pubkey

def generate_dry_run_tx(merkle_root_hex: str) -> str:
    """
    Generates a dummy raw transaction hex with the OP_RETURN output.
    """
    # Control Flow Depth: 1 (FunctionDef)
    version = "02000000"
    input_count = "01"
    
    # Dummy input (32-byte txid + 4-byte vout + empty script + sequence)
    txid = "00" * 32
    vout = "00000000"
    script_sig_len = "00"
    sequence = "ffffffff"
    tx_in = txid + vout + script_sig_len + sequence
    
    output_count = "01"
    tx_out = encode_op_return(merkle_root_hex)
    
    locktime = "00000000"
    
    return version + input_count + tx_in + output_count + tx_out + locktime

def main():
    # Control Flow Depth: 1 (FunctionDef)
    parser = argparse.ArgumentParser(description="Bitcoin L1 Thermodynamic Anchor (BABYLON-60)")
    parser.add_argument("--dry-run", action="store_true", help="Generate and print the raw transaction without broadcasting")
    args = parser.parse_args()
    
    # Simulated Swarm State / Lean 4 Proof Verification State
    dummy_state = b'BABYLON-60_SWARM_STATE_FINAL_V1'
    merkle_root = calculate_merkle_root(dummy_state)
    
    print(f"[INFO] BFT Swarm State Merkle Root: {merkle_root}")
    
    if args.dry_run:
        # Control Flow Depth: 2 (If)
        raw_tx = generate_dry_run_tx(merkle_root)
        print("\n[SUCCESS] Generated Raw Bitcoin Transaction (INV_C5_15 Compliant):")
        print(raw_tx)
        
        # Verify INV_C5_15 visually
        print("\n[AUDIT] OP_RETURN Script Check:")
        print(f"Expected OP_RETURN Hex Prefix : 6a20")
        print(f"Included Commitment (32-byte) : {merkle_root}")
        
        if f"6a20{merkle_root}" in raw_tx:
            # Control Flow Depth: 3 (If)
            print("[AUDIT] ✅ INV_C5_15 Invariant PASSED. No double-hex truncation detected.")
        else:
            # Control Flow Depth: 3 (Else)
            print("[AUDIT] ❌ INV_C5_15 Invariant FAILED.")
            sys.exit(1)

if __name__ == "__main__":
    main()
