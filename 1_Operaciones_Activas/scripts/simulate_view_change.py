# C5-REAL EXERGY CERTIFIED
import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path.cwd() / "1_Operaciones_Activas"))

import nacl.signing
from cortex.core.view_change import ViewChangeEngine, ViewChangeMessage

async def main():
    print("[🛡️] CONFIGURANDO ENJAMBRE DE DESTITUCIÓN L4-VCH (N=4, f=1, CUÓRUM=3)")
    node_ids = ["node_0", "node_1", "node_2", "node_3"]

    keys = {nid: nacl.signing.SigningKey.generate() for nid in node_ids}
    pubkeys = {nid: keys[nid].verify_key for nid in node_ids}

    engines = {}
    for nid in node_ids:
        peers = [p for p in node_ids if p != nid]
        engines[nid] = ViewChangeEngine(nid, keys[nid], len(node_ids), peers, delta_t=1.0)

    def make_broadcast(sender_id):
        async def _broadcast(msg: ViewChangeMessage):
            for peer_id in engines[sender_id].peers:
                # Simulamos propagación de red
                await asyncio.sleep(0.01)
                await engines[peer_id].receive_view_change(msg, pubkeys[sender_id])
        return _broadcast

    for nid in node_ids:
        engines[nid].broadcast_callback = make_broadcast(nid)

    print("\n[🎯] Fase 1: Funcionamiento normal. El Líder (node_0) emite heartbeat...")
    for nid in node_ids:
        engines[nid].reset_exergy_timer(seq=1)

    # Líder responde a tiempo cancelando el timer
    await asyncio.sleep(0.5)
    print("[🟢] Líder responde. Reiniciando temporizadores de exergía.")
    for nid in node_ids:
        engines[nid].reset_exergy_timer(seq=2)

    print("\n[🔥] Fase 2: Ataque Pasivo. El Líder (node_0) entra en letargo bizantino...")
    # No reiniciamos temporizadores y dejamos que expiren (delta_t = 1.0s)
    await asyncio.sleep(1.5)

    print("\n[✅] RESULTADO FINAL DE LA TOPOLOGÍA L4-VCH:")
    for nid in node_ids:
        print(f" - {nid} | current_view: {engines[nid].current_view} | is_primary: {engines[nid].is_primary}")

if __name__ == "__main__":
    asyncio.run(main())
