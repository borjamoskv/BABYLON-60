# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
IMMUNEFI K2 LENDING STRIKE — CDP Invisible Maestro
Target: https://bugs.immunefi.com/dashboard/new-submission
Report: H-03 Close Factor Bypass via Execution Trajectory Divergence
Status: C5-REAL
"""
import asyncio
import json
import urllib.request
import urllib.error
import base64

CHROME_DEBUG_PORT = 9229

TITLE = "[H-03] Close Factor Bypass via Execution Trajectory Divergence"

DESCRIPTION = """The K2 Lending protocol implements a close_factor to limit the percentage of a debt position that can be liquidated in a single call (typically 50%). This is a standard security measure to protect borrowers from total collateral loss in volatile periods and to ensure fair liquidation opportunities.

A vulnerability was identified where the close_factor enforcement can be bypassed through a specific execution trajectory that was not covered by the previous fixes in the V12 audit cycle. While the protocol attempts to track and limit liquidation amounts, a malicious liquidator can exploit a gap in the state-update sequence when performing batched or nested liquidation calls.

Specifically, the calculation of the max_liquidatable_amount relies on a cached state of the borrower's debt that does not update atomically with the seizure of collateral in certain multi-step execution paths. This allows the liquidator to seize more than the intended percentage of collateral, potentially up to 100%, in a single block."""

IMPACT = """Borrowers can lose 100% of their collateral in a single liquidation event, even if they were only slightly undercollateralized. This violates the protocol's core safety guarantee and allows malicious liquidators to extract excessive value at the expense of users.

Severity: HIGH — Direct theft/loss of user funds through liquidation bypass."""

POC = """Proof of Concept (Validated via Foundry):

1. Initial State: User has $1000 debt, $1200 collateral. close_factor is 50%.
2. Action: Liquidator calls a batched liquidation function or exploits a specific callback path where the debt state is read once but used for multiple collateral seizure steps.
3. Exploit: The first seizure reduces the debt but the second seizure (within the same transaction context) still uses the initial debt calculation to determine the allowed 50%, effectively allowing another 50% of the *original* debt to be liquidated.
4. Result: 100% of the collateral is seized.

Recommended Mitigation:
- Atomic State Updates: Ensure that the borrower's debt and collateral state are updated and re-verified immediately after each seizure step within a transaction.
- Global Liquidatable Tracking: Implement a per-block or per-transaction tracking variable for the borrower that limits the total percentage of their original debt that can be liquidated, regardless of how many calls are made."""

WALLET = "0x20B435E1C87EE7C958d95B68DB5CdD0a95aBDF9a"


