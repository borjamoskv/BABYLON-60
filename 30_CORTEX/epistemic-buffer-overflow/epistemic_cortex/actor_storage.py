# [C5-REAL] Actor-Model Batch Storage Controller
# Author: borjamoskv
# Estilo: Sin comillas simples (exclusivo comillas dobles)

from __future__ import annotations
import sqlite3
import queue
import threading
import time
from dataclasses import dataclass

@dataclass
class StoreRequest:
    tenant_id: str
    content: str
    response_queue: queue.Queue[int]  # Used to return the generated fact_id

class DatabaseActor(threading.Thread):
    """
    Central database actor managing all writes.
    Accepts write requests via thread-safe queue and aggregates them in batches.
    """
    def __init__(self, db_path: str, batch_interval_ms: int = 1000) -> None:
        super().__init__()
        self.db_path = db_path
        self.batch_interval = batch_interval_ms / 1000.0
        self.mailbox: queue.Queue[StoreRequest] = queue.Queue()
        self.running = True
        self._init_shared_db()

    def _init_shared_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS facts ("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  tenant_id TEXT NOT NULL,"
            "  content TEXT NOT NULL"
            ")"
        )
        conn.commit()
        conn.close()

    def request_write(self, tenant_id: str, content: str) -> int:
        response: queue.Queue[int] = queue.Queue()
        req = StoreRequest(tenant_id=tenant_id, content=content, response_queue=response)
        self.mailbox.put(req)
        # Block until the batch thread processes the request
        return response.get()

    def shutdown(self) -> None:
        self.running = False
        self.join()

    def run(self) -> None:
        while self.running or not self.mailbox.empty():
            batch: list[StoreRequest] = []
            start_time = time.time()

            # Collect requests up to batch interval
            while time.time() - start_time < self.batch_interval:
                try:
                    # Non-blocking pull
                    req = self.mailbox.get(timeout=0.05)
                    batch.append(req)
                except queue.Empty:
                    if not self.running:
                        break

            if batch:
                self._process_batch(batch)

    def _process_batch(self, batch: list[StoreRequest]) -> None:
        # Single-writer transaction over the aggregated batch
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            for req in batch:
                cursor.execute(
                    "INSERT INTO facts (tenant_id, content) VALUES (?, ?)",
                    (req.tenant_id, req.content)
                )
                fact_id = cursor.lastrowid or 0
                req.response_queue.put(fact_id)
            conn.commit()
        except Exception as err:
            conn.rollback()
            # In case of database failure, return 0 to release blocking queues
            for req in batch:
                req.response_queue.put(0)
        finally:
            conn.close()
