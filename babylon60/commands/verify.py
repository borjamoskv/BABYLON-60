import logging
import subprocess

logger = logging.getLogger("babylon60.commands.verify")

def run_verify() -> bool:
    """
    Execute /verify (BFT Ledger Cryptographic Verification).
    Vector: INV_BRIDGE_01 / INV_BRIDGE_04
    
    Verifies SHA-256 hash chains, Lamport ordering, and physical integrity across
    all SQLite ledgers and bridge state.
    """
    logger.info("C5-REAL VERIFY INITIATED: Auditing BFT ledger hash chain...")
    
    bridge_script = "/Users/borjafernandezangulo/30_BABYLON-60/babylon60-ide/bridge/moskv_bridge.py"
    try:
        res = subprocess.run(["python3", bridge_script, "verify"], check=False, capture_output=True, text=True)
        if res.returncode == 0:
            logger.info("Ledger Verification PASSED: Hash chain 100% intact.")
            return True
        else:
            logger.error(f"Ledger Verification FAILED: {res.stderr}")
            return False
    except Exception as e:
        logger.error(f"Friction during verification: {e}")
        return False
