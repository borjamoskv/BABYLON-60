# C5-REAL EXERGY CERTIFIED
import sys
import os

# [ULTRATHINK V3] Dynamic Out-Of-Tree Import (Ω1 / Ω24)
sys.path.insert(0, "/tmp/cortex_exergy_build")

try:
    import cortex_guard_core
except ImportError:
    sys.stderr.write("\n[FATAL] cortex_guard_core C-Extension not built in /tmp/. Run 'make build-guard'. HALTING LEDGER.\n")
    sys.stderr.flush()
    os.abort()

def verify_dependencies(required_tools: list[str]) -> None:
    """
    [CORTEX-TAINT:VERIFY]
    ULTRATHINK Zero-Tolerance Dependency Vanguard.
    Verifies the existence of POSIX/binary tools at T=0 via kernel access().
    """
    cortex_guard_core.verify_dependencies(required_tools)
