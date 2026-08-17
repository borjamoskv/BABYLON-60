#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# c5_simulations/testnet_apoptosis_notary.py — EVM Notary Integration Test
# Evaluates ApoptosisAnchor.sol on Anvil / Base Sepolia testnets
# Author: Borja Moskv (borjamoskv)
# ============================================================================

import argparse
import hashlib
import json
import os
import subprocess
import sys


def compute_genesis_hash(label: str = "GENESIS_C5_REAL_V4") -> str:
    """Compute 0x-prefixed bytes32 hash of genesis label."""
    return "0x" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def run_cast(args: list[str]) -> str:
    """Run a cast command and return stdout string."""
    cmd = ["cast"] + args
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"cast error ({res.returncode}): {res.stderr.strip()}")
    return res.stdout.strip()


def run_dry_run_simulation() -> None:
    """Run a local Forge script simulation of ApoptosisAnchor deployment."""
    print("🔨 [DRY-RUN] Executing Forge deployment script simulation...")
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    anvil_dir = os.path.join(repo_root, "experiments", "anvil_yung")
    
    cmd = ["forge", "script", "script/DeployApoptosisAnchor.s.sol:DeployApoptosisAnchorScript", "--sig", "run()"]
    res = subprocess.run(cmd, cwd=anvil_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"❌ Forge simulation failed:\n{res.stderr}")
        sys.exit(1)
    
    print("✅ Forge simulation completed successfully!")
    for line in res.stdout.splitlines():
        if "Gas used:" in line or "Return ==" in line or "address" in line:
            print(f"   {line}")


def main():
    parser = argparse.ArgumentParser(description="BABYLON-60 Testnet Apoptosis Notary Simulator")
    parser.add_argument("--dry-run", action="store_true", help="Run offline Forge simulation without RPC broadcast")
    parser.add_argument("--rpc-url", type=str, default="http://127.0.0.1:8545", help="RPC URL for Anvil or Testnet L2")
    parser.add_argument("--contract-address", type=str, help="Deployed ApoptosisAnchor contract address")
    parser.add_argument("--private-key", type=str, help="Private key for authority account")

    args = parser.parse_args()

    if args.dry_run or not args.contract_address:
        run_dry_run_simulation()
        return

    print(f"🌐 Connecting to RPC: {args.rpc_url}")
    print(f"⚓ Querying ApoptosisAnchor at: {args.contract_address}")

    try:
        current_head = run_cast(["call", args.contract_address, "currentHead()(bytes32)", "--rpc-url", args.rpc_url])
        latent_steps = run_cast(["call", args.contract_address, "latentSteps()(uint256)", "--rpc-url", args.rpc_url])
        print(f"   Current Head: {current_head}")
        print(f"   Latent Steps: {latent_steps}")
        print("✅ Query succeeded! Contract is alive and responding on RPC.")
    except Exception as e:
        print(f"❌ RPC Query failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
