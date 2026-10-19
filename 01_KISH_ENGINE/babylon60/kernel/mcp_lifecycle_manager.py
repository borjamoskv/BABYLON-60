"""
BABYLON-60 Dynamic MCP Lifecycle Manager & Bomb Orchestrator (C5-REAL)
Gestor de Registro, Persistencia, Ejecución Efímera y Autodestrucción de Servidores MCP
"""

import json
import logging
import os
import sqlite3
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from .mcp_deductive_engine import McpCandidateContract, McpDeductiveEngine
from .mcp_sandbox_validator import McpSandboxValidator
from .mcp_scaffolder import McpCodeScaffolder, compute_code_hash

logger = logging.getLogger(__name__)


class McpLifecycleManager:
    """
    Administra el ciclo de vida (Efímero Autodestructible vs Persistente) de los MCPs
    auto-sintetizados en Babylon60. Inscribe los metadatos en causal_gate.db bajo
    INV_C5_WAL_SYNCHRONOUS_FULL.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            # Resuelve a .cortex/causal_gate.db relativo a la raíz del monorepo
            repo_root = Path(__file__).resolve().parents[3]
            cortex_dir = repo_root / ".cortex"
            cortex_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(cortex_dir / "causal_gate.db")
        else:
            self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        """Abre conexión SQLite aplicando INV_C5_WAL_SYNCHRONOUS_FULL."""
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=FULL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    def _init_db(self) -> None:
        """Asegura la existencia de la tabla mcp_registry en causal_gate.db."""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS mcp_registry (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        server_name TEXT UNIQUE NOT NULL,
                        tool_name TEXT NOT NULL,
                        script_path TEXT NOT NULL,
                        scope TEXT CHECK(scope IN ('EPH_EPHEMERAL', 'PERM_SOVEREIGN')) DEFAULT 'EPH_EPHEMERAL',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'ACTIVE',
                        contract_json TEXT NOT NULL
                    )
                """
                )
                conn.commit()
        except Exception as e:
            logger.error(f"[McpLifecycleManager] Error inicializando DB: {e}")

    def register_mcp(
        self, candidate: McpCandidateContract, script_path: str, scope: str = "EPH_EPHEMERAL"
    ) -> Dict[str, Any]:
        """Inscribe el MCP en el registro de causal_gate.db."""
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                contract_data = {
                    "server_name": candidate.server_name,
                    "tool_name": candidate.tool_name,
                    "description": candidate.description,
                    "max_invocations": candidate.max_invocations,
                    "parameters": [
                        {"name": p.name, "type": p.param_type, "required": p.required} for p in candidate.parameters
                    ],
                }

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO mcp_registry (server_name, tool_name, script_path, scope, status, contract_json)
                    VALUES (?, ?, ?, ?, 'ACTIVE', ?)
                """,
                    (candidate.server_name, candidate.tool_name, script_path, scope, json.dumps(contract_data)),
                )
                conn.commit()
                logger.info(
                    f"[McpLifecycleManager] MCP '{candidate.server_name}' inscrito correctamente con alcance {scope}."
                )
                return {"status": "SUCCESS", "server_name": candidate.server_name, "scope": scope}
        except Exception as e:
            logger.error(f"[McpLifecycleManager] Error al inscribir MCP: {e}")
            return {"status": "ERROR", "reason": str(e)}

    def list_active_mcps(self) -> List[Dict[str, Any]]:
        """Devuelve la lista de MCPs activos registrados."""
        try:
            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM mcp_registry WHERE status = 'ACTIVE'")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"[McpLifecycleManager] Error consultando mcp_registry: {e}")
            return []

    def detonate_mcp(self, server_name: str) -> bool:
        """Elimina físicamente el script y purga el registro de un MCP específico (Cero Huella)."""
        try:
            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT script_path FROM mcp_registry WHERE server_name = ?", (server_name,))
                row = cursor.fetchone()
                if row:
                    script_path = row["script_path"]
                    if os.path.exists(script_path):
                        try:
                            os.unlink(script_path)
                        except Exception as fe:
                            logger.warning(f"No se pudo eliminar {script_path}: {fe}")
                cursor.execute("DELETE FROM mcp_registry WHERE server_name = ?", (server_name,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"[McpLifecycleManager] Error detonando MCP '{server_name}': {e}")
            return False

    def purge_ephemeral_mcps(self) -> int:
        """Purga los MCPs efímeros (EPH_EPHEMERAL) y elimina sus archivos del disco."""
        purged_count = 0
        try:
            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM mcp_registry WHERE scope = 'EPH_EPHEMERAL' AND status = 'ACTIVE'")
                rows = cursor.fetchall()

                for row in rows:
                    script_path = row["script_path"]
                    if os.path.exists(script_path):
                        try:
                            os.remove(script_path)
                            logger.info(f"[McpLifecycleManager] Archivo efímero purgado: {script_path}")
                        except Exception as fe:
                            logger.warning(f"No se pudo eliminar {script_path}: {fe}")

                cursor.execute("DELETE FROM mcp_registry WHERE scope = 'EPH_EPHEMERAL'")
                purged_count = cursor.rowcount
                conn.commit()
                logger.info(f"[McpLifecycleManager] Purga completada. {purged_count} MCPs efímeros eliminados.")
        except Exception as e:
            logger.error(f"[McpLifecycleManager] Error durante la purga de anergía: {e}")

        return purged_count

    def synthesize_and_detonate_bomb(
        self,
        domain_name: str,
        implementation_body: str,
        call_arguments: Dict[str, Any],
        description: Optional[str] = None,
        timeout_seconds: float = 5.0,
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Orquesta un «MCP Bomba» de principio a fin en un solo paso:
        1. Deduce el contrato desde domain_name + call_arguments y lo valida con Z3Firewall (Ring-0).
        2. Valida el AST de implementation_body y sintetiza el servidor MCP en un directorio efímero.
        3. Calcula el hash BLAKE3 (code_hash) del código sintetizado e inscribe la entrada EPH_EPHEMERAL.
        4. Ejecuta el servidor por stdio JSON-RPC 2.0 (initialize -> tools/list -> tools/call).
        5. Verifica la autodestrucción física del script (unlink) y purga el registro en causal_gate.db.
        """
        engine = McpDeductiveEngine()
        contract = engine.deduce_contract(
            domain_name=domain_name,
            sample_calls=[{"args": call_arguments}],
            implementation_body=implementation_body,
            custom_description=description,
            max_invocations=1,
        )

        # Directorio efímero dedicado si no se especifica output_dir
        managed_tmp_dir: Optional[tempfile.TemporaryDirectory[str]] = None
        if output_dir is None:
            managed_tmp_dir = tempfile.TemporaryDirectory(prefix="babylon60_mcp_bomb_")
            target_dir = managed_tmp_dir.name
        else:
            target_dir = output_dir

        script_path = ""
        try:
            scaffolder = McpCodeScaffolder(output_dir=target_dir)
            script_path = scaffolder.scaffold_fastmcp_python(contract)
            with open(script_path, "r", encoding="utf-8") as f:
                code_hash = compute_code_hash(f.read())

            self.register_mcp(contract, script_path, scope="EPH_EPHEMERAL")

            validator = McpSandboxValidator()
            exec_res = validator.execute_and_detonate_mcp_sync(
                script_path=script_path,
                candidate=contract,
                call_arguments=call_arguments,
                timeout_seconds=timeout_seconds,
                detonate=True,
            )

            self.detonate_mcp(contract.server_name)
            self_destruct_verified = not os.path.exists(script_path)

            return {
                "status": exec_res.get("status", "ERROR"),
                "is_valid": exec_res.get("is_valid", False),
                "server_name": contract.server_name,
                "tool_name": contract.tool_name,
                "code_hash": code_hash,
                "tool_output": exec_res.get("tool_output"),
                "reason": exec_res.get("reason"),
                "latency_ms": exec_res.get("latency_ms", 0.0),
                "self_destruct_verified": self_destruct_verified,
                "scope": "EPH_EPHEMERAL_DETONATED",
            }
        finally:
            if script_path and os.path.exists(script_path):
                try:
                    os.unlink(script_path)
                except Exception:
                    pass
            self.detonate_mcp(contract.server_name)
            if managed_tmp_dir is not None:
                managed_tmp_dir.cleanup()
