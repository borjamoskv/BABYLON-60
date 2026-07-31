# C5-REAL EXERGY CERTIFIED
import asyncio
from playwright.async_api import async_playwright
import json
import time

async def scrape_notes():
    notes_data = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://substack.com/@victormillan/notes")

        # Scroll to load notes
        for _ in range(15):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1.5)

        # Select all note elements (Substack notes are typically in articles or specific div classes)
        # We will look for elements containing the text or specific data attributes
        note_elements = await page.query_selector_all('div.pencraft.pc-display-flex.pc-flexDirection-column.pc-gap-16')

        for elem in note_elements:
            text = await elem.inner_text()
            if text and "Víctor Millán" in text:
                # Clean up the text
                clean_text = text.strip()
                if clean_text not in [n['text'] for n in notes_data]:
                    notes_data.append({
                        "text": clean_text
                    })

        await browser.close()

    with open("/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/notes_victor.json", "w") as f:
        json.dump(notes_data, f, ensure_ascii=False, indent=2)

    print(f"Scraped {len(notes_data)} notes.")

if __name__ == "__main__":
    asyncio.run(scrape_notes())
