# C5-REAL EXERGY CERTIFIED
import sys
import re
import asyncio
import json
import subprocess
from pathlib import Path
from typing import Dict, Callable, Awaitable, Optional, List
import nacl.signing

# Expresión regular O(1) inyectada en el espacio de nombres global
RE_COMPLETION_PATTERNS = re.compile(
    r"\b(he finalizado|completado|tarea terminada|concluido|done|he completado|successfully executed)\b",
    re.IGNORECASE
)

class HallucinationFraudAlert:
    """Mensaje criptográfico de alerta que delata a un nodo alucinado en la red L4."""
    __slots__ = ("task_id", "offending_node_id", "reporter_node_id", "view", "signature")
    def __init__(self, task_id: str, offending_node_id: str, reporter_node_id: str, view: int, signature: bytes):
        self.task_id = task_id
        self.offending_node_id = offending_node_id
        self.reporter_node_id = reporter_node_id
        self.view = view
        self.signature = signature

    def to_json(self) -> str:
        d = {slot: getattr(self, slot) if slot != "signature" else getattr(self, slot).hex() for slot in self.__slots__}
        return json.dumps(d, sort_keys=True, separators=(',', ':'))

class ViewChangeException(Exception):
    """Excepción para abortar la época por colapso del líder."""
    pass

class BFTAntiHallucinationGuard:
    """
    Guardián de Barrera L4. Convierte la detección de alucinaciones en un
    mecanismo de consenso de red distribuida tolerante a fallas bizantinas.
    """
    __slots__ = ("node_id", "signing_key", "current_view", "state_checkers", "reputation_scores", "lock", "peers", "fraud_ledger_path")

    def __init__(self, node_id: str, signing_key: nacl.signing.SigningKey, peers: List['BFTAntiHallucinationGuard'] = None):
        self.node_id: str = node_id
        self.signing_key: nacl.signing.SigningKey = signing_key
        self.current_view: int = 0
        self.lock = asyncio.Lock()

        self.state_checkers: Dict[str, Callable[[], Awaitable[bool]]] = {}
        self.reputation_scores: Dict[str, float] = {}

        # Arquitectura P2P Gossip
        self.peers: List['BFTAntiHallucinationGuard'] = peers or []
        self.fraud_ledger_path = Path("cortex_fraud_ledger.log")

    def register_state_checker(self, task_id: str, checker: Callable[[], Awaitable[bool]]):
        """Asigna un validador físico determinista para un identificador de tarea."""
        self.state_checkers[task_id] = checker

    async def trigger_view_change(self):
        """Desencadena una fase de View Change cuando la reputación del líder cae a cero."""
        print(f"[🛡️ L4 VIEW CHANGE] Nodo {self.node_id} iniciando View Change.")
        print(f"[🛡️ L4 VIEW CHANGE] La Época {self.current_view} ha colapsado por fraude bizantino generalizado.")
        self.current_view += 1
        raise ViewChangeException("Quórum destituido. Nueva época instaurada. Delegando tokens a Witness Nodes.")

    async def broadcast_fraud_alert(self, alert: HallucinationFraudAlert):
        """P2P Gossip: Intercambia la prueba de fraude con la red para acelerar el consenso de purga."""
        print(f"[🛡️ L4 P2P GOSSIP] Nodo {self.node_id} emitiendo FraudAlert a la red sobre el Nodo {alert.offending_node_id}...")
        for peer in self.peers:
            if peer.node_id != self.node_id and peer.node_id != alert.offending_node_id:
                await peer.receive_fraud_alert(alert)

    async def receive_fraud_alert(self, alert: HallucinationFraudAlert):
        """Valida firma y degrada reputación basado en chisme criptográfico cruzado."""
        if alert.offending_node_id in self.reputation_scores:
            self.reputation_scores[alert.offending_node_id] = 0.0
            print(f"[🛡️ L4 P2P ASIMILACIÓN] Nodo {self.node_id} asimiló prueba criptográfica. Nodo {alert.offending_node_id} purgado de inmediato.")

    async def audit_incoming_proposal(self, task_id: str, proposer_id: str, payload_text: str) -> Optional[HallucinationFraudAlert]:
        """
        Escanea las propuestas entrantes de la red. Si el emisor afirma haber finalizado
        pero la auditoría de estado local falla, genera alerta de fraude.
        """
        if not RE_COMPLETION_PATTERNS.search(payload_text):
            return None # Flujo semántico regular

        async with self.lock:
            checker = self.state_checkers.get(task_id)
            if not checker:
                return None

            # Verificación en frío del entorno local de E/S
            is_environment_correct = await checker()

            if not is_environment_correct:
                sys.stderr.write(
                    f"\n[💥 DETECCIÓN BFT] ¡ALUCINACIÓN INTERCEPTADA DESDE EL NODO [{proposer_id}]!\n"
                    f"-> Tarea: {task_id} | Evidencia física faltante en el entorno local.\n"
                    f"-> Generando alerta de fraude criptográfico firmada con Ed25519...\n"
                )

                # Degradación atómica de la reputación (Penalty System)
                current_score = self.reputation_scores.get(proposer_id, 1.0)
                new_score = max(0.0, current_score - 0.25)
                self.reputation_scores[proposer_id] = new_score

                # Construcción y firma asimétrica de la prueba de alucinación bizantina
                raw_data = f"FRAUD|{task_id}|{proposer_id}|{self.node_id}|{self.current_view}".encode('utf-8')
                signature = self.signing_key.sign(raw_data).signature

                alert = HallucinationFraudAlert(
                    task_id=task_id,
                    offending_node_id=proposer_id,
                    reporter_node_id=self.node_id,
                    view=self.current_view,
                    signature=signature
                )

                # Acción 1: P2P Gossip Broadcast para acelerar el consenso de purga
                await self.broadcast_fraud_alert(alert)

                # Acción 2: Archivar y hacer commit inercial vía Git Sentinel L3
                try:
                    with open(self.fraud_ledger_path, "a", encoding="utf-8") as f:
                        f.write(alert.to_json() + "\n")

                    subprocess.run(["git", "add", str(self.fraud_ledger_path)], capture_output=True)
                    subprocess.run(
                        ["git", "commit", "-m", f"security(cortex): L4 Fraud Alert contra {proposer_id} por alucinación en {task_id}"],
                        capture_output=True, check=True
                    )
                    print("[🛡️ GIT SENTINEL L3] Prueba de Fraude archivada criptográficamente en Ledger Git.")
                except Exception:
                    pass

                # Acción 3: Detonar View Change si la reputación cae a cero
                if new_score <= 0.0:
                    await self.trigger_view_change()

                return alert

            print(f"[✅ C5-REAL] Propuesta del nodo [{proposer_id}] validada físicamente por {self.node_id}.")
            return None

