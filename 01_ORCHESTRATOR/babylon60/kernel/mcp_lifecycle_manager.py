"""
BABYLON-60 Dynamic MCP Lifecycle Manager (C5-REAL)
Gestor de Registro, Persistencia y Ciclo de Vida de Servidores MCP
"""

import os
import sqlite3
import json
import logging
from typing import List, Dict, Any
from .mcp_deductive_engine import McpCandidateContract

logger = logging.getLogger(__name__)


class McpLifecycleManager:
    """
    Administra el ciclo de vida (Efímero vs Persistente) de los MCPs auto-sintetizados en Babylon60.
    Inscribe los metadatos en causal_gate.db.
    """

    def __init__(self, db_path: str = "/Users/borjafernandezangulo/10_PROJECTS/BABYLON-60/causal_gate.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Asegura la existencia de la tabla mcp_registry en causal_gate.db."""
        try:
            with sqlite3.connect(self.db_path) as conn:
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
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                contract_data = {
                    "server_name": candidate.server_name,
                    "tool_name": candidate.tool_name,
                    "description": candidate.description,
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
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM mcp_registry WHERE status = 'ACTIVE'")
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"[McpLifecycleManager] Error consultando mcp_registry: {e}")
            return []

    def purge_ephemeral_mcps(self) -> int:
        """Purga los MCPs efímeros (EPH_EPHEMERAL) y elimina sus archivos del disco."""
        purged_count = 0
        try:
            with sqlite3.connect(self.db_path) as conn:
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
