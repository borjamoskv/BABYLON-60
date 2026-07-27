import ast
#!/usr/bin/env python3
"""
IMMUNEFI STRIKE — Mac-Control-OMEGA CDP Substrate
Target: https://bugs.immunefi.com/dashboard/new-submission
Wallet: 0x20B435E1C87EE7C958d95B68DB5CdD0a95aBDF9a
Report: Exactly Protocol VerifiedMarket Delegate Bypass
Commit: main@c62bf4c
C5-REAL — Sovereign Submission Engine
"""
import asyncio
import json
import sys
import urllib.request
import urllib.error
import subprocess
from typing import Optional

CHROME_DEBUG_PORT = 9229

TITLE = "Disallowed delegate can keep borrowing from and withdrawing from Base VerifiedMarket after firewall revocation"

SUMMARY = """Disallowed delegates can continue operating Exactly's Base VerifiedMarket after firewall revocation if they were previously approved by an allowlisted user. On current public main (c62bf4ce53f26ea0ca8d7ece2732c84f2b2bfaef), stale market approval remains exploitable on inherited delegated paths because VerifiedMarket does not fully enforce current-caller allowlisting there. In particular, borrow() / borrowAtMaturity() only firewall-check the borrower, not msg.sender or receiver, and withdraw() relies on owner shortfall plus allowance without requiring the delegated spender to remain allowlisted. This lets a revoked delegate both create debt for an allowlisted victim and withdraw an allowlisted owner's assets to an attacker-controlled receiver.

I validated this against a clean public clone of exactly/protocol main with two PoCs: test_poc_disallowedDelegateCanBorrowForAllowedBorrower() and test_poc_disallowedDelegateCanWithdrawFromAllowedOwner(), and both returned Success. The issue affects the in-scope Base MarketUSDC proxy at 0x61EDAcB54aA8a689013682529df8914C87692E4b, whose deployment metadata points to VerifiedMarket. I also scanned the public audit set and did not find a matching public finding. Public repo history strengthens intent rather than weakening it: Exactly merged commit 0e5281e (verified: firewall borrows) and commit bb51de1 (verified: firewall redeem and withdraw), but those changes only covered borrower/owner checks, not revoked delegated spenders. Recommended remediation is to override borrow(), borrowAtMaturity(), withdraw(), and redeem() in VerifiedMarket, require _requireAllowed(msg.sender) on those paths, and require _requireAllowed(receiver) wherever assets can be sent to third parties."""

STEPS = """Borrow branch:
1. Allowlisted user BOB deposits collateral and enters the collateral market.
2. BOB approves attacker on the verified borrow market.
3. Firewall removes attacker from the allowlist.
4. attacker calls borrow(1 ether, attacker, BOB).
5. Assets are transferred to attacker and debt is assigned to BOB.

Withdraw branch:
1. Allowlisted user BOB holds withdrawable balance on the verified market.
2. BOB approves attacker on that market.
3. Firewall removes attacker from the allowlist.
4. attacker calls withdraw(10 ether, attacker, BOB).
5. Assets are transferred to attacker and BOB market balance is reduced.

Validated against: exactly/protocol main at commit c62bf4c"""

WALLET = "0x20B435E1C87EE7C958d95B68DB5CdD0a95aBDF9a"


# ─── CDP SESSION ──────────────────────────────────────────────────────────────

