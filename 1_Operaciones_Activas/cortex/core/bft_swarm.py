# C5-REAL EXERGY CERTIFIED
"""Nivel L4: BFT Swarm Quorum (cortex/core/bft_swarm.py)

Proporciona la topología de malla asíncrona para la validación PBFT.
Garantiza que el consenso L4 alcance el umbral de 2f+1 antes de la persistencia L2/L3.
"""

import os
import json
import asyncio
import hashlib
from typing import Dict, List, Optional, Callable, Any
from cryptography.fernet import Fernet

class BFTMessage:
    __slots__ = ("phase", "seq", "envelope", "node_id", "signature")

    def __init__(self, phase: str, seq: int, envelope: dict, node_id: str, signature: str = ""):
        self.phase = phase
        self.seq = seq
        self.envelope = envelope
        self.node_id = node_id
        self.signature = signature

    def to_dict(self) -> dict:
        return {
            "phase": self.phase,
            "seq": self.seq,
            "envelope": self.envelope,
            "node_id": self.node_id,
            "signature": self.signature
        }

    @staticmethod
    def sign_payload(secret: str, data: dict) -> str:
        """Firma simétrica del bloque BFT."""
        canon = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha3_256(f"{canon}_{secret}".encode('utf-8')).hexdigest()

class BFTNode:
    """Nodo del enjambre L4 que ejecuta PBFT simplificado a través de sockets TCP."""

    def __init__(self, host: str, port: int, peers: List[Tuple[str, int]], f_faults: int = 1):
        self.host = host
        self.port = port
        self.node_id = f"{host}:{port}"
        self.peers = peers
        self.f_faults = f_faults
        self.quorum_size = 2 * self.f_faults + 1

        self.secret_key = os.getenv("CORTEX_VAULT_KEY", "bft_dev_secret")
        self.server: Optional[asyncio.AbstractServer] = None

        # Almacén de estado del consenso: seq -> phase -> Set(node_ids)
        self.consensus_state: Dict[int, Dict[str, set]] = {}
        # Promesas que esperan el consenso de una secuencia
        self.pending_commits: Dict[int, asyncio.Future] = {}

        self.on_commit_callback: Optional[Callable[[dict], Any]] = None

    async def start(self):
        """Inicia el servidor TCP del nodo L4."""
        self.server = await asyncio.start_server(self._handle_client, self.host, self.port)

    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            data = await reader.read(4096)
            if not data:
                return

            payload = json.loads(data.decode('utf-8'))
            msg = BFTMessage(**payload)

            # Validación de firma
            sign_data = {"phase": msg.phase, "seq": msg.seq, "envelope": msg.envelope, "node_id": msg.node_id}
            expected_sig = BFTMessage.sign_payload(self.secret_key, sign_data)

            if msg.signature != expected_sig:
                # Falla Bizantina Detectada (Firma Inválida)
                writer.close()
                await writer.wait_closed()
                return

            await self._process_message(msg)

            writer.write(b'ACK')
            await writer.drain()
        except Exception:
            pass
        finally:
            writer.close()
            await writer.wait_closed()

    async def _broadcast(self, msg: BFTMessage):
        """Emite el mensaje a todos los pares (y a sí mismo para avanzar estado)."""
        await self._process_message(msg) # Auto-procesamiento

        for peer_host, peer_port in self.peers:
            try:
                reader, writer = await asyncio.open_connection(peer_host, peer_port)
                writer.write(json.dumps(msg.to_dict()).encode('utf-8'))
                await writer.drain()
                writer.close()
                await writer.wait_closed()
            except ConnectionRefusedError:
                # Nodo caído, ignorar
                pass

    async def _process_message(self, msg: BFTMessage):
        """Máquina de estados PBFT (Pre-Prepare -> Prepare -> Commit)."""
        seq = msg.seq
        if seq not in self.consensus_state:
            self.consensus_state[seq] = {"PREPARE": set(), "COMMIT": set()}

        if msg.phase == "PRE-PREPARE":
            # Recibido del líder, procedemos a votar PREPARE
            sign_data = {"phase": "PREPARE", "seq": seq, "envelope": msg.envelope, "node_id": self.node_id}
            sig = BFTMessage.sign_payload(self.secret_key, sign_data)
            prep_msg = BFTMessage("PREPARE", seq, msg.envelope, self.node_id, sig)
            asyncio.create_task(self._broadcast(prep_msg))

        elif msg.phase == "PREPARE":
            self.consensus_state[seq]["PREPARE"].add(msg.node_id)
            if len(self.consensus_state[seq]["PREPARE"]) >= self.quorum_size:
                # Cuórum de Prepare alcanzado, emitir COMMIT
                sign_data = {"phase": "COMMIT", "seq": seq, "envelope": msg.envelope, "node_id": self.node_id}
                sig = BFTMessage.sign_payload(self.secret_key, sign_data)
                com_msg = BFTMessage("COMMIT", seq, msg.envelope, self.node_id, sig)
                # Emitimos commit solo si no lo hemos hecho ya
                if self.node_id not in self.consensus_state[seq]["COMMIT"]:
                    asyncio.create_task(self._broadcast(com_msg))

        elif msg.phase == "COMMIT":
            self.consensus_state[seq]["COMMIT"].add(msg.node_id)
            if len(self.consensus_state[seq]["COMMIT"]) >= self.quorum_size:
                # Cuórum absoluto. Resolver promesas de escritura
                if seq in self.pending_commits and not self.pending_commits[seq].done():
                    self.pending_commits[seq].set_result(msg.envelope)
                    if self.on_commit_callback:
                        self.on_commit_callback(msg.envelope)

    async def propose_mutation(self, seq: int, envelope: dict) -> dict:
        """El líder local propone una mutación al enjambre. (Punto de entrada desde Lexicon)"""
        future = asyncio.get_running_loop().create_future()
        self.pending_commits[seq] = future

        sign_data = {"phase": "PRE-PREPARE", "seq": seq, "envelope": envelope, "node_id": self.node_id}
        sig = BFTMessage.sign_payload(self.secret_key, sign_data)
        msg = BFTMessage("PRE-PREPARE", seq, envelope, self.node_id, sig)

        await self._broadcast(msg)
        return await future
