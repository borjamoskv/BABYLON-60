# C5-REAL EXERGY CERTIFIED
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path.cwd() / "1_Operaciones_Activas"))

import nacl.signing
from cortex.core.bft_swarm import BFTNode
from cortex.core.l5_opentimestamps import BlockchainAnchor

async def main():
    print("[🛡️] CONFIGURANDO ENJAMBRE L4 Y ANCLAJE L5 (OpenTimestamps)")
    node_ids = ["node_0", "node_1", "node_2", "node_3"]

    keys = {nid: nacl.signing.SigningKey.generate() for nid in node_ids}
    pubkeys = {nid: bytes(keys[nid].verify_key) for nid in node_ids}

    nodes = []

    l5_dir = Path("l5_anchors")
    anchor = BlockchainAnchor(l5_dir)

    for name in node_ids:
        peers = {k: 9001 + i for i, k in enumerate(node_ids) if k != name}
        port = 9001 + node_ids.index(name)
        node = BFTNode(
            name, port, peers, is_primary=(name == "node_0"),
            private_key_bytes=bytes(keys[name]),
            peer_pubkeys=pubkeys
        )
        if name == "node_0":
            node.l5_anchor = anchor

        nodes.append(node)
        await node.start()

    print("[🟢] Malla TCP L4 activa. Preparando inyección de anclaje L5...")

    leader = nodes[0]
    test_future = asyncio.get_running_loop().create_future()

    dummy_hash = "6a4e81cc4cdf4fbc94c20876adfb42a2" # Fake SHA3
    print(f"\n[🎯] Líder proponiendo bloque terminal: {dummy_hash}...")
    await leader.propose_block(seq=1, entry_hash=dummy_hash, taint="user:l5_ots_test", future=test_future)

    try:
        await asyncio.wait_for(test_future, timeout=3.0)
        print("\n[✅] Consenso L4 garantizado. Esperando asincronía L5 (3s)...")
        # Damos tiempo a que el subprocess de OTS resuelva
        await asyncio.sleep(3.0)

        ots_file = l5_dir / f"{dummy_hash}.ots"
        if ots_file.exists():
            print(f"[💥] INVARIANTE L5 CONFIRMADA: {ots_file.name} (Tamaño: {ots_file.stat().st_size} bytes)")
        else:
            print("[❌] ERROR: OTS no fue generado.")

    except asyncio.TimeoutError:
        print("\n[❌] ERROR CRÍTICAL: El quórum falló.")
    finally:
        for node in nodes:
            await node.stop()

if __name__ == "__main__":
    asyncio.run(main())
