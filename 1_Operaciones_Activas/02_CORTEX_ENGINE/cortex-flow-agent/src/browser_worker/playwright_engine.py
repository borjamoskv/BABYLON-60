from playwright.async_api import async_playwright
import asyncio

class BrowserWorker:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def start(self):
        self.playwright = await async_playwright().start()
        # C5-REAL: Evitar automatizaciones detectables lanzando Chromium regular con perfil si es posible.
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    async def navigate(self, url: str):
        if not self.page:
            await self.start()
        print(f"[BROWSER] Navegando a {url}")
        await self.page.goto(url, wait_until="networkidle")

    async def create_project(self):
        print("[BROWSER] Creando proyecto en UI...")
        # Lógica abstracta a rellenar con selectores exactos o OCR.
        await asyncio.sleep(1)

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