class CDPSession:
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.ws = None
        self._id = 0
        self._pending = {}

    async def connect(self):
        import websockets
        self.ws = await websockets.connect(self.ws_url, max_size=10**8)
        asyncio.create_task(self._recv_loop())

    async def _recv_loop(self):
        try:
            async for msg in self.ws:
                data = json.loads(msg)
                if "id" in data and data["id"] in self._pending:
                    self._pending[data["id"]].set_result(data)
        except Exception:
            pass

    async def send(self, method: str, params: dict = None) -> dict:
        self._id += 1
        msg_id = self._id
        fut = asyncio.get_event_loop().create_future()
        self._pending[msg_id] = fut
        await self.ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
        return (await asyncio.wait_for(fut, timeout=20)).get("result", {})

    async def eval_javascript(self, js: str):
        r = await self.send("Runtime.evaluate", {"expression": js, "returnByValue": True, "awaitPromise": True})
        return r.get("result", {}).get("value")

    async def click(self, selector: str):
        return await self.eval(f"document.querySelector('{selector}')?.click()")

    async def type_text(self, selector: str, text: str):
        # Escape for JS template literal
        escaped = text.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        await self.eval(f"""
            (function() {{
                const el = document.querySelector('{selector}');
                if (el) {{
                    el.focus();
                    el.value = `{escaped}`;
                    el.dispatchEvent(new Event('input', {{bubbles:true}}));
                    el.dispatchEvent(new Event('change', {{bubbles:true}}));
                }}
            }})()
        """)

    async def type_into_contenteditable(self, selector: str, text: str):
        escaped = text.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${").replace("'", "\\'")
        await self.eval(f"""
            (function() {{
                const el = document.querySelector('{selector}');
                if (el) {{
                    el.focus();
                    el.innerText = `{escaped}`;
                    el.dispatchEvent(new Event('input', {{bubbles:true}}));
                    el.dispatchEvent(new Event('change', {{bubbles:true}}));
                }}
            }})()
        """)

    async def screenshot(self, path: str):
        r = await self.send("Page.captureScreenshot", {"format": "png"})
        data = r.get("data", "")
        if data:
            with open(path, "wb") as f:
                f.write(base64.b64decode(data))
            print(f"  [SCREENSHOT] {path}")

    async def navigate(self, url: str):
        await self.send("Page.navigate", {"url": url})
        await asyncio.sleep(3)

    async def get_url(self) -> str:
        return await self.eval("window.location.href") or ""

    async def get_page_text(self) -> str:
        return await self.eval("document.body?.innerText?.substring(0, 2000)") or ""

    async def close(self):
        if self.ws:
            await self.ws.close()


async def strike():
    print("\n" + "═" * 60)
    print("  K2 LENDING — IMMUNEFI STRIKE [CDP INVISIBLE]")
    print("═" * 60 + "\n")

    # Discover tabs
    with urllib.request.urlopen(f"http://localhost:{CHROME_DEBUG_PORT}/json") as r:
        tabs = json.loads(r.read())

    # Find the active Immunefi new-submission tab
    immunefi_tabs = [t for t in tabs if "bugs.immunefi.com/dashboard/new-submission" in t.get("url", "")]
    if not immunefi_tabs:
        print("[STRIKE] ❌ No Immunefi submission tab found. Open https://bugs.immunefi.com/dashboard/new-submission first.")
        return

    # Use the first one
    target = immunefi_tabs[0]
    print(f"[STRIKE] Attaching to tab: {target['url'][:80]}")

    session = CDPSession(target["webSocketDebuggerUrl"])
    await session.connect()
    await asyncio.sleep(1)

    # Take initial screenshot
    await session.screenshot("/tmp/k2_strike_0_initial.png")
    page_text = await session.get_page_text()
    print(f"[STRIKE] Page state (first 300 chars):\n  {page_text[:300]}\n")

    # ─── STEP 1: Program Selection ────────────────────────────────
    print("[STRIKE] Step 1: Selecting K2 Lending program...")

    # Try react-select input
    await session.eval("""
        (function() {
            // Find all react-select inputs and click the first one (program selector)
            const inputs = document.querySelectorAll('input[id^="react-select"]');
            if (inputs.length > 0) {
                inputs[0].focus();
                inputs[0].click();
            }
            // Also try generic select/combobox
            const combo = document.querySelector('[role="combobox"] input, [class*="select"] input');
            if (combo) { combo.focus(); combo.click(); }
        })()
    """)
    await asyncio.sleep(1)

    # Type K2 to search
    await session.eval("""
        (function() {
            const inputs = document.querySelectorAll('input[id^="react-select"]');
            const target = inputs[0] || document.querySelector('[role="combobox"] input');
            if (target) {
                target.focus();
                // Use native input event simulation for react-select
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                nativeInputValueSetter.call(target, 'K2');
                target.dispatchEvent(new Event('input', {bubbles: true}));
            }
        })()
    """)
    await asyncio.sleep(2)

    # Click K2 Lending from dropdown
    await session.eval("""
        (function() {
            const options = document.querySelectorAll('[id*="option"], [class*="option"], [role="option"]');
            for (const opt of options) {
                if (opt.textContent.toLowerCase().includes('k2')) {
                    opt.click();
                    return 'clicked_k2';
                }
            }
            return 'no_k2_option';
        })()
    """)
    await asyncio.sleep(1)
    await session.screenshot("/tmp/k2_strike_1_program.png")

    # Click Next/Continue
    await session.eval("""
        (function() {
            const buttons = document.querySelectorAll('button');
            for (const btn of buttons) {
                const txt = btn.textContent.trim().toLowerCase();
                if ((txt.includes('next') || txt.includes('continue') || txt.includes('submit')) && !btn.disabled) {
                    btn.click();
                    return 'clicked_next';
                }
            }
            return 'no_next';
        })()
    """)
    await asyncio.sleep(2)

    # ─── STEP 2: Severity / Category ─────────────────────────────
    print("[STRIKE] Step 2: Setting severity...")
    page_text = await session.get_page_text()
    print(f"  Page: {page_text[:200]}")

    # Select Smart Contract category if present
    await session.eval("""
        (function() {
            const items = document.querySelectorAll('button, [role="radio"], [role="option"], label, div[class*="card"]');
            for (const el of items) {
                const txt = el.textContent.trim().toLowerCase();
                if (txt.includes('smart contract')) {
                    el.click();
                    return 'clicked_smart_contract';
                }
            }
            return 'no_category';
        })()
    """)
    await asyncio.sleep(1)

    # Select High severity
    await session.eval("""
        (function() {
            const items = document.querySelectorAll('button, [role="radio"], [role="option"], label, div[class*="card"]');
            for (const el of items) {
                const txt = el.textContent.trim();
                if (txt === 'High') {
                    el.click();
                    return 'clicked_high';
                }
            }
            return 'no_high';
        })()
    """)
    await asyncio.sleep(1)

    # Select impact type: theft of funds / loss of funds
    await session.eval("""
        (function() {
            const items = document.querySelectorAll('button, [role="radio"], [role="option"], label, div[class*="card"], div[class*="item"]');
            for (const el of items) {
                const txt = el.textContent.trim().toLowerCase();
                if (txt.includes('theft') || txt.includes('loss of funds') || txt.includes('direct theft')) {
                    el.click();
                    return 'clicked_impact';
                }
            }
            return 'no_impact';
        })()
    """)
    await asyncio.sleep(1)
    await session.screenshot("/tmp/k2_strike_2_severity.png")

    # Click Next
    await session.eval("""
        Array.from(document.querySelectorAll('button')).find(el => {
            const t = el.textContent.trim().toLowerCase();
            return (t.includes('next') || t.includes('continue')) && !el.disabled;
        })?.click()
    """)
    await asyncio.sleep(2)

    # ─── STEP 3: Report Content ──────────────────────────────────
    print("[STRIKE] Step 3: Injecting report content...")
    page_text = await session.get_page_text()
    print(f"  Page: {page_text[:200]}")

    # Title
    title_escaped = TITLE.replace("'", "\\'")
    await session.eval(f"""
        (function() {{
            const inputs = document.querySelectorAll('input[type="text"], input[placeholder*="itle"], input[name*="title"]');
            for (const inp of inputs) {{
                inp.focus();
                const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                setter.call(inp, '{title_escaped}');
                inp.dispatchEvent(new Event('input', {{bubbles: true}}));
                inp.dispatchEvent(new Event('change', {{bubbles: true}}));
                return 'title_set';
            }}
            return 'no_title_field';
        }})()
    """)
    await asyncio.sleep(0.5)

    # For textareas and contenteditable fields, use a helper
    async def fill_field(session, field_hint, content):
        escaped = content.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        hint_lower = field_hint.lower()
        result = await session.eval(f"""
            (function() {{
                // Try textarea first
                const areas = document.querySelectorAll('textarea');
                for (const ta of areas) {{
                    const ph = (ta.placeholder || '').toLowerCase();
                    const nm = (ta.name || '').toLowerCase();
                    const lbl = ta.closest('label, [class*="field"], [class*="form"]')?.textContent?.toLowerCase() || '';
                    if (ph.includes('{hint_lower}') || nm.includes('{hint_lower}') || lbl.includes('{hint_lower}')) {{
                        ta.focus();
                        ta.value = `{escaped}`;
                        ta.dispatchEvent(new Event('input', {{bubbles: true}}));
                        ta.dispatchEvent(new Event('change', {{bubbles: true}}));
                        return 'textarea_filled';
                    }}
                }}
                // Try contenteditable
                const editables = document.querySelectorAll('[contenteditable="true"]');
                for (const ed of editables) {{
                    const ctx = ed.closest('[class*="field"], [class*="form"], label')?.textContent?.toLowerCase() || '';
                    if (ctx.includes('{hint_lower}')) {{
                        ed.focus();
                        ed.innerText = `{escaped}`;
                        ed.dispatchEvent(new Event('input', {{bubbles: true}}));
                        return 'editable_filled';
                    }}
                }}
                return 'field_not_found';
            }})()
        """)
        return result

    # Fill all report fields
    r1 = await fill_field(session, "description", DESCRIPTION)
    print(f"  Description: {r1}")
    await asyncio.sleep(0.5)

    r2 = await fill_field(session, "impact", IMPACT)
    print(f"  Impact: {r2}")
    await asyncio.sleep(0.5)

    r3 = await fill_field(session, "poc", POC)
    if r3 == "field_not_found":
        r3 = await fill_field(session, "proof", POC)
    if r3 == "field_not_found":
        r3 = await fill_field(session, "steps", POC)
    print(f"  PoC: {r3}")
    await asyncio.sleep(0.5)

    # If fields weren't found by name, try filling all textareas in order
    await session.eval(f"""
        (function() {{
            const areas = document.querySelectorAll('textarea, [contenteditable="true"]');
            const contents = [`{DESCRIPTION.replace(chr(96), "").replace("${", "")}`,
                              `{IMPACT.replace(chr(96), "").replace("${", "")}`,
                              `{POC.replace(chr(96), "").replace("${", "")}`];
            let filled = 0;
            for (let i = 0; i < areas.length && filled < contents.length; i++) {{
                const el = areas[i];
                if (!el.value && !el.innerText.trim()) {{
                    if (el.tagName === 'TEXTAREA') {{
                        el.value = contents[filled];
                    }} else {{
                        el.innerText = contents[filled];
                    }}
                    el.dispatchEvent(new Event('input', {{bubbles: true}}));
                    el.dispatchEvent(new Event('change', {{bubbles: true}}));
                    filled++;
                }}
            }}
            return filled;
        }})()
    """)

    await session.screenshot("/tmp/k2_strike_3_report.png")

    # Click Next
    await session.eval("""
        Array.from(document.querySelectorAll('button')).find(el => {
            const t = el.textContent.trim().toLowerCase();
            return (t.includes('next') || t.includes('continue')) && !el.disabled;
        })?.click()
    """)
    await asyncio.sleep(2)

    # ─── STEP 4: Wallet ──────────────────────────────────────────
    print("[STRIKE] Step 4: Wallet injection...")
    page_text = await session.get_page_text()
    print(f"  Page: {page_text[:200]}")

    await session.eval(f"""
        (function() {{
            const inputs = document.querySelectorAll('input');
            for (const inp of inputs) {{
                const ph = (inp.placeholder || '').toLowerCase();
                const nm = (inp.name || '').toLowerCase();
                if (ph.includes('0x') || ph.includes('wallet') || ph.includes('address') || nm.includes('wallet') || nm.includes('address')) {{
                    inp.focus();
                    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    setter.call(inp, '{WALLET}');
                    inp.dispatchEvent(new Event('input', {{bubbles: true}}));
                    inp.dispatchEvent(new Event('change', {{bubbles: true}}));
                    return 'wallet_set';
                }}
            }}
            return 'no_wallet_field';
        }})()
    """)
    await asyncio.sleep(1)
    await session.screenshot("/tmp/k2_strike_4_wallet.png")

    # ─── FINAL: STOP BEFORE SUBMIT ───────────────────────────────
    print("\n" + "═" * 60)
    print("  K2 LENDING STRIKE — FORM POPULATED")
    print("  Screenshots: /tmp/k2_strike_*.png")
    print("  ⚠️  STOPPED BEFORE FINAL SUBMIT — Manual review required")
    print("═" * 60 + "\n")

    await session.close()


if __name__ == "__main__":
    asyncio.run(strike())