class CDPSession:
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.ws = None
        self._id = 0
        self._pending = {}

    async def connect(self):
        try:
            import websockets
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", "websockets", "-q"])
            import websockets
        self.ws = await websockets.connect(self.ws_url, max_size=10**8)
        asyncio.create_task(self._recv_loop())
        print("[CDP] Connected ✅")

    async def _recv_loop(self):
        async for msg in self.ws:
            data = json.loads(msg)
            if "id" in data and data["id"] in self._pending:
                self._pending[data["id"]].set_result(data)

    async def send(self, method: str, params: dict = None) -> dict:
        self._id += 1
        msg_id = self._id
        fut = asyncio.get_event_loop().create_future()
        self._pending[msg_id] = fut
        await self.ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
        try:
            result = await asyncio.wait_for(fut, timeout=20)
            return result.get("result", {})
        except asyncio.TimeoutError:
            return {}

    async def eval_javascript(self, js: str):
        r = await self.send("Runtime.evaluate", {
            "expression": js,
            "returnByValue": True,
            "awaitPromise": True
        })
        return r.get("result", {}).get("value")

    async def navigate(self, url: str):
        await self.send("Page.navigate", {"url": url})
        await asyncio.sleep(3)

    async def get_url(self) -> str:
        return await self.eval("window.location.href") or ""

    async def get_text(self, selector: str) -> str:
        return await self.eval(f"""
            (function() {{
                const el = document.querySelector('{selector}');
                return el ? el.innerText || el.value : null;
            }})()
        """) or ""

    async def screenshot(self, path: str = "/tmp/immunefi_state.png"):
        r = await self.send("Page.captureScreenshot", {"format": "png"})
        data = r.get("data", "")
        if data:
            import base64
            with open(path, "wb") as f:
                f.write(base64.b64decode(data))
            print(f"[CDP] Screenshot → {path}")
        return data

    async def fill_field(self, selector: str, text: str, label: str = ""):
        """Fill a field using React-compatible value injection."""
        escaped = text.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        result = await self.eval(f"""
            (function() {{
                const el = document.querySelector(`{selector}`);
                if (!el) return 'NOT_FOUND';
                el.focus();
                // React synthetic event injection
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value') ||
                                               Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value');
                if (nativeInputValueSetter) {{
                    nativeInputValueSetter.set.call(el, `{escaped}`);
                }}
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
                el.dispatchEvent(new KeyboardEvent('keydown', {{bubbles: true}}));
                el.dispatchEvent(new KeyboardEvent('keyup', {{bubbles: true}}));
                return 'OK';
            }})()
        """)
        status = "✅" if result == "OK" else "⚠️ " + str(result)
        print(f"[CDP] Field '{label}': {status}")
        return result == "OK"

    async def click(self, selector: str, label: str = "") -> bool:
        result = await self.eval(f"""
            (function() {{
                const el = document.querySelector('{selector}');
                if (el) {{ el.click(); return true; }}
                return false;
            }})()
        """)
        status = "✅" if result else "❌ NOT FOUND"
        print(f"[CDP] Click '{label}': {status}")
        return bool(result)

    async def wait_for(self, selector: str, timeout: int = 15) -> bool:
        for _ in range(timeout * 2):
            exists = await self.eval(f"!!document.querySelector('{selector}')")
            if exists:
                return True
            await asyncio.sleep(0.5)
        print(f"[CDP] ⚠️  Timeout waiting for: {selector}")
        return False

    async def get_all_inputs(self) -> list:
        """Audit all visible input/textarea fields on page."""
        return await self.eval("""
            (function() {
                const inputs = document.querySelectorAll('input, textarea, [contenteditable="true"], [role="textbox"]');
                return Array.from(inputs).map((el, i) => ({
                    index: i,
                    tag: el.tagName,
                    type: el.type || '',
                    id: el.id || '',
                    name: el.name || '',
                    placeholder: el.placeholder || '',
                    ariaLabel: el.getAttribute('aria-label') || '',
                    classes: el.className.substring(0, 60),
                    value: el.value ? el.value.substring(0, 30) : ''
                }));
            })()
        """) or []

    async def close(self):
        if self.ws:
            await self.ws.close()


# ─── CHROME DISCOVERY ─────────────────────────────────────────────────────────

def get_tabs(port: int = CHROME_DEBUG_PORT) -> list:
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/json", timeout=3) as r:
            return json.loads(r.read())
    except (urllib.error.URLError, ConnectionError):
        return []


def find_immunefi_tab(tabs: list) -> Optional[dict]:
    for tab in tabs:
        if "immunefi" in tab.get("url", "").lower() or "bugs.immunefi" in tab.get("url", ""):
            return tab
    return None


# ─── IMMUNEFI FORM AUTOMATION ─────────────────────────────────────────────────

async def audit_page(session: CDPSession):
    """Audit current page state."""
    url = await session.get_url()
    print(f"\n[AUDIT] Current URL: {url}")
    
    inputs = await session.get_all_inputs()
    print(f"[AUDIT] Found {len(inputs)} input fields:")
    for inp in inputs[:20]:
        print(f"  [{inp['index']}] {inp['tag']} type={inp['type']} id='{inp['id']}' "
              f"placeholder='{inp['placeholder'][:40]}' aria='{inp['ariaLabel'][:40]}'")
    
    # Get page title/h1
    h1 = await session.eval("document.querySelector('h1,h2')?.innerText")
    print(f"[AUDIT] Page heading: {h1}")
    
    return inputs


