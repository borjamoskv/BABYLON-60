# C5-REAL EXERGY CERTIFIED
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path.cwd() / "1_Operaciones_Activas"))

from typing import List, Dict
import nacl.signing
from cortex.core.bft_swarm import BFTNode, BFTMessage

class ByzantineNode(BFTNode):
    """Nodo corrupto modificado intencionadamente para simular fallos bizantinos."""
    async def _process_pbft_message(self, msg: BFTMessage):
        if msg.phase == "PRE-PREPARE":
            # Inyección de firma corrupta deliberada (Falsificación de voto)
            corrupt_sig = "CORRUPT_SIGNATURE_DATA_X"
            prepare_msg = BFTMessage("PREPARE", msg.seq, msg.entry_hash, msg.taint, self.node_id, corrupt_sig)
            print(f"[🔥 ATACA] Nodo Bizantino {self.node_id} transmitiendo firma falsificada.")
            await self.broadcast(prepare_msg)

async def main():
    print("[🛡️] CONFIGURANDO ENJAMBRE BFT L4 (N=4, f=1, CUÓRUM=3)")
    print("[🔑] Generando claves Ed25519 (PyNaCl)...")

    ports = {"node_0": 9001, "node_1": 9002, "node_2": 9003, "node_3": 9004}
    nodes: List[BFTNode] = []

    # Generar claves para todos
    keys: Dict[str, nacl.signing.SigningKey] = {}
    pubkeys: Dict[str, bytes] = {}
    for name in ports.keys():
        sk = nacl.signing.SigningKey.generate()
        keys[name] = sk
        pubkeys[name] = bytes(sk.verify_key)

    # Instanciación de nodos
    for name, port in ports.items():
        peers = {k: v for k, v in ports.items() if k != name}
        if name == "node_3":
            node = ByzantineNode(
                name, port, peers, is_primary=False,
                private_key_bytes=bytes(keys[name]),
                peer_pubkeys=pubkeys
            )
        else:
            node = BFTNode(
                name, port, peers, is_primary=(name == "node_0"),
                private_key_bytes=bytes(keys[name]),
                peer_pubkeys=pubkeys
            )
        nodes.append(node)
        await node.start()

    print("[🟢] Malla TCP activa. Nodos escuchando en localhost:9001-9004 (Ed25519 Nativo).")

    leader = nodes[0]
    test_future = asyncio.get_running_loop().create_future()

    print("\n[🎯] Líder emitiendo bloque experimental al Swarm...")
    dummy_hash = "sha3_sample_root_hash_validation_c5_real"
    await leader.propose_block(seq=1, entry_hash=dummy_hash, taint="user:l4_test_audit", future=test_future)

    try:
        await asyncio.wait_for(test_future, timeout=3.0)
        print(f"\n[✅] ENTORNO COMPLETO: Consenso L4 alcanzado de forma exitosa.")
        print(f" Votos Prepare acumulados para el bloque: {leader.prepare_votes[dummy_hash]}")
        print(f" Votos Commit acumulados para el bloque: {leader.commit_votes[dummy_hash]}")
        print("[ℹ️] El sistema ignoró el ataque del Nodo 3 y aseguró la inmutabilidad.")
    except asyncio.TimeoutError:
        print("\n[❌] ERROR CRÍTICAL: El quórum falló o el nodo bizantino disipó el sistema.")
        print(f" Votos Prepare Leader: {leader.prepare_votes.get(dummy_hash, set())}")
        print(f" Votos Commit Leader: {leader.commit_votes.get(dummy_hash, set())}")
    finally:
        for node in nodes:
            await node.stop()

if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.append(str(Path.cwd() / "1_Operaciones_Activas"))
    asyncio.run(main())
