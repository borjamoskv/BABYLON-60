import logging
import re
from pathlib import Path

path = Path("/Users/borjafernandezangulo/30_BABYLON-60/babylon60/audit/ledger.py")
content = path.read_text()

# 1. Replace _CREATE_AUDIT_SQL
new_sql = """_CREATE_AUDIT_SQL = \"\"\"
CREATE TABLE IF NOT EXISTS security_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id TEXT NOT NULL UNIQUE CHECK (length(audit_id) = 64 AND audit_id GLOB '[0-9a-f]*'),
    lamport_t INTEGER NOT NULL CHECK (lamport_t >= 0),
    timestamp TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    actor_role TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    action TEXT NOT NULL,
    resource TEXT NOT NULL,
    status TEXT NOT NULL,
    payload TEXT NOT NULL CHECK (json_valid(payload)),
    prev_hash TEXT NOT NULL CHECK (length(prev_hash) = 64 AND prev_hash GLOB '[0-9a-f]*'),
    signature TEXT NOT NULL,
    external_anchor TEXT,
    UNIQUE (prev_hash),
    UNIQUE (lamport_t, actor_id, action)
) STRICT;

CREATE TRIGGER IF NOT EXISTS ledger_no_update
BEFORE UPDATE ON security_audit_log
BEGIN
    SELECT RAISE(ABORT, 'LEDGER VIOLATION: security_audit_log is append-only (UPDATE blocked)');
END;

CREATE TRIGGER IF NOT EXISTS ledger_no_delete
BEFORE DELETE ON security_audit_log
BEGIN
    SELECT RAISE(ABORT, 'LEDGER VIOLATION: security_audit_log is append-only (DELETE blocked)');
END;

CREATE TRIGGER IF NOT EXISTS ledger_chain_link
BEFORE INSERT ON security_audit_log
WHEN NEW.prev_hash != COALESCE(
    (SELECT audit_id FROM security_audit_log ORDER BY id DESC LIMIT 1),
    '0000000000000000000000000000000000000000000000000000000000000000'
)
BEGIN
    SELECT RAISE(ABORT, 'CHAIN BREAK: prev_hash mismatch');
END;
\"\"\"
"""

content = re.sub(r'_CREATE_AUDIT_SQL\s*=\s*"""[\s\S]*?"""\n', new_sql, content)

# 2. Add LamportClock and WriteSerializer after AsyncFileLock class
classes_to_add = """
from dataclasses import dataclass

class LamportClock:
    \"\"\"Reloj lógico de Lamport thread-safe para asyncio.\"\"\"
    def __init__(self, initial: int = 0):
        self._time: int = initial
        self._lock = asyncio.Lock()

    @property
    def time(self) -> int:
        return self._time

    async def tick(self, incoming: int | None = None) -> int:
        async with self._lock:
            if incoming is not None:
                self._time = max(self._time, incoming) + 1
            else:
                self._time += 1
            return self._time

@dataclass
class WriteOp:
    sql: str
    params: tuple
    future: asyncio.Future

class WriteSerializer:
    \"\"\"Serializa TODAS las escrituras a SQLite a través de un único canal.\"\"\"
    def __init__(self, db: aiosqlite.Connection):
        self._db = db
        self._queue: asyncio.Queue[WriteOp] = asyncio.Queue()
        self._running = False
        self._task = None

    async def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._process_writes())

    async def _process_writes(self):
        while self._running:
            try:
                op = await self._queue.get()
                try:
                    cursor = await self._db.execute(op.sql, op.params)
                    await self._db.commit()
                    op.future.set_result(cursor.lastrowid)
                except Exception as e:  # noqa: BLE001
                    op.future.set_exception(e)
                finally:
                    self._queue.task_done()
            except asyncio.CancelledError:
                break

    async def write(self, sql: str, params: tuple = ()):
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        await self._queue.put(WriteOp(sql, params, future))
        return await future

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
"""

content = re.sub(
    r"(class AsyncFileLock:[\s\S]*?self\.fp = None\n)", r"\1\n" + classes_to_add, content
)

# 3. Update EnterpriseAuditLedger __init__ to instantiate LamportClock and WriteSerializer
init_addition = """
        self._lamport = LamportClock()
        self._writer = WriteSerializer(self._conn)
        # Requerimos arrancar el writer asíncronamente en ensure_table
"""
content = re.sub(r"(self\._lock = asyncio\.Lock\(\)\n)", r"\1" + init_addition, content)

# 4. Update ensure_table to start the writer and drop old table
ensure_table_addition = """
                # [C5-REAL] Purgar tabla vieja si no cumple con el nuevo esquema STRICT
                try:
                    cursor = await self._conn.execute("PRAGMA table_info(security_audit_log)")
                    cols = await cursor.fetchall()
                    col_names = [c[1] for c in cols]
                    if cols and 'lamport_t' not in col_names:
                        logger.warning("[C5-REAL] Detectado esquema C4-SIM (antiguo). Purgando Ledger Génesis...")
                        await self._conn.execute("DROP TABLE security_audit_log")
                except Exception as e:  # noqa: BLE001
                    pass

                await self._writer.start()
"""
content = re.sub(
    r"(await self\._conn\.execute\(_CREATE_AUDIT_SQL\))",
    ensure_table_addition + r"\n                \1",
    content,
)

# 5. Fix ensure_table fetch to use audit_id instead of rowid/prev_hash since order is preserved
fetch_fix = """
                cursor = await self._conn.execute(
                    "SELECT audit_id, prev_hash, signature FROM security_audit_log ORDER BY id DESC LIMIT 1"
                )
                row = await cursor.fetchone()
                if row:
                    audit_id_db, prev_hash, sig = row[0], row[1], row[2]
"""
content = re.sub(
    r'cursor = await self\._conn\.execute\(\n\s*"SELECT prev_hash, signature FROM security_audit_log ORDER BY rowid DESC LIMIT 1"\n\s*\)\n\s*row = await cursor\.fetchone\(\)\n\s*if row:\n\s*prev_hash, sig = row\[0\], row\[1\]',
    fetch_fix,
    content,
)

path.write_text(content)
logging.getLogger(__name__).info("Transformation successful")
