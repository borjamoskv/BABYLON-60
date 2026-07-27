# C5-REAL EXERGY CERTIFIED
import asyncio
from pathlib import Path
import subprocess

class BlockchainAnchor:
    """
    Nivel L5: Atestación criptográfica inmutable.
    Interconecta el hash terminal consolidado de la malla PBFT con los calendarios
    distribuidos de OpenTimestamps (anclaje final en Bitcoin).
    """
    __slots__ = ("storage_dir",)

    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def anchor_hash(self, entry_hash: str) -> str:
        """
        Envía el hash L4 consolidado a OpenTimestamps de forma asíncrona.
        Retorna la ruta del archivo .ots temporal/parcial generado.
        """
        ots_file = self.storage_dir / f"{entry_hash}.ots"
        if ots_file.exists():
            return str(ots_file)

        print(f"[🔗 L5 ANCHOR] Elevando hash terminal {entry_hash[:16]}... a OpenTimestamps...")

        data_file = self.storage_dir / f"{entry_hash}.txt"

        def _execute_ots():
            try:
                # Escribimos el string del hash SHA3 como data pura.
                # 'ots stamp' generará un sello SHA256 sobre este archivo de texto.
                data_file.write_text(entry_hash)

                # Invocación directa a la CLI ots (aislada del event loop)
                subprocess.run(
                    ["ots", "stamp", str(data_file)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True
                )

                ots_generated = self.storage_dir / f"{entry_hash}.txt.ots"
                if ots_generated.exists():
                    ots_generated.rename(ots_file)

                print(f"[✅ L5 ANCHOR] Sello OTS (Pending) persistido en {ots_file.name}")
                return str(ots_file)
            except Exception as e:
                print(f"[❌ L5 ANCHOR] Fricción en OTS (Letargo de Red): {e}")
                return ""
            finally:
                if data_file.exists():
                    data_file.unlink()

        return await asyncio.to_thread(_execute_ots)