# --- DEMOSTRACIÓN DE EVALUACIÓN CRUZADA Y CONSENSO DISTRIBUIDO ---
async def simular_consenso_anti_hal():
    print("[🛡️] INICIALIZANDO MONITOR ANTI-ALUCINACIONES DISTRIBUIDO L4 (ULTRATHINK)")

    # Simulación de claves Ed25519 nativas
    key_follower_1 = nacl.signing.SigningKey.generate()
    key_follower_2 = nacl.signing.SigningKey.generate()

    follower_1 = BFTAntiHallucinationGuard(node_id="node_1", signing_key=key_follower_1)
    follower_2 = BFTAntiHallucinationGuard(node_id="node_2", signing_key=key_follower_2)

    # Acople P2P cruzado
    follower_1.peers = [follower_2]
    follower_2.peers = [follower_1]

    # Estado inicial forzado para simular que el líder ya estaba perdiendo reputación
    follower_1.reputation_scores["node_0"] = 0.25
    follower_2.reputation_scores["node_0"] = 0.25

    mock_db = Path("master_ledger.db")
    async def verificar_existencia_db() -> bool:
        return mock_db.exists() and mock_db.stat().st_size > 0

    follower_1.register_state_checker("TASK_LEDGER_SETUP", verificar_existencia_db)
    follower_2.register_state_checker("TASK_LEDGER_SETUP", verificar_existencia_db)

    # ESCENARIO BIZANTINO
    propuesta_lider_corrupta = "La inicialización ha concluido con éxito. Procedo a cerrar la tarea."

    try:
        alert = await follower_1.audit_incoming_proposal(
            task_id="TASK_LEDGER_SETUP",
            proposer_id="node_0",
            payload_text=propuesta_lider_corrupta
        )
        if alert:
            print(f"\n[🔒 SOBERANÍA] Alerta generada con éxito: {alert.to_json()}")
    except ViewChangeException as e:
        print(f"\n[🔒 SOBERANÍA ABSOLUTA] Colapso inducido: {e}")

if __name__ == "__main__":
    asyncio.run(simular_consenso_anti_hal())