async def fill_immunefi_form(session: CDPSession):
    """Main form fill logic — adapts to discovered field structure."""
    
    url = await session.get_url()
    print(f"\n[STRIKE] URL: {url}")
    
    if "immunefi" not in url:
        print("[STRIKE] Navigating to Immunefi submission...")
        await session.navigate("https://bugs.immunefi.com/dashboard/new-submission")
        await asyncio.sleep(3)
    
    await session.screenshot("/tmp/immunefi_01_initial.png")
    
    # --- Audit all fields ---
    await audit_page(session)
    
    # --- Strategy: Try known Immunefi selectors first, then fallback ---
    
    # 1. Program selector (search for Exactly)
    print("\n[STRIKE] Step 1: Program selector")
    selectors_to_try = [
        "input[id^='react-select']",
        "input[placeholder*='Search']",
        "input[placeholder*='program']",
        "input[placeholder*='Protocol']",
        "input[aria-label*='program']",
        "input[type='search']",
    ]
    program_found = False
    for sel in selectors_to_try:
        exists = await session.eval(f"!!document.querySelector('{sel}')")
        if exists:
            await session.fill_field(sel, "Exactly", "Program Search")
            await asyncio.sleep(2)
            # Click first result
            clicked = await session.eval("""
                (function() {
                    const items = document.querySelectorAll('[role="option"], [id*="-option-"], .dropdown-item, .suggestion-item');
                    if (items.length > 0) { items[0].click(); return items[0].textContent; }
                    return null;
                })()
            """)
            print(f"[STRIKE] Program selection: {clicked}")
            program_found = True
            break
    
    if not program_found:
        print("[STRIKE] ⚠️  Program selector not found")
    
    # Wait for form to expand
    await asyncio.sleep(3)
    await session.screenshot("/tmp/immunefi_02_program.png")
    
    # 2. Title field
    print("\n[STRIKE] Step 2: Title field")
    await session.wait_for("input[name='title'], input[placeholder*='title' i]", timeout=10)
    title_selectors = [
        "input[name='title']",
        "input[placeholder*='title' i]",
        "input[id*='title']",
    ]
    title_filled = False
    for sel in title_selectors:
        exists = await session.eval(f"!!document.querySelector('{sel}')")
        if exists:
            title_filled = await session.fill_field(sel, TITLE, "Title")
            break
    
    if not title_filled:
        print("[STRIKE] ⚠️  Title field not found, attempting fallback")
        await session.eval(f"""
            (function() {{
                const inputs = Array.from(document.querySelectorAll('input[type="text"], input:not([type])'));
                const vis = inputs.filter(el => el.offsetParent !== null && !el.id.includes('react-select'));
                if (vis[0]) {{
                    vis[0].focus();
                    const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');
                    if (nativeSetter) nativeSetter.set.call(vis[0], `{TITLE}`);
                    vis[0].dispatchEvent(new Event('input', {{bubbles: true}}));
                    vis[0].dispatchEvent(new Event('change', {{bubbles: true}}));
                }}
            }})()
        """)
    
    await asyncio.sleep(1)
    
    # 3. Severity selector
    print("\n[STRIKE] Step 3: Severity")
    severity_set = await session.eval("""
        (function() {
            // Try buttons first
            const btns = Array.from(document.querySelectorAll('button'));
            const high = btns.find(el => el.textContent.trim() === 'High');
            if (high) { high.click(); return 'button:High'; }
            
            // Try select element
            const sel = document.querySelector('select[name*="severity"], select[aria-label*="severity" i]');
            if (sel) {
                sel.value = 'High';
                sel.dispatchEvent(new Event('change', {bubbles: true}));
                return 'select:High';
            }
            
            // Try labels/cards
            const labels = Array.from(document.querySelectorAll('label, div[role="radio"], div[role="option"]'));
            const targetLabel = labels.find(el => el.textContent.trim() === 'High');
            if (targetLabel) { targetLabel.click(); return 'label:High'; }
            
            return null;
        })()
    """)
    print(f"[STRIKE] Severity: {severity_set}")
    await asyncio.sleep(1)
    
    # 4. Description / Summary textarea
    print("\n[STRIKE] Step 4: Description/Summary")
    escaped_summary = SUMMARY.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${").replace("\n", "\\n")
    desc_set = await session.eval(f"""
        (function() {{
            const selectors = [
                'textarea[name*="description" i]',
                'textarea[name*="summary" i]',
                'textarea[placeholder*="description" i]',
                'textarea[placeholder*="summary" i]',
                'textarea[aria-label*="description" i]',
                '[contenteditable="true"]',
                '[role="textbox"]',
                'textarea'
            ];
            let target = null;
            for (const s of selectors) {{
                const el = document.querySelector(s);
                if (el && el.offsetParent !== null) {{ target = el; break; }}
            }}
            if (!target) return 'NOT_FOUND';
            target.focus();
            const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value') ||
                                 Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');
            if (nativeSetter) nativeSetter.set.call(target, `{escaped_summary}`);
            target.dispatchEvent(new Event('input', {{bubbles: true}}));
            target.dispatchEvent(new Event('change', {{bubbles: true}}));
            return 'OK:' + target.tagName + ':' + (target.name || target.id || 'anon');
        }})()
    """)
    print(f"[STRIKE] Description: {desc_set}")
    await asyncio.sleep(1)
    
    # 5. Steps / PoC textarea (second textarea)
    print("\n[STRIKE] Step 5: Steps to Reproduce")
    escaped_steps = STEPS.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${").replace("\n", "\\n")
    steps_set = await session.eval(f"""
        (function() {{
            const textareas = Array.from(document.querySelectorAll('textarea, [contenteditable="true"], [role="textbox"]'));
            const visible = textareas.filter(el => el.offsetParent !== null);
            // Use second textarea if available
            const target = visible[1] || visible[0];
            if (!target) return 'NOT_FOUND';
            target.focus();
            const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value') ||
                                 Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');
            if (nativeSetter) nativeSetter.set.call(target, `{escaped_steps}`);
            target.dispatchEvent(new Event('input', {{bubbles: true}}));
            target.dispatchEvent(new Event('change', {{bubbles: true}}));
            return 'OK:' + (target.name || target.id || 'textarea[' + visible.indexOf(target) + ']');
        }})()
    """)
    print(f"[STRIKE] Steps: {steps_set}")
    await asyncio.sleep(1)
    
    # 6. Wallet address field
    print("\n[STRIKE] Step 6: Wallet/Payout address")
    wallet_set = await session.eval(f"""
        (function() {{
            const selectors = [
                'input[name*="wallet" i]',
                'input[name*="address" i]',
                'input[name*="payout" i]',
                'input[placeholder*="wallet" i]',
                'input[placeholder*="0x" i]',
                'input[placeholder*="address" i]',
                'input[aria-label*="wallet" i]',
                'input[aria-label*="address" i]',
                'input[id*="wallet"]',
                'input[id*="address"]',
            ];
            for (const s of selectors) {{
                const el = document.querySelector(s);
                if (el && el.offsetParent !== null) {{
                    el.focus();
                    const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');
                    if (nativeSetter) nativeSetter.set.call(el, '{WALLET}');
                    el.dispatchEvent(new Event('input', {{bubbles: true}}));
                    el.dispatchEvent(new Event('change', {{bubbles: true}}));
                    return 'OK:' + s;
                }}
            }}
            return 'NOT_FOUND';
        }})()
    """)
    print(f"[STRIKE] Wallet: {wallet_set}")
    await asyncio.sleep(1)
    
    # Final screenshot
    await session.screenshot("/tmp/immunefi_03_filled.png")
    
    # Re-audit to confirm values
    print("\n[STRIKE] ═══ FINAL STATE AUDIT ═══")
    final_inputs = await session.get_all_inputs()
    for inp in final_inputs[:15]:
        if inp.get('value'):
            print(f"  [{inp['index']}] {inp['tag']} '{inp['placeholder'][:30]}' → value: '{inp['value']}'")
    
    print("\n[STRIKE] Screenshots saved:")
    print("  /tmp/immunefi_01_initial.png")
    print("  /tmp/immunefi_02_program.png")
    print("  /tmp/immunefi_03_filled.png")
    print("\n[STRIKE] ⚠️  FORM FILLED — NOT SUBMITTED (awaiting sovereign confirmation)")
    
    return True


# ─── MAIN ─────────────────────────────────────────────────────────────────────

async def main():
    print("═" * 60)
    print("  IMMUNEFI STRIKE — Mac-Control-OMEGA CDP")
    print("  Target: Exactly Protocol VerifiedMarket Bypass")
    print(f"  Wallet: {WALLET}")
    print("═" * 60)
    
    # Find Chrome tabs
    tabs = []
    for port in [9229, 9222, 9223, 9224]:
        t = get_tabs(port)
        if t:
            global CHROME_DEBUG_PORT
            CHROME_DEBUG_PORT = port
            tabs = t
            print(f"[CDP] Port {port}: {len(t)} tabs")
            break
    
    if not tabs:
        print("[CDP] ❌ No Chrome debug session. Open Chrome with:")
        print("  open -a 'Google Chrome' --args --remote-debugging-port=9229")
        return
    
    print("[CDP] Tabs found:")
    for t in tabs[:10]:
        print(f"  → {t.get('url', '')[:80]}")
    
    # Find Immunefi tab or use first available
    target = find_immunefi_tab(tabs)
    if target:
        print(f"\n[CDP] Immunefi tab found: {target['url'][:60]}")
    else:
        target = tabs[0]
        print(f"\n[CDP] Using tab: {target.get('url', '')[:60]}")
    
    ws_url = target.get("webSocketDebuggerUrl")
    if not ws_url:
        print("[CDP] ❌ No WebSocket URL for tab")
        return
    
    session = CDPSession(ws_url)
    await session.connect()
    
    success = await fill_immunefi_form(session)
    
    await session.close()
    
    print("\n" + "═" * 60)
    print(f"  STATUS: {'✅ C5-REAL FORM FILLED' if success else '⚠️  PARTIAL'}")
    print("═" * 60)


if __name__ == "__main__":
    asyncio.run(main())
