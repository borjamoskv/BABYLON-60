# C5-REAL EXERGY CERTIFIED
"""Cortex Ontological Lexicon Transducer (cortex/lexicon.py)

Executable transducer for loading, verifying, programmatically querying,
and cryptographically persisting the Sovereign Lexicon / Glosario (glosario.md)
and Kernel Invariants (Ω0 - Ω187) via SQLite WAL, Single-Writer Actor,
Git Sentinel (L3 Witness), and Fernet Vault (C5ENC:).
"""

import os
import re
import math
import uuid
import json
import hashlib
import asyncio
import sqlite3
import subprocess
from cryptography.fernet import Fernet
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, TypedDict, Union

from .bft_swarm import BFTNode

# --- CONSTANTES ONTOLÓGICAS DE ALTA VELOCIDAD ---
RE_GLOSARIO = re.compile(
    r"\*\*(?P<term>[^\*\(\n]+)(?:\s*\((?P<symbol>[^\)]+)\))?\*\*\nTipo:\s*(?P<category>[^\n]+)\n(?P<desc>.*?)(?=\n\*\*|\n---|\Z)",
    re.DOTALL
)
RE_INVARIANTES = re.compile(r"-\s*\*\*(?P<id>Ω\d+)\s*·\s*(?P<title>[^\*\:]+)\:\*\*\s*(?P<desc>[^\n]+)")
RE_TOKENIZER = re.compile(r"\w+")

class C5EnrichedEnvelope(TypedDict):
    seq: int
    event_id: str
    stream: str
    payload_json: str
    cortex_taint: str
    lamport_t: int
    prev_hash: str
    entry_hash: str
    created_at: str

# --- CAPA DE SEGURIDAD: VAULT FERNET ---
class CortexVault:
    """Gestiona el cifrado/descifrado de payloads bajo el estándar C5ENC: de BABYLON-60."""
    __slots__ = ("cipher", "active")

    def __init__(self):
        # Lee la clave de entorno CORTEX_VAULT_KEY; si no existe, opera en texto plano
        key = os.getenv("CORTEX_VAULT_KEY")
        if key:
            self.cipher = Fernet(key.encode('utf-8'))
            self.active = True
        else:
            self.cipher = None
            self.active = False

    def shield_payload(self, plain_json: str) -> str:
        """Cifra el payload si la bóveda está activa, inyectando el prefijo simétrico."""
        if not self.active or not self.cipher:
            return plain_json
        encrypted_bytes = self.cipher.encrypt(plain_json.encode('utf-8'))
        return f"C5ENC:{encrypted_bytes.decode('utf-8')}"

    def unshield_payload(self, payload_str: str) -> str:
        """Detecta el testigo C5ENC: y descifra el contenido en caliente."""
        if payload_str.startswith("C5ENC:") and self.cipher:
            token = payload_str.split("C5ENC:")[1]
            return self.cipher.decrypt(token.encode('utf-8')).decode('utf-8')
        return payload_str

