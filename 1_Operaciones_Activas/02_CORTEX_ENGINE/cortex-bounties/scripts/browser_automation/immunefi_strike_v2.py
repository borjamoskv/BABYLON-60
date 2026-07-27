import ast
#!/usr/bin/env python3
"""
IMMUNEFI STRIKE v2 — Multi-Step CDP
Target: https://bugs.immunefi.com/dashboard/new-submission
Exactly Protocol VerifiedMarket Delegate Bypass
"""
import asyncio
import json
import urllib.request
import urllib.error
import base64

CHROME_DEBUG_PORT = 9229

TITLE = "Disallowed delegate can keep borrowing from and withdrawing from Base VerifiedMarket after firewall revocation"
SUMMARY = """Disallowed delegates can continue operating Exactly's Base VerifiedMarket after firewall revocation if they were previously approved by an allowlisted user. On current public main (c62bf4ce53f26ea0ca8d7ece2732c84f2b2bfaef), stale market approval remains exploitable on inherited delegated paths because VerifiedMarket does not fully enforce current-caller allowlisting there. In particular, borrow() / borrowAtMaturity() only firewall-check the borrower, not msg.sender or receiver, and withdraw() relies on owner shortfall plus allowance without requiring the delegated spender to remain allowlisted. This lets a revoked delegate both create debt for an allowlisted victim and withdraw an allowlisted owner's assets to an attacker-controlled receiver.

I validated this against a clean public clone of exactly/protocol main with two PoCs: test_poc_disallowedDelegateCanBorrowForAllowedBorrower() and test_poc_disallowedDelegateCanWithdrawFromAllowedOwner(), and both returned Success. The issue affects the in-scope Base MarketUSDC proxy at 0x61EDAcB54aA8a689013682529df8914C87692E4b, whose deployment metadata points to VerifiedMarket. I also scanned the public audit set and did not find a matching public finding. Public repo history strengthens intent rather than weakening it: Exactly merged commit 0e5281e (verified: firewall borrows) and commit bb51de1 (verified: firewall redeem and withdraw), but those changes only covered borrower/owner checks, not revoked delegated spenders. Recommended remediation is to override borrow(), borrowAtMaturity(), withdraw(), and redeem() in VerifiedMarket, require _requireAllowed(msg.sender) on those paths, and require _requireAllowed(receiver) wherever assets can be sent to third parties."""
IMPACT = """This is an authorization bypass with direct economic impact. A revoked delegate can create debt in an allowlisted victim's name and route borrowed funds to itself. A revoked delegate can withdraw an allowlisted owner's assets to itself. The victim does not need to approve any new action after revocation. Borrow victims can be pushed toward liquidation and collateral loss."""
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
        return (await asyncio.wait_for(fut, timeout=20)).get("result", {})

    async def ast.literal_eval(self, js: str):
        r = await self.send("Runtime.evaluate", {"expression": js, "returnByValue": True, "awaitPromise": True})
        return r.get("result", {}).get("value")

    async def click(self, selector: str):
        return await self.eval(f"document.querySelector('{selector}')?.click()")

    async def type_text(self, selector: str, text: str):
        escaped = text.replace("`", "\\`").replace("${", "\\${")
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

    async def screenshot(self, path: str):
        r = await self.send("Page.captureScreenshot", {"format": "png"})
        with open(path, "wb") as f: f.write(base64.b64decode(r.get("data", "")))

async def strike():
    # Discovery
    with urllib.request.urlopen(f"http://localhost:{CHROME_DEBUG_PORT}/json") as r:
        tabs = json.loads(r.read())
    target = next((t for t in tabs if "bugs.immunefi.com" in t["url"]), tabs[0])
    session = CDPSession(target["webSocketDebuggerUrl"])
    await session.connect()

    print("[STRIKE] Step 1: Program Selection")
    await session.click("input[id^='react-select']")
    await session.type_text("input[id^='react-select']", "Exactly")
    await asyncio.sleep(2)
    # Click Exactly from dropdown
    await session.eval("""
        Array.from(document.querySelectorAll('[id^="react-select-"][id$="-option-"]'))
             .find(el => el.textContent.includes('Exactly'))?.click()
    """)
    await asyncio.sleep(1)
    # Check if "MarketUSDC" or similar needs to be selected if asset selector appears
    await session.eval("""
        // If asset selector exists, pick MarketUSDC
        const assetInp = Array.from(document.querySelectorAll('input[id^="react-select"]')).find(el => el.placeholder.includes('Asset'));
        if (assetInp) {
            assetInp.focus();
            assetInp.click();
            // Just pick the first one if it's the only one or search
        }
    """)
    await session.screenshot("/tmp/strike_v2_1_program.png")
    await session.click("button:not([disabled])") # Next button
    await asyncio.sleep(1)

    print("[STRIKE] Step 2: Severity")
    await session.eval("""
        Array.from(document.querySelectorAll('button, [role="radio"], [role="option"]'))
             .find(el => el.textContent.trim() === 'High')?.click()
    """)
    await session.screenshot("/tmp/strike_v2_2_severity.png")
    await session.eval("Array.from(document.querySelectorAll('button')).find(el => el.textContent.includes('Next'))?.click()")
    await asyncio.sleep(1)

    print("[STRIKE] Step 3: Main Report")
    # Title
    await session.type_text("input[placeholder*='Title'], input[name='title']", TITLE)
    # Summary
    await session.type_text("textarea[placeholder*='Summary'], textarea[name*='summary']", SUMMARY)
    # Impact
    await session.type_text("textarea[placeholder*='Impact'], textarea[name*='impact']", IMPACT)
    # Steps
    await session.type_text("textarea[placeholder*='Steps'], textarea[name*='steps']", STEPS)
    await session.screenshot("/tmp/strike_v2_3_report.png")
    await session.eval("Array.from(document.querySelectorAll('button')).find(el => el.textContent.includes('Next'))?.click()")
    await asyncio.sleep(1)

    print("[STRIKE] Step 4: Wallet")
    await session.type_text("input[placeholder*='0x'], input[name*='wallet']", WALLET)
    await session.screenshot("/tmp/strike_v2_4_wallet.png")
    
    print("[STRIKE] COMPLETED. Check /tmp/strike_v2_*.png")
    if session.ws:
        await session.ws.close()

if __name__ == "__main__":
    asyncio.run(strike())
