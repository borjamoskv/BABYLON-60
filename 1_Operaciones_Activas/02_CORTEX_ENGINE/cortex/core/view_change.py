# C5-REAL EXERGY CERTIFIED
import asyncio
from typing import Dict, Set, Optional
import nacl.signing

class ViewChangeMessage:
    """Estructura criptográfica para la transmisión de votos de destitución."""
    __slots__ = ("next_view", "last_stable_seq", "last_stable_hash", "sender_id", "signature")

    def __init__(self, next_view: int, last_stable_seq: int, last_stable_hash: str, sender_id: str, signature: bytes):
        self.next_view: int = next_view
        self.last_stable_seq: int = last_stable_seq
        self.last_stable_hash: str = last_stable_hash
        self.sender_id: str = sender_id
        self.signature: bytes = signature

class ViewChangeEngine:
    """Motor termodinámico encargado de medir el letargo del líder y forzar el quórum de cambio."""
    __slots__ = ("node_id", "current_view", "signing_key", "f", "quorum",
                 "view_change_votes", "timer_task", "delta_t_exergia", "is_primary", "peers", "broadcast_callback")

    def __init__(self, node_id: str, signing_key: nacl.signing.SigningKey, total_nodes: int, peers: list, delta_t: float = 2.0):
        self.node_id: str = node_id
        self.signing_key: nacl.signing.SigningKey = signing_key
        self.peers: list = peers
        self.current_view: int = 0
        self.delta_t_exergia: float = delta_t # Tiempo límite antes de declarar letargo bizantino

        self.f: int = (total_nodes - 1) // 3
        self.quorum: int = 2 * self.f + 1
        self.is_primary: bool = (node_id == "node_0")

        # Almacén de votos para la vista propuesta: Dict[next_view, Set[sender_id]]
        self.view_change_votes: Dict[int, Set[str]] = {}
        self.timer_task: Optional[asyncio.Task] = None
        self.broadcast_callback = None # Inyectado en simulacion

    def reset_exergy_timer(self, seq: int):
        """Reinicia el temporizador ante un flujo regular de mensajes válidos del líder."""
        if self.is_primary:
            return
        if self.timer_task and not self.timer_task.done():
            self.timer_task.cancel()
        self.timer_task = asyncio.create_task(self._await_leader_heartbeat(seq))

    async def _await_leader_heartbeat(self, expected_seq: int):
        """Monitorea el letargo del líder. Dispara el colapso si expira el tiempo límite."""
        try:
            await asyncio.sleep(self.delta_t_exergia)
            # Si despierta sin haber sido cancelado, el líder ha entrado en letargo bizantino
            print(f"\n[⚠️ LETARGO] {self.node_id} detectó silencio del Líder en seq {expected_seq}. Iniciando View Change.")
            await self.initiate_view_change(expected_seq)
        except asyncio.CancelledError:
            pass # El líder envió el bloque a tiempo; gasto energético cero

    async def initiate_view_change(self, last_seq: int):
        """Construye y propaga la propuesta de destitución firmada asimétricamente."""
        next_view = self.current_view + 1
        fake_last_hash = "dummy_hash_link_l4" # En producción se extrae del storage L2

        raw_data = f"{next_view}|{last_seq}|{fake_last_hash}|{self.node_id}".encode('utf-8')
        signature = self.signing_key.sign(raw_data).signature

        msg = ViewChangeMessage(next_view, last_seq, fake_last_hash, self.node_id, signature)
        self.view_change_votes.setdefault(next_view, set()).add(self.node_id)

        # Difusión en malla del voto de destitución
        await self._broadcast_view_change(msg)

    async def receive_view_change(self, msg: ViewChangeMessage, verify_key: nacl.signing.VerifyKey):
        """Valida las firmas de destitución entrantes y evalúa el estado de quórum."""
        raw_data = f"{msg.next_view}|{msg.last_stable_seq}|{msg.last_stable_hash}|{msg.sender_id}".encode('utf-8')
        try:
            verify_key.verify(raw_data, msg.signature)
        except Exception:
            print(f"[🔥 ATACA] Firma de View Change corrupta rechazada desde {msg.sender_id}")
            return

        votes = self.view_change_votes.setdefault(msg.next_view, set())
        votes.add(msg.sender_id)

        # Evaluación atómica del quórum de destitución (2f + 1)
        if len(votes) >= self.quorum and msg.next_view > self.current_view:
            self.current_view = msg.next_view
            # Determinación matemática del nuevo líder por residuo topológico
            new_leader_idx = self.current_view % (len(self.peers) + 1)
            self.is_primary = (f"node_{new_leader_idx}" == self.node_id)

            print(f"[⚙️ CONVERGENCIA] Quórum de View Change exitoso. Nueva Vista: {self.current_view}. ¿Es {self.node_id} el nuevo Líder?: {self.is_primary}")
            if self.timer_task and not self.timer_task.done():
                self.timer_task.cancel()

    async def _broadcast_view_change(self, msg: ViewChangeMessage):
        """Abstracción de transmisión de red para la simulación del protocolo."""
        if self.broadcast_callback:
            await self.broadcast_callback(msg)
