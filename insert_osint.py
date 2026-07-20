import asyncio
from pathlib import Path
from babylon60.bft.ledger_actor import BFTLedgerActor, LedgerEvent

async def main():
    payload = {
        "Target": "https://www.youtube.com/@oscarrivas2828",
        "PPI_Reality_Score": 5,
        "Exergy_Payload": {
            "Primitivas_Extraidas": [
                "Nombre Registrado: Oscar Rivas",
                "Identificador Handle: @oscarrivas2828",
                "Channel ID Físico: UCMoUxWpRFaiaoF_qr10gFig",
                "Timestamp Ignición: 2013-07-01",
                "Avatar Hash (SHA256): 4f9e6986d3d5b44a900a278b0ce3d871823ff323bf3639e955a4ef1ab461b967"
            ],
            "Invariantes_Detectadas": [
                "Canal de consumo pasivo o inactivo; entropía pública nula (0 videos).",
                "Ausencia de metadatos secundarios.",
                "No hay snapshots en Wayback Machine."
            ],
            "Ruido_Purgado_Porcentaje": "100%"
        },
        "Handoff_Status": "AUTODIDACT-OMEGA (Triggered)"
    }
    
    actor = BFTLedgerActor(Path("cortex_osint.db"))
    await actor.start()
    
    event = LedgerEvent(
        stream="osint_scrapes",
        entity_id="oscarrivas2828",
        event_type="OSINT_EXTRACTION",
        payload=payload,
        cortex_taint="borjamoskv:osint_extractor:goal",
        source_db="cortex_osint.db",
        source_table="osint",
        source_pk="oscarrivas2828"
    )
    
    future = actor.append(event)
    result = await future
    print(f"Ledger Result: {result}")
    
    is_valid = await actor.verify_chain()
    print(f"Chain Verified: {is_valid}")
    
    await actor.stop()

if __name__ == "__main__":
    asyncio.run(main())
