import sys
import os
import asyncio

# Añadir el directorio kimi_nexus al sys.path para poder importarlo
sys.path.append(os.path.abspath("kimi_nexus"))
from kimi_nexus import kimi_audit

async def main():
    with open("src/manifest.rs", "r") as f:
        code = f.read()
    
    criteria = "Revisa este manifiesto de memoria compartida lock-free y certifica si cumple con los invariantes topológicos C5-REAL. Busca puntos de fricción entrópica, data races no controlados, huecos de existencia o desviaciones del diseño de memoria (64B align/zero-split coherence)."
    
    print("Enviando 'src/manifest.rs' a Kimi K3 para auditoría C5-REAL...")
    result = await kimi_audit(code, criteria)
    print("\n--- RESULTADO DE KIMI K3 ---\n")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
