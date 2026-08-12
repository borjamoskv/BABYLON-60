import asyncio
from babylon60.cortex.cortex_chaos_monad import run_chaos_monad
import json

async def test_attestation():
    with open("scripts/c5_isomorphisms/cancer_isomorphism_pipeline.py", "r") as f:
        payload_code = f.read()

    print("[ORCHESTRATOR] Inyectando payload en la Mónada del Caos (Test Harness)...")
    result = await run_chaos_monad(
        source_code=payload_code,
        frontier_tick="TICK_90f2b3a1_EMPIRICAL",
        timeout_ms=5000
    )

    print("\n[RESULTADO MONADA]")
    print(f"Status: {result.get('status')}")
    
    receipt = result.get('scitt_receipt', {})
    print("\n[RECIBO SCITT / COSE]")
    print(json.dumps(receipt, indent=2))
    
    if result.get('status') == 'Falsified':
        print("\n[DEFENSA] El oráculo interceptó una Falsificación (AssertionError). ¡El agente fue repudiado!")
    elif result.get('status') == 'Success':
        print("\n[ATTESTATION] Éxito. El hash del AST está criptográficamente sellado.")
    else:
        print("\n[ERROR] El script falló o fue bloqueado por seguridad.")
        print(f"Error trace:\n{result.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_attestation())
