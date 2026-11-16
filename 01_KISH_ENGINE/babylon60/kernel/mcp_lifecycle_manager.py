"""
BABYLON-60 Dynamic MCP Lifecycle Manager & Bomb Orchestrator (C5-REAL)
Gestor de Registro, Persistencia, Ejecución Efímera y Autodestrucción de Servidores MCP
"""

import contextlib
import hashlib
from importlib.machinery import ExtensionFileLoader
import importlib.util
import json
import logging
import os
import secrets
import sqlite3
import stat
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, cast

from blake3 import blake3

from .mcp_deductive_engine import McpCandidateContract, McpDeductiveEngine
from .mcp_sandbox_validator import McpSandboxValidator
from .mcp_scaffolder import McpCodeScaffolder, compute_code_hash

logger = logging.getLogger(__name__)
QuarantineDestroyFn = Callable[[str, str, bytes, Optional[bytes]], Tuple[int, int, bytes]]


class McpLifecycleManager:
    """
    Administra el ciclo de vida (Efímero Autodestructible vs Persistente) de los MCPs
    auto-sintetizados en Babylon60. Inscribe los metadatos en causal_gate.db bajo
    INV_C5_WAL_SYNCHRONOUS_FULL.
    """

    def __init__(self, db_path: Optional[str] = None, capability_library: Optional[str | Path] = None) -> None:
        if db_path is None:
            # Resuelve a .cortex/causal_gate.db relativo a la raíz del monorepo
            repo_root = Path(__file__).absolute().parents[3]
            cortex_dir = repo_root / ".cortex"
            cortex_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(cortex_dir / "causal_gate.db")
        else:
            self.db_path = db_path
        self._capability_library = Path(capability_library).absolute() if capability_library is not None else None
        self._last_quarantine_receipt: Optional[Dict[str, Any]] = None
        self._pending_detonation_ctx: Dict[str, Tuple[Optional[bytes], Optional[str]]] = {}
        self._init_db()

    def _resolve_quarantine_destroyer(self) -> Tuple[Optional[QuarantineDestroyFn], str, bool]:
        """Return (destroyer_fn, nonce_seed, mandatory_fail_closed)."""
        from babylon60.mcp.effect_dispatch import active_effect_tx_context

        ctx = active_effect_tx_context()
        if ctx is not None:
            return (ctx[0], ctx[1], True)

        lib_candidate = self._capability_library
        if lib_candidate is None:
            env_lib = os.environ.get("BABYLON60_CAPABILITY_LIBRARY")
            if env_lib:
                lib_candidate = Path(env_lib).absolute()
        if lib_candidate is not None and lib_candidate.is_file():
            loader = ExtensionFileLoader("_babylon60_mcp", str(lib_candidate))
            spec = importlib.util.spec_from_file_location("_babylon60_mcp", lib_candidate, loader=loader)
            if spec is not None and spec.loader is not None:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                fn = getattr(module, "quarantine_and_destroy", None)
                if callable(fn):
                    return (cast(QuarantineDestroyFn, fn), secrets.token_hex(16), True)
        return (None, "", False)

    @staticmethod
    def _read_regular_script_nofollow(script_path: str) -> Tuple[str, bytes]:
        """Read regular script via O_NOFOLLOW descriptor, returning (blake3_hex, sha256_bytes)."""
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(script_path, flags)
        try:
            st = os.fstat(fd)
            if not stat.S_ISREG(st.st_mode):
                raise PermissionError(f"MCP artifact is not a regular file: {script_path}")
            chunks: List[bytes] = []
            for chunk in iter(lambda: os.read(fd, 65536), b""):
                chunks.append(chunk)
            raw = b"".join(chunks)
            return (compute_code_hash(raw.decode("utf-8")), hashlib.sha256(raw).digest())
        finally:
            os.close(fd)

    def _connect(self) -> sqlite3.Connection:
        """Abre conexión SQLite aplicando INV_C5_WAL_SYNCHRONOUS_FULL."""
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=FULL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    @contextlib.contextmanager
    def _write_tx(self) -> Iterator[sqlite3.Connection]:
        """Use a nested SAVEPOINT when sharing the active VerificationGate lock; else BEGIN IMMEDIATE + close."""
        from babylon60.mcp.effect_dispatch import active_gate_sqlite_connection

        shared = active_gate_sqlite_connection()
        if shared is not None and Path(self.db_path).absolute() == Path(shared[1]).absolute():
            conn = cast(sqlite3.Connection, shared[0])
            sp = f"mcp_lc_{secrets.token_hex(6)}"
            prev_factory = conn.row_factory
            conn.execute(f"SAVEPOINT {sp}")
            try:
                yield conn
                conn.execute(f"RELEASE SAVEPOINT {sp}")
            except BaseException:
                conn.execute(f"ROLLBACK TO SAVEPOINT {sp}")
                conn.execute(f"RELEASE SAVEPOINT {sp}")
                raise
            finally:
                conn.row_factory = prev_factory
            return

        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Asegura la existencia de la tabla mcp_registry en causal_gate.db."""
        try:
            with self._write_tx() as conn:
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
        except Exception as e:
            logger.error(f"[McpLifecycleManager] Error inicializando DB: {e}")

    def register_mcp(
        self, candidate: McpCandidateContract, script_path: str, scope: str = "EPH_EPHEMERAL"
    ) -> Dict[str, Any]:
        """Inscribe el MCP en el registro de causal_gate.db."""
        try:
            with self._write_tx() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT script_path FROM mcp_registry WHERE server_name = ?",
                    (candidate.server_name,),
                )
                existing_row = cursor.fetchone()
                if existing_row and existing_row[0] and existing_row[0] != script_path:
                    self._unlink_script(existing_row[0])

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
                logger.info(
                    f"[McpLifecycleManager] MCP '{candidate.server_name}' inscrito correctamente con alcance {scope}."
                )
                return {"status": "SUCCESS", "server_name": candidate.server_name, "scope": scope}
        except Exception as e:
            logger.error(f"[McpLifecycleManager] Error al inscribir MCP: {e}")
            return {"status": "ERROR", "reason": str(e)}

    def list_active_mcps(self) -> List[Dict[str, Any]]:
        """Devuelve la lista de MCPs activos registrados."""
        conn: Optional[sqlite3.Connection] = None
        try:
            conn = self._connect()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM mcp_registry WHERE status = 'ACTIVE'")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"[McpLifecycleManager] Error consultando mcp_registry: {e}")
            return []
        finally:
            if conn is not None:
                conn.close()

    @staticmethod
    def _active_path_absent(script_path: str) -> bool:
        try:
            os.lstat(script_path)
        except FileNotFoundError:
            return True
        except OSError:
            return False
        return False

    def _unlink_script(
        self,
        script_path: str,
        *,
        expected_sha256: Optional[bytes] = None,
        nonce_seed: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Destroy the active script via Rust EffectTx quarantine when available; fail closed if mediated."""
        destroyer, ctx_seed, mandatory = self._resolve_quarantine_destroyer()
        if destroyer is not None:
            p = Path(script_path)
            if not p.exists() and not p.is_symlink():
                return None
            seed = nonce_seed or ctx_seed or secrets.token_hex(16)
            tx_nonce = blake3(f"mcp_effect_tx_v2:{seed}:{p.name}".encode("utf-8")).digest()
            dev, ino, pre_sha256 = destroyer(str(p.parent), p.name, tx_nonce, expected_sha256)
            if not self._active_path_absent(script_path):
                raise OSError(f"MCP source path remains present after EffectTx: {script_path}")
            receipt = {
                "enforced": True,
                "protocol": "RUST_EFFECT_TX_V2",
                "dev": int(dev),
                "ino": int(ino),
                "pre_sha256": bytes(pre_sha256).hex(),
                "tx_nonce": tx_nonce.hex(),
            }
            self._last_quarantine_receipt = receipt
            return receipt

        if mandatory:
            raise PermissionError("FL-MCP-01: EffectTx quarantine unavailable under active mediated dispatch")

        try:
            st = os.lstat(script_path)
            if not stat.S_ISREG(st.st_mode) and not stat.S_ISLNK(st.st_mode):
                raise OSError(f"Unsupported MCP script file mode: {oct(st.st_mode)}")
            os.unlink(script_path)
        except FileNotFoundError:
            pass
        if not self._active_path_absent(script_path):
            raise OSError(f"MCP source path remains present: {script_path}")
        return None

    def detonate_mcp(
        self,
        server_name: str,
        *,
        expected_sha256: Optional[bytes] = None,
        nonce_seed: Optional[str] = None,
    ) -> bool:
        """Purge a registration only after its active script path is quarantined and absent."""
        pending_sha, pending_seed = self._pending_detonation_ctx.pop(server_name, (None, None))
        effective_sha = expected_sha256 if expected_sha256 is not None else pending_sha
        effective_seed = nonce_seed if nonce_seed is not None else pending_seed
        try:
            with self._write_tx() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT script_path FROM mcp_registry WHERE server_name = ?", (server_name,))
                row = cursor.fetchone()
                if row:
                    self._unlink_script(
                        row["script_path"],
                        expected_sha256=effective_sha,
                        nonce_seed=effective_seed,
                    )
                cursor.execute("DELETE FROM mcp_registry WHERE server_name = ?", (server_name,))
                return True
        except Exception as e:
            logger.error(f"[McpLifecycleManager] Error detonando MCP '{server_name}': {e}")
            return False

    def purge_ephemeral_mcps(self) -> int:
        """Purge only ephemeral entries whose active source paths were removed."""
        purged_count = 0
        try:
            with self._write_tx() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM mcp_registry WHERE scope = 'EPH_EPHEMERAL'")
                rows = cursor.fetchall()

                for row in rows:
                    script_path = row["script_path"]
                    try:
                        self._unlink_script(script_path, nonce_seed=f"purge:{row['server_name']}:{row['id']}")
                    except (OSError, PermissionError) as exc:
                        logger.warning(f"No se pudo eliminar {script_path}: {exc}")
                        continue
                    cursor.execute("DELETE FROM mcp_registry WHERE id = ?", (row["id"],))
                    purged_count += cursor.rowcount
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
        3. Calcula el hash BLAKE3 (code_hash) y SHA-256 por descriptor O_NOFOLLOW e inscribe EPH_EPHEMERAL.
        4. Ejecuta el servidor por stdio JSON-RPC 2.0 bajo Seatbelt.
        5. Aísla en cuarentena EffectTx, reverifica (dev, ino, sha256), destruye y purga causal_gate.db.
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
        expected_sha256: Optional[bytes] = None
        self._last_quarantine_receipt = None
        detonated_Attempted = False
        try:
            scaffolder = McpCodeScaffolder(output_dir=target_dir)
            script_path = scaffolder.scaffold_fastmcp_python(contract)
            code_hash, expected_sha256 = self._read_regular_script_nofollow(script_path)

            registration = self.register_mcp(contract, script_path, scope="EPH_EPHEMERAL")
            if registration.get("status") != "SUCCESS":
                raise RuntimeError(f"MCP registration failed: {registration.get('reason')}")

            validator = McpSandboxValidator()
            exec_res = validator.execute_and_detonate_mcp_sync(
                script_path=script_path,
                candidate=contract,
                call_arguments=call_arguments,
                timeout_seconds=timeout_seconds,
                detonate=True,
            )

            detonated_Attempted = True
            self._pending_detonation_ctx[contract.server_name] = (expected_sha256, None)
            registry_purged = self.detonate_mcp(contract.server_name)
            active_path_absent = self._active_path_absent(script_path)
            self_destruct_verified = registry_purged and active_path_absent

            destruct_evidence: Dict[str, Any] = {
                "active_path_absent": active_path_absent,
                "registry_purged": registry_purged,
            }
            if self._last_quarantine_receipt is not None:
                destruct_evidence["effect_tx_quarantine"] = self._last_quarantine_receipt

            return {
                "status": exec_res.get("status", "ERROR") if self_destruct_verified else "ERROR",
                "is_valid": exec_res.get("is_valid", False) if self_destruct_verified else False,
                "server_name": contract.server_name,
                "tool_name": contract.tool_name,
                "code_hash": exec_res.get("code_hash", code_hash),
                "isolation_backend": exec_res.get("isolation_backend"),
                "isolation_evidence": exec_res.get("isolation_evidence"),
                "error_code": exec_res.get("error_code") if self_destruct_verified else "CLEANUP_FAILED",
                "tool_output": exec_res.get("tool_output"),
                "reason": exec_res.get("reason") if self_destruct_verified else "MCP logical cleanup is incomplete",
                "latency_ms": exec_res.get("latency_ms", 0.0),
                "self_destruct_verified": self_destruct_verified,
                "self_destruct_evidence": destruct_evidence,
                "scope": "EPH_EPHEMERAL_DETONATED" if self_destruct_verified else "EPH_EPHEMERAL_PENDING",
            }
        finally:
            if not detonated_Attempted:
                if script_path:
                    try:
                        self._unlink_script(
                            script_path,
                            expected_sha256=expected_sha256,
                            nonce_seed=f"abort:{contract.server_name}",
                        )
                    except Exception:
                        pass
                self.detonate_mcp(contract.server_name)
            self._pending_detonation_ctx.pop(contract.server_name, None)
            if managed_tmp_dir is not None:
                managed_tmp_dir.cleanup()
