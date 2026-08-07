# C5-REAL EXERGY CERTIFIED
import sqlite3
import time
import random

class BFTConnection:
    """Wrapper C5-REAL para SQLite con Exponential Backoff and Jitter."""
    def __init__(self, db_path, max_retries=15, base_delay=0.02, timeout=0.0):
        self.db_path = db_path
        self.max_retries = max_retries
        self.base_delay = base_delay
        # Conexión nativa inicial (timeout=0.0 fuerza Fail-Fast para el Backoff)
        self.conn = sqlite3.connect(db_path, timeout=timeout)

    def _execute_with_backoff(self, operation, *args, **kwargs):
        retries = 0
        while True:
            try:
                return operation(*args, **kwargs)
            except sqlite3.OperationalError as e:
                err_msg = str(e).lower()
                if "locked" in err_msg or "busy" in err_msg:
                    if retries >= self.max_retries:
                        raise e
                    # Dispersion termodinámica del I/O (Exponential Backoff + Jitter)
                    delay = self.base_delay * (2 ** retries)
                    jitter = random.uniform(0, delay * 0.1)
                    time.sleep(delay + jitter)
                    retries += 1
                else:
                    raise e

    def execute(self, sql, parameters=()):
        return self._execute_with_backoff(self.conn.execute, sql, parameters)

    def executemany(self, sql, parameters_seq):
        return self._execute_with_backoff(self.conn.executemany, sql, parameters_seq)

    def commit(self):
        return self._execute_with_backoff(self.conn.commit)

    def close(self):
        self.conn.close()

def connect(db_path, max_retries=15, base_delay=0.01, timeout=0.0):
    return BFTConnection(db_path, max_retries, base_delay, timeout)
