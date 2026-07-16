"""
C5-REAL: UNIVERSAL TRI-LINGUAL IPC TRANSDUCER & WAL SINGLE-WRITER BARRIER
=========================================================================
SYS_ID: MOSKV-1 APEX ULTRATHINK P0 (Universal IPC Mesh)
REALITY_LEVEL: C5-REAL (Asynchronous UNIX Socket / Single Physical WAL Writer)

Implementa la Ley Ω13 (`SERIALIZACIÓN DE ESCRITURA`) y Ω9 (`IGNICIÓN DETERMINISTA`)
junto con los invariantes de base de datos (`INV_BFT_02`, `INV_BFT_03`, `INV_BFT_04`).
Abre un UNIX Domain Socket asíncrono para recibir flujos de consenso BFT concurrentes
desde microkernel Go (`swarm_10k`), núcleo Rust (`strike_rs`) y agentes Python,
encolando cada transacción en `asyncio.Queue` con un único escritor físico a SQLite WAL.
"""

import asyncio
import sqlite3
import json
import uuid
import time
import os
import ctypes
from typing import Dict, Any, Optional

IPC_SOCKET_PATH = os.environ.get("CORTEX_IPC_SOCKET", "/tmp/cortex_ipc_mesh.sock")
DB_PATH = os.environ.get("CORTEX_IPC_DB", os.path.join(os.path.dirname(__file__), "nexus_anchors.db"))
IDEMPOTENCY_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8") # DNS namespace UUID

# FFI Reloj Sexagesimal Mach-O
try:
    _dylib_path = os.path.join(os.path.dirname(__file__), "cortex_base60_clock.dylib")
    if os.path.exists(_dylib_path):
        _clock_lib = ctypes.CDLL(_dylib_path)
        _clock_lib.cortex_get_base60_ticks.restype = ctypes.c_uint64
        def get_base60_ticks() -> int:
            return int(_clock_lib.cortex_get_base60_ticks())
    else:
        def get_base60_ticks() -> int:
            return int(time.time() * 60)
except Exception:
    def get_base60_ticks() -> int:
        return int(time.time() * 60)

class UniversalIPCTransducer:
    """Orquestador asíncrono e interfaz de barrera para el Master Ledger WAL."""
    def __init__(self, socket_path: str = IPC_SOCKET_PATH, db_path: str = DB_PATH):
        self.socket_path = socket_path
        self.db_path = db_path
        self.queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=50000)
        self.server: Optional[asyncio.AbstractServer] = None
        self.is_running = False
        self.transactions_written = 0
        self.idempotency_cache: set[str] = set()

    def _init_wal_schema(self, conn: sqlite3.Connection) -> None:
        """Inicializa el esquema WAL con restricciones de idempotencia y CORTEX-TAINT."""
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ipc_mesh_ledger (
                idempotency_key TEXT PRIMARY KEY,
                source_lang TEXT NOT NULL,
                primitive_id TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                merkle_hash TEXT NOT NULL,
                cortex_taint_sig TEXT NOT NULL,
                sexagesimal_tick INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

    async def _wal_writer_loop(self) -> None:
        """Bucle consumidor único que toma transacciones de la cola y muta el disco atómicamente."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        self._init_wal_schema(conn)

        try:
            while self.is_running or not self.queue.empty():
                try:
                    # Esperamos hasta 0.1s por nuevas transacciones en la cola
                    payload = await asyncio.wait_for(self.queue.get(), timeout=0.1)
                except asyncio.TimeoutError:
                    continue

                # Procesamiento e inserción WAL (INV_BFT_03 & INV_BFT_04)
                src = str(payload.get("source_lang", "python"))
                prim_id = str(payload.get("primitive_id", "P_UNKNOWN"))
                data_dict = payload.get("data", {})
                data_json = json.dumps(data_dict)
                m_hash = str(payload.get("merkle_hash", ""))

                # Generación de Idempotency Key UUID V5 biyectiva
                raw_idemp = f"{src}:{prim_id}:{m_hash}"
                idemp_key = str(uuid.uuid5(IDEMPOTENCY_NAMESPACE, raw_idemp))

                # Falsación de Idempotencia en memoria/cache antes de tocar disco
                if idemp_key in self.idempotency_cache:
                    self.queue.task_done()
                    continue

                ticks = get_base60_ticks()
                taint_sig = f"[CORTEX-TAINT:borjamoskv:ipc_mesh:{ticks}:{idemp_key[:8]}]"

                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO ipc_mesh_ledger (
                            idempotency_key, source_lang, primitive_id, payload_json, merkle_hash, cortex_taint_sig, sexagesimal_tick
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (idemp_key, src, prim_id, data_json, m_hash, taint_sig, ticks))
                    conn.commit()
                    self.idempotency_cache.add(idemp_key)
                    self.transactions_written += 1
                except sqlite3.Error as e:
                    print(f"[C5-REAL: IPC WAL ERROR] Sensor Drift (Ω2): {e}")
                finally:
                    self.queue.task_done()
        finally:
            conn.close()

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Manejador de cliente UNIX para conexiones entrantes desde Go/Rust/Python."""
        try:
            data = await reader.readline()
            if not data:
                writer.close()
                await writer.wait_closed()
                return

            message = json.loads(data.decode("utf-8").strip())
            await self.queue.put(message)

            response = json.dumps({"status": "ACK_QUEUED", "sexagesimal_tick": get_base60_ticks()}) + "\n"
            writer.write(response.encode("utf-8"))
            await writer.drain()
        except Exception as e:
            err_resp = json.dumps({"status": "ERR_REJECTED", "reason": str(e)}) + "\n"
            writer.write(err_resp.encode("utf-8"))
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    async def start(self) -> None:
        """Enciende síncronamente el socket UNIX e inicia el daemon único de escritura."""
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

        self.is_running = True
        self.server = await asyncio.start_unix_server(self._handle_client, path=self.socket_path)
        os.chmod(self.socket_path, 0o777)
        print(f"[C5-REAL] Ignición del Transductor IPC en UNIX Socket: {self.socket_path}")

        # Lanzar el bucle escritor físico en segundo plano (coroutine)
        asyncio.create_task(self._wal_writer_loop())

    async def stop(self) -> None:
        """Detiene el servidor asíncrono y vacía la cola en WAL antes de apagar."""
        self.is_running = False
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        # Esperar vaciado de cola
        await self.queue.join()
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)
        print(f"[C5-REAL] Transductor IPC detenido. Total escrituras WAL transaccionadas: {self.transactions_written}")

async def _main_demo() -> None:
    transducer = UniversalIPCTransducer()
    await transducer.start()
    # Simular una inyección rápida desde el propio loop para verificar
    await transducer.queue.put({
        "source_lang": "python_demo",
        "primitive_id": "P_0001",
        "data": {"agent_id": "Agent_Root_01", "action": "INITIALIZE_BFT_QUORUM"},
        "merkle_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    })
    await asyncio.sleep(0.5)
    await transducer.stop()

if __name__ == "__main__":
    asyncio.run(_main_demo())
