#!/usr/bin/env python3
"""
K2 LENDING — Immunefi Navigator to Step 3
CDP-based invisible navigation via existing browser session.
C5-REAL — Zero UI.
"""
import asyncio
import json
import base64

WS_URL = "ws://localhost:9229/devtools/page/3A87A01B8B57CBA2942482BC81F9123C"

class CDPSession:
    def __init__(self, ws_url):
        self.ws_url = ws_url
        self.ws = None
        self._id = 0
        self._pending = {}

    async def connect(self):
        import websockets
        self.ws = await websockets.connect(self.ws_url, max_size=10**8)
        asyncio.create_task(self._recv_loop())

    async def _recv_loop(self):
        async for msg in self.ws:
            data = json.loads(msg)
            if "id" in data and data["id"] in self._pending:
                self._pending[data["id"]].set_result(data)

    async def send(self, method, params=None):
        self._id += 1
        mid = self._id
        fut = asyncio.get_event_loop().create_future()
        self._pending[mid] = fut
        await self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        try:
            result = await asyncio.wait_for(fut, timeout=20)
            return result.get("result", {})
        except asyncio.TimeoutError:
            return {}

    async def ev(self, js):
        r = await self.send("Runtime.evaluate", {
            "expression": js,
            "returnByValue": True,
            "awaitPromise": True
        })
        return r.get("result", {}).get("value")

    async def screenshot(self, path):
        r = await self.send("Page.captureScreenshot", {"format": "png"})
        data = r.get("data", "")
        if data:
            with open(path, "wb") as f:
                f.write(base64.b64decode(data))
            print(f"[SCREENSHOT] {path}")

    async def close(self):
        if self.ws:
            await self.ws.close()


