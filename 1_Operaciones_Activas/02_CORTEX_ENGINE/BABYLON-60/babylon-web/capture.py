# C5-REAL EXERGY CERTIFIED
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("http://localhost:4321", wait_until="networkidle")
        await page.screenshot(path="screenshot.png", full_page=True)
        print("Screenshot captured to screenshot.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
