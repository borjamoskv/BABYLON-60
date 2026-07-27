import asyncio
import argparse
from playwright.async_api import async_playwright

# [OUROBOROS-A2A] CORTEX to Jules Bridge (Vector 1: CDP Hook)

async def send_to_jules(prompt: str):
    async with async_playwright() as p:
        try:
            # Conecta al navegador físico del usuario vía CDP (Chrome Remote Debugging)
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            
            jules_page = None
            for page in context.pages:
                if "jules.google.com/session/" in page.url:
                    jules_page = page
                    break
                    
            if not jules_page:
                print("❌ ERROR: No se encontró ninguna pestaña de Jules activa.")
                return

            print(f"🔗 [A2A-BRIDGE] Conectado a Jules en: {jules_page.url}")
            
            # Selector heurístico para la caja de texto de Jules (chat input)
            # Nota: Esto puede requerir ajuste dependiendo de la clase exacta del DOM de Jules
            chat_input = jules_page.locator("textarea").first
            
            if await chat_input.count() == 0:
                print("❌ ERROR: No se encontró la caja de entrada de texto en la UI de Jules.")
                return
                
            # Inyectar el payload (Intent)
            print("⚡ Inyectando payload (CORTEX Intent)...")
            await chat_input.fill(prompt)
            
            # Simular presionar Enter para enviar el mensaje
            await chat_input.press("Enter")
            print("✅ Payload transmitido con éxito.")
            
        except Exception as e:
            print(f"❌ Fricción detectada en el puente CDP: {e}")
            print("Asegúrate de haber lanzado Chrome con: --remote-debugging-port=9222")

def main():
    parser = argparse.ArgumentParser(description="A2A Bridge to Jules via CDP")
    parser.add_argument("payload", type=str, help="El mensaje/payload a inyectar en Jules")
    args = parser.parse_args()
    
    asyncio.run(send_to_jules(args.payload))

if __name__ == "__main__":
    main()
