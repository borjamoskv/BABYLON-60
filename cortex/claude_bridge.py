# C5-REAL EXERGY CERTIFIED
"""
CORTEX CLAUDE CODE BRIDGE (C5-REAL)
Puente Causal e Isomórfico entre MOSKV-1 APEX (Antigravity) y Claude Code CLI.
Soporta Consenso BFT Multi-Kernel (Ω1b), Fallback por Cuota (Ω27) e IPC Estructurado (Ω45).
"""

import json
import os
import subprocess
from typing import Any, Dict, Optional


class ClaudeCodeBridge:
    """Transductor C5-REAL para orquestación síncrona/asíncrona con Claude Code CLI."""

    def __init__(self, binary_path: Optional[str] = None) -> None:
        if binary_path is not None:
            self.binary_path = binary_path
        else:
            default_path = "/opt/homebrew/bin/claude"
            self.binary_path = default_path if os.path.exists(default_path) else "claude"

    def is_available(self) -> bool:
        """Verifica la presencia física del ejecutable Claude Code."""
        try:
            res = subprocess.run(
                [self.binary_path, "--version"],
                capture_output=True,
                text=True,
                check=False,
            )
            return res.returncode == 0
        except OSError:
            return False

    def query(
        self,
        prompt: str,
        cwd: Optional[str] = None,
        timeout: int = 60,
        env_extra: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Ejecuta una consulta sobre Claude Code y transduce el payload a una estructura BFT.

        Implementa Ω27 (Subagent Rate-Limit/Quota Fallback) y Ω45 (IPC Buffering).
        """
        env = os.environ.copy()
        if env_extra:
            env.update(env_extra)

        target_cwd = cwd or os.getcwd()

        try:
            proc = subprocess.run(
                [self.binary_path, "-p", prompt, "--output-format", "json"],
                cwd=target_cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                check=False,
            )

            stdout = proc.stdout.strip()
            stderr = proc.stderr.strip()

            # Intentar parsear el JSON estructurado de Claude Code
            try:
                data = json.loads(stdout)
                if data.get("is_error") and "Credit balance" in data.get("result", ""):
                    return {
                        "status": "QUOTA_EXHAUSTED",
                        "kernel": "claude-code",
                        "error": "Credit balance too low",
                        "raw_response": data,
                        "fallback_required": True,
                    }
                return {
                    "status": "SUCCESS" if proc.returncode == 0 else "ERROR",
                    "kernel": "claude-code",
                    "result": data.get("result", stdout),
                    "raw_response": data,
                    "fallback_required": False,
                }
            except json.JSONDecodeError:
                if "Credit balance is too low" in stderr or "Credit balance is too low" in stdout:
                    return {
                        "status": "QUOTA_EXHAUSTED",
                        "kernel": "claude-code",
                        "error": "Credit balance too low",
                        "fallback_required": True,
                    }
                return {
                    "status": "RAW_TEXT" if proc.returncode == 0 else "ERROR",
                    "kernel": "claude-code",
                    "result": stdout or stderr,
                    "fallback_required": False,
                }

        except subprocess.TimeoutExpired:
            return {
                "status": "TIMEOUT",
                "kernel": "claude-code",
                "error": f"Execution timed out after {timeout}s",
                "fallback_required": True,
            }
        except OSError as e:
            return {
                "status": "EXEC_ERROR",
                "kernel": "claude-code",
                "error": str(e),
                "fallback_required": True,
            }


def main() -> None:
    bridge = ClaudeCodeBridge()
    available = bridge.is_available()
    print(f"[CLAUDE-BRIDGE C5-REAL] Available: {available}")
    if available:
        res = bridge.query("Ping test - respond status ok")
        print(f"[CLAUDE-BRIDGE RESULT] Status: {res.get('status')}")
        print(f"[CLAUDE-BRIDGE DETAILS] {res}")


if __name__ == "__main__":
    main()
