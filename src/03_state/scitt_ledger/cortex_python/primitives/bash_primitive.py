# C5-REAL EXERGY CERTIFIED
import subprocess
import sys
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple

# [ULTRATHINK V3] Dynamic Out-Of-Tree Import for BFT Kernel Verification
sys.path.insert(0, "/tmp/cortex_exergy_build")
try:
    import cortex_guard_core
except ImportError:
    sys.stderr.write("\n[FATAL] cortex_guard_core C-Extension not built in /tmp/. Run 'make build-guard'. HALTING LEDGER.\n")
    sys.stderr.flush()
    os.abort()

@dataclass(frozen=True)
class CommandResult:
    """[C5-REAL: Ω33 Domain Primitive] Estructura inmutable del resultado de Kernel."""
    stdout: str
    stderr: str
    returncode: int

    @property
    def success(self) -> bool:
        return self.returncode == 0

@dataclass(frozen=True)
class BashCommand:
    """
    [C5-REAL: Ω33 Domain Primitive]
    Encapsula de forma estricta un comando Bash. Erradica el 'State Spaghetti'
    (uso de strings crudos).
    Ejecuta validación física O(1) en T=0: Si el binario no existe en el sistema,
    la instanciación de este objeto provocará un volcado de memoria inmediato (SIGABRT).
    """
    binary: str
    args: Tuple[str, ...] = field(default_factory=tuple)
    cwd: Path = field(default_factory=lambda: Path(os.getcwd()))
    check: bool = True
    timeout: float | None = None

    def __post_init__(self):
        if self.check:
            # O(1) Kernel-Level Physical Validation
            # Bypasses Python exception layers. Throws SIGABRT if tool missing.
            cortex_guard_core.verify_dependencies([self.binary])

    def execute(self) -> CommandResult:
        """
        Ejecuta el comando inmutable retornando estrictamente el CommandResult limpio.
        Cualquier error (return code != 0) eleva una excepción estructurada si check=True.
        """
        full_command = [self.binary] + list(self.args)

        try:
            result = subprocess.run(
                full_command,
                cwd=str(self.cwd),
                check=self.check,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            return CommandResult(
                stdout=result.stdout.strip() if result.stdout else "",
                stderr=result.stderr.strip() if result.stderr else "",
                returncode=result.returncode
            )
        except subprocess.CalledProcessError as e:
            msg = f"[FATAL] BashCommand Execution Failed: {' '.join(full_command)}\n"
            msg += f"STDERR: {e.stderr.strip() if e.stderr else 'None'}"
            raise RuntimeError(msg) from e
        except subprocess.TimeoutExpired as e:
            msg = f"[FATAL] BashCommand Timeout: {' '.join(full_command)}\n"
            raise RuntimeError(msg) from e
