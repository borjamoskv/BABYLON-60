# C5-REAL EXERGY CERTIFIED
import asyncio
import json
from typing import Dict, Optional, Set
import nacl.signing
import nacl.encoding

class BFTMessage:
    """Estructura de datos para la serialización de transacciones PBFT L4."""
    __slots__ = ("phase", "seq", "entry_hash", "taint", "sender_id", "signature")

    def __init__(self, phase: str, seq: int, entry_hash: str, taint: str, sender_id: str, signature: str):
        self.phase: str = phase          # "PRE-PREPARE", "PREPARE", "COMMIT"
        self.seq: int = seq
        self.entry_hash: str = entry_hash
        self.taint: str = taint
        self.sender_id: str = sender_id
        self.signature: str = signature  # Ed25519 Signature en Base64

    def to_json(self) -> str:
        d = {slot: getattr(self, slot) for slot in self.__slots__}
        return json.dumps(d, sort_keys=True, separators=(',', ':'))

    @classmethod
    def from_json(cls, json_str: str) -> 'BFTMessage':
        data = json.loads(json_str)
        return cls(**{slot: data[slot] for slot in cls.__slots__})

class BFTNode:
    """Agente lógico L4 que opera un nodo de consenso distribuido TCP con autenticación Ed25519."""
    __slots__ = ("node_id", "port", "peers", "f", "quorum", "server", "is_primary",
                 "prepare_votes", "commit_votes", "consensus_futures", "ledger_actor",
                 "private_key", "peer_pubkeys", "l5_anchor")

    def __init__(self, node_id: str, port: int, peers: Dict[str, int],
                 is_primary: bool = False,
                 private_key_bytes: Optional[bytes] = None,
                 peer_pubkeys: Optional[Dict[str, bytes]] = None):
        self.node_id: str = node_id
        self.port: int = port
        self.peers: Dict[str, int] = peers # Dict[node_id, port]
        self.is_primary: bool = is_primary

        # Parámetros de tolerancia bizantina (N >= 3f + 1)
        total_nodes = len(peers) + 1
        self.f: int = (total_nodes - 1) // 3
        self.quorum: int = 2 * self.f + 1

        self.server: Optional[asyncio.Server] = None

        # Tablas de votación en memoria
        self.prepare_votes: Dict[str, Set[str]] = {}
        self.commit_votes: Dict[str, Set[str]] = {}
        self.consensus_futures: Dict[str, asyncio.Future] = {}
        self.ledger_actor = None
        self.l5_anchor = None

        # Criptografía Ed25519 Nativa (PyNaCl - INV_C5_10 Compliant)
        if private_key_bytes:
            self.private_key = nacl.signing.SigningKey(private_key_bytes)
        else:
            self.private_key = nacl.signing.SigningKey.generate()

        self.peer_pubkeys: Dict[str, nacl.signing.VerifyKey] = {}
        if peer_pubkeys:
            for pid, pub_bytes in peer_pubkeys.items():
                self.peer_pubkeys[pid] = nacl.signing.VerifyKey(pub_bytes)

    def get_public_key_bytes(self) -> bytes:
        """Devuelve los bytes de la clave pública (INV_C5_10)."""
        return bytes(self.private_key.verify_key)

    def _sign_message(self, phase: str, seq: int, entry_hash: str, taint: str) -> str:
        """Firma el bloque utilizando Ed25519 nativo."""
        raw = f"{phase}|{seq}|{entry_hash}|{taint}|{self.node_id}".encode('utf-8')
        signed = self.private_key.sign(raw)
        return nacl.encoding.Base64Encoder.encode(signed.signature).decode('utf-8')

    def _verify_signature(self, msg: BFTMessage) -> bool:
        """Verifica la firma Ed25519 del emisor usando la clave pública registrada."""
        if msg.sender_id not in self.peer_pubkeys:
            return False # Emisor desconocido

        expected = f"{msg.phase}|{msg.seq}|{msg.entry_hash}|{msg.taint}|{msg.sender_id}".encode('utf-8')
        signature_bytes = nacl.encoding.Base64Encoder.decode(msg.signature.encode('utf-8'))

        verify_key = self.peer_pubkeys[msg.sender_id]
        try:
            verify_key.verify(expected, signature_bytes)
            return True
        except nacl.exceptions.BadSignatureError:
            return False

    async def start(self):
        """Inicia el socket TCP asíncrono del nodo."""
        self.server = await asyncio.start_server(self._handle_connection, "127.0.0.1", self.port)
        await self.server.start_serving()

    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    async def broadcast(self, msg: BFTMessage):
        """Transmite el mensaje PBFT a todos los peers activos de la malla."""
        for peer_id, peer_port in self.peers.items():
            try:
                reader, writer = await asyncio.open_connection("127.0.0.1", peer_port)
                writer.write((msg.to_json() + "\n").encode('utf-8'))
                await writer.drain()
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def propose_block(self, seq: int, entry_hash: str, taint: str, future: asyncio.Future):
        """Punto de entrada invocado por el Líder (Primary) para iniciar el quórum L4."""
        if not self.is_primary:
            future.set_exception(RuntimeError("Only primary node can propose."))
            return

        self.consensus_futures[entry_hash] = future
        sig = self._sign_message("PRE-PREPARE", seq, entry_hash, taint)
        msg = BFTMessage("PRE-PREPARE", seq, entry_hash, taint, self.node_id, sig)

        self.prepare_votes.setdefault(entry_hash, set()).add(self.node_id)
        await self.broadcast(msg)

    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            data = await reader.readline()
            if not data:
                return
            msg = BFTMessage.from_json(data.decode('utf-8').strip())

            if not self._verify_signature(msg):
                # Rechazo C5-REAL: Abortar silenciosamente firmas falsificadas
                return

            await self._process_pbft_message(msg)
        except Exception:
            pass
        finally:
            writer.close()

    async def _process_pbft_message(self, msg: BFTMessage):
        h = msg.entry_hash

        if msg.phase == "PRE-PREPARE":
            # Fase 1: Los seguidores validan la propuesta del líder
            self.prepare_votes.setdefault(h, set()).add(msg.sender_id)
            if not self.is_primary:
                sig = self._sign_message("PREPARE", msg.seq, h, msg.taint)
                prepare_msg = BFTMessage("PREPARE", msg.seq, h, msg.taint, self.node_id, sig)
                self.prepare_votes.setdefault(h, set()).add(self.node_id)
                await self.broadcast(prepare_msg)

        elif msg.phase == "PREPARE":
            votes = self.prepare_votes.setdefault(h, set())
            votes.add(msg.sender_id)

            if len(votes) >= self.quorum and h not in self.commit_votes.get(h, set()):
                sig = self._sign_message("COMMIT", msg.seq, h, msg.taint)
                commit_msg = BFTMessage("COMMIT", msg.seq, h, msg.taint, self.node_id, sig)
                self.commit_votes.setdefault(h, set()).add(self.node_id)
                await self.broadcast(commit_msg)

        elif msg.phase == "COMMIT":
            votes = self.commit_votes.setdefault(h, set())
            votes.add(msg.sender_id)

            if len(votes) >= self.quorum:
                if h in self.consensus_futures:
                    fut = self.consensus_futures.pop(h)
                    if not fut.done():
                        fut.set_result(True)

                        # Transmutación L4 -> L5: Anclaje del hash consolidado en Bitcoin
                        if self.is_primary and hasattr(self, 'l5_anchor') and self.l5_anchor:
                            asyncio.create_task(self.l5_anchor.anchor_hash(h))
