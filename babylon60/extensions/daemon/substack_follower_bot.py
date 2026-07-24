import asyncio
import logging
import random
import urllib.parse

from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("CDP-Automata")


async def run_automata():
    """
    Se conecta al puerto CDP 9222 del Chrome del usuario.
    Audita los seguidores en la página actual y hace "Follow".
    """
    try:
        async with async_playwright() as p:
            logger.info("Intentando conectar al navegador local (CDP puerto 9222)...")
            browser = await p.chromium.connect_over_cdp("http://localhost:9222")

            contexts = browser.contexts
            if not contexts:
                logger.error(
                    "No se encontraron contextos de navegador. Abre Chrome con el flag --remote-debugging-port=9222"
                )
                return

            context = contexts[0]
            pages = context.pages

            target_page = None
            for page in pages:
                parsed_url = urllib.parse.urlparse(page.url)
                hostname = parsed_url.hostname or ""
                if hostname == "substack.com" or hostname.endswith(".substack.com"):
                    target_page = page
                    break

            if not target_page:
                target_page = pages[0]
                logger.warning(
                    "No se encontró una URL explícita de Substack. Operando sobre la pestaña activa: %s",
                    target_page.url,
                )

            logger.info("Auditoría activa en la URL: %s", target_page.url)

            logger.info("Escaneando el DOM en busca de oyentes...")

            follow_buttons = await target_page.locator("button:has-text('Follow')").all()
            seguir_buttons = await target_page.locator("button:has-text('Seguir')").all()

            buttons_to_click = follow_buttons + seguir_buttons

            if not buttons_to_click:
                logger.warning("No se encontraron botones de Follow sin pulsar en la vista actual.")
                await target_page.mouse.wheel(0, 1000)
                await asyncio.sleep(2)
            else:
                logger.info("[C5-REAL] Nodos sin seguir detectados: %s", len(buttons_to_click))

                for i, button in enumerate(buttons_to_click):
                    try:
                        if await button.is_visible() and await button.is_enabled():
                            await button.click()
                            logger.info(" -> Nodo %s sincronizado (Followed).", i + 1)

                            await asyncio.sleep(random.uniform(1.2, 3.1))
                        else:
                            logger.info(
                                " -> Nodo %s ignorado (Botón oculto o deshabilitado).", i + 1
                            )
                    except Exception as e:  # noqa: BLE001
                        logger.error("Fricción al sincronizar nodo %s: %s", i + 1, e)

            logger.info("Auditoría de pantalla completada.")
            await browser.close()

    except Exception as e:  # noqa: BLE001
        logger.error("Fallo crítico en el Automata CDP: %s", e)
        logger.info("¿Has iniciado Google Chrome con el puerto abierto en la terminal?")


if __name__ == "__main__":
    asyncio.run(run_automata())
