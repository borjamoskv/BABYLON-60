#!/usr/bin/env python3
# C5-REAL: MOSKV-1 Kinetic IDE Main Entrypoint
import os
import asyncio
from cortex_bft_ledger import CortexBFTLedger
from shadow_workspace import ShadowWorkspace
from kinetic_loop import KineticEventLoop

class MoskvIdeEngine:
    """
    Orquestador Causal.
    Une el Bucle Cinético (TDAH), el Shadow Workspace (Cursor) y el Ledger BFT (Moskv).
    """
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.ledger = CortexBFTLedger(os.path.join(root_dir, ".cortex_engine.db"))
        self.shadow = ShadowWorkspace(root_dir)
        self.loop = KineticEventLoop(hyperfocus_budget_ms=3000) # Corto para la prueba atómica
        
    async def ignite(self, omni_paste_payload: str):
        print("\n[🚀] INICIANDO MOSKV-1 IDE ENGINE")
        
        # 1. Anclaje Epistémico de la intención cruda del operador
        tx_hash = self.ledger.commit_mutation(omni_paste_payload, agent_id="omni_paste_listener")
        
        # 2. Spawning de la capa de clonado para evaluación sin fricción
        self.shadow.spawn_shadow_tree()
        
        # 3. Activación del Hyperfocus (Bloqueo OS) para procesar la mutación en background
        await self.loop.ignite_hyperfocus()
        
        print(f"[✅] CICLO IDE COMPLETADO. Mutación {tx_hash[:8]} lista para merge asíncrono.")

if __name__ == "__main__":
    pwd = os.path.dirname(os.path.abspath(__file__))
    engine = MoskvIdeEngine(pwd)
    asyncio.run(engine.ignite("Omni-Paste Chaos: Fix all TypeErrors in the ast compiler and add 3 tests"))
