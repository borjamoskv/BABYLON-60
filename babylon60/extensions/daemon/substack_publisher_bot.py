import asyncio
import logging
import os

from playwright.async_api import async_playwright

from babylon60.extensions.daemon.gmail_magic_link import GmailMagicLinkExtractor

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Cortex.SubstackCDP")


class SubstackPublisherBot:
    """
    [C5-REAL] Inyector de estado en Substack vía Playwright CDP.
    """

    def __init__(self, cdp_url="http://localhost:9222"):
        from urllib.parse import urlparse

        parsed = urlparse(cdp_url)
        hostname = parsed.hostname or ""
        if hostname not in ("localhost", "127.0.0.1", "[::1]"):
            raise ValueError(
                f"[Security Violation] CDP interface must be isolated to loopback. Got: {hostname}"
            )
        self.cdp_url = cdp_url
        self.base_url = "https://substack.com"
        self.publish_url = "https://borjamoskv.substack.com/publish"

    async def inject_essay(self, title: str, markdown_content: str):
        """
        Ejecuta la mutación de estado en el lienzo web.
        """
        try:
            async with async_playwright() as p:
                logger.info("Conectando a Chromium CDP en %s...", self.cdp_url)
                browser = await p.chromium.connect_over_cdp(self.cdp_url)

                context = browser.contexts[0]
                page = await context.new_page()

                logger.info("Navegando al editor: %s", self.publish_url)
                await page.goto(self.publish_url)

                if "login" in page.url or await page.locator("input[name='email']").count() > 0:
                    logger.warning(
                        "Sesión caducada. Desplegando bypass Autodidact (IMAP Magic Link)..."
                    )

                    if await page.locator("input[name='email']").count() > 0:
                        email_input = os.getenv("CORTEX_EMAIL_USER")
                        await page.fill("input[name='email']", email_input)
                        await page.click("button:has-text('Email me a login link')")
                        logger.info(
                            "Petición de Magic Link enviada. Esperando 10 segundos a que llegue..."
                        )
                        await asyncio.sleep(10)

                    extractor = GmailMagicLinkExtractor()
                    magic_link = extractor.extract_latest_magic_link()

                    if not magic_link:
                        logger.error("No se pudo obtener el Magic Link. Misión abortada.")
                        await browser.close()
                        return

                    logger.info("Inyectando Magic Link...")
                    await page.goto(magic_link)
                    await page.wait_for_load_state("networkidle")

                    await page.goto(self.publish_url)

                logger.info("Sesión confirmada. Preparando lienzo...")

                title_locator = page.locator("textarea[placeholder='Title'], h1.editor-title")
                if await title_locator.count() > 0:
                    await title_locator.first.fill(title)

                editor_locator = page.locator(".ProseMirror")
                await editor_locator.click()

                await page.evaluate(
                    """
                    (content) => {
                        const editor = document.querySelector('.ProseMirror');
                        if (editor) {
                            const pre = document.createElement('pre');
                            const code = document.createElement('code');
                            code.textContent = content;
                            pre.appendChild(code);
                            editor.textContent = '';
                            editor.appendChild(pre);
                        }
                    }
                """,
                    markdown_content,
                )

                logger.info("[C5-REAL] Ensayo inyectado en Substack.")

                logger.info(
                    "Estado guardado como Borrador. Pendiente de Aserción Manual para Publish."
                )

                await page.close()
                await browser.disconnect()

        except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError) as e:  # noqa: BLE001
            logger.error("Fallo crítico en CDP Inyector: %s", e)
            raise RuntimeError("C5-REAL Publisher Bot Failed") from e


if __name__ == "__main__":
    pass