# --- TESTIGO EXTERNO: GIT SENTINEL ---
class GitSentinel:
    """Automatiza el no-repudio atómico mediante commits firmados localmente (Nivel L3)."""
    __slots__ = ("repo_path", "lock", "push_enabled")

    def __init__(self, repo_path: Path, push_enabled: bool = False):
        self.repo_path = repo_path
        self.lock = asyncio.Lock()
        self.push_enabled = push_enabled

    async def commit_entry(self, seq: int, entry_hash: str, taint: str) -> bool:
        """Captura el rastro causal y el hash SHA3 dentro del árbol de Git de forma asíncrona."""
        async with self.lock:
            try:
                msg = f"CORTEX_L3_WITNESS [seq={seq}] | Hash: {entry_hash} | Taint: {taint}"

                # Ejecuciones en subprocesos asíncronos para evitar el bloqueo del bucle de eventos
                p1 = await asyncio.create_subprocess_exec(
                    "git", "-C", str(self.repo_path), "add", ".",
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                await p1.wait()

                p2 = await asyncio.create_subprocess_exec(
                    "git", "-C", str(self.repo_path), "commit", "-m", msg,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
                await p2.wait()
                if self.push_enabled:
                    push_proc = await asyncio.create_subprocess_exec(
                        "git", "-C", str(self.repo_path), "push", "origin", "master",
                        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
                    )
                    await push_proc.wait()
                return p2.returncode == 0
            except Exception:
                return False

    async def freeze_purged_leader_state(self, purged_node_id: str, last_stable_seq: int, terminal_hash: str):
        """
        [L3 SENTINEL] Amputa el árbol de ejecución del nodo degradado.
        Sella el fin de la vista en el repositorio local de Git con carácter definitivo.
        """
        async with self.lock:
            commit_msg = f"CRITICAL_PURGE [Ω_VCH] | Node: {purged_node_id} | Final_Seq: {last_stable_seq} | Root: {terminal_hash}"
            process = await asyncio.create_subprocess_exec(
                "git", "-C", str(self.repo_path), "commit", "--allow-empty", "-m", commit_msg,
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
            )
            await process.wait()

# --- MOTOR AST PARA INVARIANTES ---
class ASTNode:
    __slots__ = ("type", "value", "children")
    def __init__(self, node_type: str, value: Optional[str] = None, children: Optional[List['ASTNode']] = None):
        self.type: str = node_type
        self.value: Optional[str] = value
        self.children: List['ASTNode'] = children or []

    def to_dict(self) -> dict:
        return {"type": self.type, "value": self.value, "children": [c.to_dict() for c in self.children]}

class InvariantASTParser:
    @staticmethod
    def parse_expression(desc: str) -> ASTNode:
        found_ids = [m.group(0).upper() for m in re.finditer(r"Ω\d+", desc)]
        if not found_ids:
            return ASTNode("INVARIANT_LEAF", "SELF")
        children = [ASTNode("INVARIANT_REF", inv_id) for inv_id in found_ids]
        if " o " in desc.lower() or " OR " in desc:
            return ASTNode("OR", children=children)
        return ASTNode("AND", children=children)

# --- MODELO EXERGÉTICO OKAPI BM25 ---
class BM25Engine:
    __slots__ = ("b", "k1", "doc_term_freqs", "doc_lengths", "avg_doc_len", "doc_count", "idf")
    def __init__(self, b: float = 0.75, k1: float = 1.5):
        self.b = b
        self.k1 = k1
        self.doc_term_freqs: List[Dict[str, int]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_count: int = 0
        self.idf: Dict[str, float] = {}

    def fit(self, corpus: List[str]) -> None:
        self.doc_count = len(corpus)
        if self.doc_count == 0: return
        total_len = 0
        df: Dict[str, int] = {}

        for doc in corpus:
            tokens = RE_TOKENIZER.findall(doc.lower())
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_len += doc_len

            tf: Dict[str, int] = {}
            for token in tokens:
                tf[token] = tf.get(token, 0) + 1
            self.doc_term_freqs.append(tf)
            for token in tf.keys():
                df[token] = df.get(token, 0) + 1

        self.avg_doc_len = total_len / self.doc_count
        for token, freq in df.items():
            self.idf[token] = math.log((self.doc_count - freq + 0.5) / (freq + 0.5) + 1.0)

    def score(self, query_tokens: List[str], doc_idx: int) -> float:
        tf_map = self.doc_term_freqs[doc_idx]
        doc_len = self.doc_lengths[doc_idx]
        score = 0.0
        for token in query_tokens:
            if token not in tf_map: continue
            tf = tf_map[token]
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
            score += self.idf.get(token, 0.0) * (numerator / denominator)
        return score

# --- SUSTRETO DE PERSISTENCIA INMUTABLE (SQLITE WAL) ---
class SQLiteAppendOnlyStorage:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        # INV_BFT_02: Timeout explícito para evitar deadlocks termodinámicos
        self.conn = sqlite3.connect(self.db_path, timeout=5.0)
        self._init_db()

    def _init_db(self):
        with self.conn:
            self.conn.execute("PRAGMA journal_mode=WAL;")
            self.conn.execute("PRAGMA synchronous=NORMAL;")
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS master_ledger (
                    seq INTEGER PRIMARY KEY,
                    event_id TEXT UNIQUE,
                    stream TEXT,
                    payload_json TEXT,
                    cortex_taint TEXT,
                    lamport_t INTEGER,
                    prev_hash TEXT,
                    entry_hash TEXT,
                    created_at TEXT
                );
            """)
            self.conn.execute("""
                CREATE TRIGGER IF NOT EXISTS abort_updates BEFORE UPDATE ON master_ledger
                BEGIN
                    SELECT RAISE(FAIL, 'BFTCausalInvariantError: UPDATE blocked on append-only ledger.');
                END;
            """)
            self.conn.execute("""
                CREATE TRIGGER IF NOT EXISTS abort_deletes BEFORE DELETE ON master_ledger
                BEGIN
                    SELECT RAISE(FAIL, 'BFTCausalInvariantError: DELETE blocked on append-only ledger.');
                END;
            """)

    def write_envelope(self, env: C5EnrichedEnvelope):
        with self.conn:
            self.conn.execute("""
                INSERT OR IGNORE INTO master_ledger
                (seq, event_id, stream, payload_json, cortex_taint, lamport_t, prev_hash, entry_hash, created_at)
                VALUES (:seq, :event_id, :stream, :payload_json, :cortex_taint, :lamport_t, :prev_hash, :entry_hash, :created_at)
            """, env)

    def load_all(self) -> List[C5EnrichedEnvelope]:
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM master_ledger ORDER BY seq ASC")
        return [dict(row) for row in cursor.fetchall()] # type: ignore

# --- ACTOR CONCURRENTE SINGLE-WRITER BALANCED ---
class LexiconLedgerActor:
    def __init__(self, db_path: Path, bft_node: Optional[BFTNode] = None):
        self.storage = SQLiteAppendOnlyStorage(db_path)
        self.vault = CortexVault()
        self.sentinel = GitSentinel(db_path.parent)
        self.queue: asyncio.Queue = asyncio.Queue()
        self._loop_task: Optional[asyncio.Task] = None
        self.is_running = False

        # Inyección del nodo de red BFT L4
        self.bft_node = bft_node
        if self.bft_node:
            self.bft_node.ledger_actor = self

        self.current_seq = 0
        self.lamport_clock = 0
        self.last_hash = "0" * 64
        self.namespace_uuid = uuid.UUID("bfa707e8-0000-5000-a000-000000000000")
        self._rehydrate_state()

    def _rehydrate_state(self):
        records = self.storage.load_all()
        if records:
            last_record = records[-1]
            self.current_seq = last_record["seq"]
            self.lamport_clock = last_record["lamport_t"]
            self.last_hash = last_record["entry_hash"]

    async def start(self):
        self.is_running = True
        self._loop_task = asyncio.create_task(self._processing_loop())

    async def stop(self):
        self.is_running = False
        if self._loop_task:
            await self.queue.put(None)
            await self._loop_task

    async def submit_mutation(self, term: str, category: str, description: str, taint: str) -> asyncio.Future:
        future = asyncio.get_running_loop().create_future()
        await self.queue.put((term, category, description, taint, future))
        return future

    async def _processing_loop(self):
        while self.is_running:
            item = await self.queue.get()
            if item is None:
                self.queue.task_done()
                break
            term, category, description, taint, future = item
            try:
                payload = {"term": term, "category": category, "description": description}
                canonical_payload = json.dumps(payload, sort_keys=True, separators=(',', ':'))
                event_id = str(uuid.uuid5(self.namespace_uuid, f"{canonical_payload}_{taint}"))

                cursor = self.storage.conn.cursor()
                cursor.execute("SELECT * FROM master_ledger WHERE event_id = ?", (event_id,))
                existing = cursor.fetchone()

                if existing:
                    self.storage.conn.row_factory = sqlite3.Row
                    cursor.execute("SELECT * FROM master_ledger WHERE event_id = ?", (event_id,))
                    future.set_result(dict(cursor.fetchone()))
                else:
                    # Cálculo anticipado del sobre para validación criptográfica en la red
                    temp_seq = self.current_seq + 1
                    temp_lamport = self.lamport_clock + 1
                    created_at = datetime.now(timezone.utc).isoformat()

                    shielded_payload = self.vault.shield_payload(canonical_payload)
                    shielded_event_id = self.vault.shield_payload(event_id)
                    shielded_stream = self.vault.shield_payload("cortex.ontology")
                    shielded_taint = self.vault.shield_payload(taint)

                    envelope_data = f"{temp_seq}|{shielded_event_id}|{shielded_payload}|{shielded_taint}|{temp_lamport}|{self.last_hash}|{created_at}"
                    entry_hash = hashlib.sha3_256(envelope_data.encode('utf-8')).hexdigest()

                    envelope: C5EnrichedEnvelope = {
                        "seq": temp_seq,
                        "event_id": shielded_event_id,
                        "stream": shielded_stream,
                        "payload_json": shielded_payload,
                        "cortex_taint": shielded_taint,
                        "lamport_t": temp_lamport,
                        "prev_hash": self.last_hash,
                        "entry_hash": entry_hash,
                        "created_at": created_at
                    }

                    # --- INTERCEPCIÓN EXERGÉTICA CRÍTICA NIVEL L4 ---
                    if self.bft_node:
                        if self.bft_node.is_primary:
                            network_future = asyncio.get_running_loop().create_future()
                            await self.bft_node.propose_block(temp_seq, entry_hash, shielded_taint, network_future)
                            await network_future
                        else:
                            # Los seguidores registran cuando su propia red alcance el COMMIT
                            pass

                    # Actualización de contadores locales
                    self.current_seq = temp_seq
                    self.lamport_clock = temp_lamport
                    self.last_hash = entry_hash

                    # Consolidación física L2
                    self.storage.write_envelope(envelope)

                    # Testigo L3 asíncrono
                    asyncio.create_task(self.sentinel.commit_entry(self.current_seq, entry_hash, taint))
                    future.set_result(envelope)
            except Exception as e:
                future.set_exception(e)
            finally:
                self.queue.task_done()

# --- NÚCLEO CENTRAL DEL TRANSDUCTOR ---
class LexiconEntry:
    __slots__ = ("key", "term", "category", "description", "ast", "meta_envelope")
    def __init__(self, key: str, term: str, category: str, description: str, ast: ASTNode, meta_envelope: dict):
        self.key = key
        self.term = term
        self.category = category
        self.description = description
        self.ast = ast
        self.meta_envelope = meta_envelope

class LexiconEngine:
    def __init__(self, root_dir: Optional[Path] = None, db_name: str = "master_ledger.db"):
        self.root_dir = root_dir or Path.cwd()
        self.glosario_path = self.root_dir / "glosario.md"
        self.agents_path = self.root_dir / "AGENTS.md"
        self.actor = LexiconLedgerActor(self.root_dir / db_name)
        self.terms: Dict[str, LexiconEntry] = {}
        self.invariants: Dict[str, Tuple[str, ASTNode]] = {}
        self.bm25 = BM25Engine()
        self._term_keys_ordered: List[str] = []

    async def initialize_c5_substrate(self, system_taint: str = "system:boot_sync"):
        await self.actor.start()
        self._load_invariants()
        if self.glosario_path.exists():
            content = self.glosario_path.read_text(encoding="utf-8", errors="replace")
            futures = []
            for m in RE_GLOSARIO.finditer(content):
                term = m.group("term").strip()
                cat = m.group("category").strip()
                desc = m.group("desc").strip()
                key = term.lower().replace(" ", "_")
                fut = await self.actor.submit_mutation(term, cat, desc, system_taint)
                futures.append((key, term, cat, desc, fut))

            for key, term, cat, desc, fut in futures:
                envelope = await fut
                ast_node = InvariantASTParser.parse_expression(desc)
                self.terms[key] = LexiconEntry(
                    key=key, term=term, category=cat, description=desc, ast=ast_node, meta_envelope=envelope
                )
            self._initialize_search_index()

    def _load_invariants(self) -> None:
        if not self.agents_path.exists(): return
        content = self.agents_path.read_text(encoding="utf-8", errors="replace")
        for m in RE_INVARIANTES.finditer(content):
            inv_id = m.group("id").strip().upper()
            title = m.group("title").strip()
            desc = m.group("desc").strip()
            self.invariants[inv_id] = (f"{title}: {desc}", InvariantASTParser.parse_expression(desc))

    def _initialize_search_index(self) -> None:
        corpus: List[str] = []
        self._term_keys_ordered = list(self.terms.keys())
        for key in self._term_keys_ordered:
            entry = self.terms[key]
            corpus.append(f"{entry.term} {entry.category} {entry.description}")
        self.bm25.fit(corpus)

    def search_bm25(self, query: str, limit: int = 5) -> List[Tuple[LexiconEntry, float]]:
        query_tokens = RE_TOKENIZER.findall(query.lower())
        if not query_tokens or not self._term_keys_ordered: return []
        scored_results: List[Tuple[LexiconEntry, float]] = []
        for idx, key in enumerate(self._term_keys_ordered):
            score = self.bm25.score(query_tokens, idx)
            if score > 0.0: scored_results.append((self.terms[key], score))
        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results[:limit]

    def get_invariant(self, inv_id: str) -> Optional[str]:
        if not self.invariants:
            self._load_invariants()
        val = self.invariants.get(inv_id.upper())
        return val[0] if val else None

    def search(self, query: str, limit: int = 5) -> List[LexiconEntry]:
        scored = self.search_bm25(query, limit=limit)
        return [entry for entry, score in scored]

    def verify_ledger_integrity(self) -> bool:
        records = self.actor.storage.load_all()
        expected_prev = "0" * 64
        for idx, env in enumerate(records):
            if env["seq"] != idx + 1: return False
            if env["prev_hash"] != expected_prev: return False
            envelope_data = f"{env['seq']}|{env['event_id']}|{env['payload_json']}|{env['cortex_taint']}|{env['lamport_t']}|{env['prev_hash']}|{env['created_at']}"
            if hashlib.sha3_256(envelope_data.encode('utf-8')).hexdigest() != env["entry_hash"]: return False
            expected_prev = env["entry_hash"]
        return True

    async def close(self):
        await self.actor.stop()

def lookup_invariant(inv_id: str) -> Optional[str]:
    engine = LexiconEngine()
    return engine.get_invariant(inv_id)