async def main():
    print("=" * 60)
    print("  K2 LENDING — IMMUNEFI CDP NAVIGATOR")
    print("=" * 60)

    s = CDPSession(WS_URL)
    await s.connect()
    print("[CDP] Connected")

    # 1. Audit current state
    url = await s.ev("window.location.href")
    print(f"[STATE] URL: {url}")

    page_html_summary = await s.ev("""
        (function() {
            const h1 = document.querySelector('h1,h2,h3');
            const steps = document.querySelectorAll('[class*="step"], [class*="Step"], [data-step], [role="tabpanel"], [class*="wizard"]');
            const btns = Array.from(document.querySelectorAll('button')).map(b => b.textContent.trim()).filter(t => t.length > 0 && t.length < 50);
            const inputs = document.querySelectorAll('input, textarea, select, [contenteditable]');
            const labels = Array.from(document.querySelectorAll('label')).map(l => l.textContent.trim()).filter(t => t.length > 0 && t.length < 80);
            const links = Array.from(document.querySelectorAll('a')).map(a => a.textContent.trim()).filter(t => t.length > 1 && t.length < 60).slice(0, 20);
            
            // Check for any "step" indicators
            const allText = document.body.innerText;
            const stepMatches = allText.match(/step\\s*\\d/gi) || [];
            
            // Check visible content in main area
            const mainContent = document.querySelector('main, [role="main"], .content, .container');
            const mainText = mainContent ? mainContent.innerText.substring(0, 1000) : document.body.innerText.substring(0, 1000);
            
            return JSON.stringify({
                heading: h1 ? h1.innerText : 'none',
                stepElements: steps.length,
                buttons: btns.slice(0, 15),
                inputCount: inputs.length,
                labels: labels.slice(0, 20),
                links: links,
                stepMatches: stepMatches,
                mainText: mainText.substring(0, 800)
            });
        })()
    """)
    
    print("[STATE] Page audit:")
    try:
        audit = json.loads(page_html_summary)
        print(f"  Heading: {audit.get('heading')}")
        print(f"  Step elements: {audit.get('stepElements')}")
        print(f"  Buttons: {audit.get('buttons')}")
        print(f"  Input count: {audit.get('inputCount')}")
        print(f"  Labels: {audit.get('labels')}")
        print(f"  Step matches: {audit.get('stepMatches')}")
        print("  Main text (first 500):")
        print(f"    {audit.get('mainText','')[:500]}")
    except Exception:
        print(f"  Raw: {page_html_summary}")

    await s.screenshot("/tmp/k2_immunefi_state_01.png")

    # 2. Check if we need to select program first
    # Look for program selector / search
    program_state = await s.ev("""
        (function() {
            // Check for search input for programs
            const searchInputs = Array.from(document.querySelectorAll('input')).filter(el => {
                const ph = (el.placeholder || '').toLowerCase();
                const aria = (el.getAttribute('aria-label') || '').toLowerCase();
                return ph.includes('search') || ph.includes('program') || ph.includes('project') || aria.includes('search');
            });
            
            // Check for program cards/list
            const programItems = document.querySelectorAll('[class*="program"], [class*="project"], [class*="bounty"]');
            
            // Check for any element containing "K2" text
            const allElements = Array.from(document.querySelectorAll('*'));
            const k2Elements = allElements.filter(el => el.children.length === 0 && el.textContent.trim().includes('K2'));
            
            // Check dropdowns
            const selects = document.querySelectorAll('select');
            const selectOptions = Array.from(selects).map(s => Array.from(s.options).map(o => o.text));
            
            return JSON.stringify({
                searchInputs: searchInputs.length,
                searchPlaceholders: searchInputs.map(i => i.placeholder),
                programItems: programItems.length,
                k2Matches: k2Elements.map(el => el.tagName + ':' + el.textContent.trim().substring(0, 50)).slice(0, 5),
                selects: selectOptions
            });
        })()
    """)
    print(f"\n[PROGRAM] State: {program_state}")

    # 3. Try to find and click K2 Lending in the form
    search_result = await s.ev("""
        (function() {
            // Strategy 1: Find search/filter input and type K2
            const inputs = Array.from(document.querySelectorAll('input[type="text"], input[type="search"], input:not([type])'));
            const visible = inputs.filter(el => el.offsetParent !== null);
            
            if (visible.length > 0) {
                const searchInput = visible[0];
                searchInput.focus();
                
                // React-compatible value injection
                const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');
                if (nativeSetter) {
                    nativeSetter.set.call(searchInput, 'K2');
                }
                searchInput.dispatchEvent(new Event('input', {bubbles: true}));
                searchInput.dispatchEvent(new Event('change', {bubbles: true}));
                
                return 'TYPED_K2_IN:' + (searchInput.placeholder || searchInput.id || 'input[0]');
            }
            return 'NO_INPUT_FOUND';
        })()
    """)
    print(f"[SEARCH] {search_result}")
    
    await asyncio.sleep(2)
    await s.screenshot("/tmp/k2_immunefi_state_02.png")
    
    # 4. Look for K2 Lending in results and click it
    click_result = await s.ev("""
        (function() {
            // Find any element containing "K2" that looks clickable
            const all = Array.from(document.querySelectorAll('*'));
            const candidates = all.filter(el => {
                const text = el.textContent.trim();
                return text.includes('K2') && text.length < 100 && el.offsetParent !== null;
            });
            
            // Sort by specificity (fewer children = more specific)
            candidates.sort((a, b) => a.children.length - b.children.length);
            
            const report = candidates.slice(0, 10).map(el => ({
                tag: el.tagName,
                text: el.textContent.trim().substring(0, 60),
                children: el.children.length,
                classes: el.className?.toString().substring(0, 50) || ''
            }));
            
            return JSON.stringify(report);
        })()
    """)
    print(f"[K2 CANDIDATES] {click_result}")
    
    # 5. After audit, try clicking the K2 Lending option
    k2_click = await s.ev("""
        (function() {
            const all = Array.from(document.querySelectorAll('*'));
            // Look for leaf nodes containing exactly "K2 Lending" or "K2"
            const matches = all.filter(el => {
                const text = el.textContent.trim();
                return (text === 'K2 Lending' || text === 'K2' || text.startsWith('K2 Lending'))
                    && el.children.length <= 2
                    && el.offsetParent !== null;
            });
            
            if (matches.length > 0) {
                matches[0].click();
                return 'CLICKED: ' + matches[0].tagName + ' — ' + matches[0].textContent.trim().substring(0, 40);
            }
            
            // Fallback: try dropdown option / role=option
            const opts = Array.from(document.querySelectorAll('[role="option"], [role="listitem"], li, .option'));
            const k2opt = opts.find(el => el.textContent.includes('K2'));
            if (k2opt) {
                k2opt.click();
                return 'CLICKED_OPT: ' + k2opt.textContent.trim().substring(0, 40);
            }
            
            return 'K2_NOT_FOUND';
        })()
    """)
    print(f"[K2 CLICK] {k2_click}")
    
    await asyncio.sleep(2)
    await s.screenshot("/tmp/k2_immunefi_state_03.png")

    # 6. Final state audit
    final_state = await s.ev("""
        (function() {
            const btns = Array.from(document.querySelectorAll('button')).map(b => b.textContent.trim()).filter(t => t.length > 0 && t.length < 50);
            const h = document.querySelector('h1,h2,h3');
            const allText = document.body.innerText.substring(0, 1500);
            return JSON.stringify({
                heading: h ? h.innerText : 'none',
                buttons: btns.slice(0, 15),
                mainText: allText.substring(0, 800)
            });
        })()
    """)
    print(f"\n[FINAL STATE] {final_state}")

    await s.close()
    print("\n" + "=" * 60)
    print("  CDP NAVIGATOR COMPLETE — Check screenshots")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
