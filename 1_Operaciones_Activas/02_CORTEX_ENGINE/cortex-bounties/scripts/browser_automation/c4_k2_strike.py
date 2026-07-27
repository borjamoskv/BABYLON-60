import ast
#!/usr/bin/env python3
"""
CODE4RENA K2 LENDING STRIKE — CDP Invisible Maestro
Target: Code4rena bug submission form for K2 Lending
Report: H-03 Close Factor Bypass via Direct KineticRouter Liquidation Call
Status: C5-REAL
"""
import asyncio
import json
import urllib.request
import urllib.error
import base64

CHROME_DEBUG_PORT = 9229

TITLE = "[H-03] Close Factor Bypass via Direct KineticRouter Liquidation Call"

REPORT_BODY = """## Severity
High

## Description
The K2 Lending protocol implements a `close_factor` (typically 50%) to limit the amount of debt that can be liquidated in a single transaction. To enforce this, the protocol uses a dedicated `LiquidationEngine` contract that tracks cumulative liquidations for a user in the current transaction using `USER_LIQUIDATED_THIS_TX`.

However, a vulnerability exists because the `KineticRouter` contract exposes a public `liquidation_call` function that performs the actual liquidation but **does not enforce or update the cumulative liquidation tracking**. Furthermore, this function is `pub` and lacks any caller restrictions, allowing anyone to bypass the `LiquidationEngine` entirely.

In `contracts/kinetic-router/src/liquidation.rs`:
```rust
pub fn liquidation_call(
    env: Env,
    liquidator: Address,
    collateral_asset: Address,
    debt_asset: Address,
    user: Address,
    debt_to_cover: u128,
    _receive_a_token: bool,
) -> Result<(), KineticRouterError> {
    liquidator.require_auth(); // Only checks the liquidator's signature

    internal_liquidation_call(
        &env,
        liquidator,
        collateral_asset,
        debt_asset,
        user,
        debt_to_cover,
        _receive_a_token,
    )
}
```

The `internal_liquidation_call` only calls `validate_close_factor`, which checks if the *current* `debt_to_cover` is within the limit of the *current* debt balance:

```rust
pub(crate) fn validate_close_factor(
    env: &Env,
    health_factor: u128,
    individual_debt_base: u128,
    individual_collateral_base: u128,
    debt_to_cover_base: u128,
) -> Result<(), KineticRouterError> {
    // ...
    let max_liquidatable_debt = individual_debt_base
        .checked_mul(close_factor)
        .div(BASIS_POINTS_MULTIPLIER);

    if debt_to_cover_base > max_liquidatable_debt {
        return Err(KineticRouterError::LiquidationAmountTooHigh);
    }
    Ok(())
}
```

Because `KineticRouter` does not track the `USER_LIQUIDATED_THIS_TX` state (which resides in the `LiquidationEngine` contract's storage), an attacker can call `KineticRouter.liquidation_call` multiple times in a single transaction. Each call will reduce the user's debt, and the subsequent call will allow liquidating 50% of the *new, reduced* debt balance. By repeating this process in a loop within a single transaction, a liquidator can seize nearly 100% of a borrower's collateral, bypassing the intended 50% close factor protection.

## Impact
Malicious liquidators can liquidate nearly 100% of a borrower's position in a single transaction, leading to excessive collateral loss and violating the protocol's risk management guarantees.

## Proof of Concept
1. **Setup:** User A has $1000 debt. `close_factor` is 50%.
2. **Step 1:** Attacker calls `KineticRouter.liquidation_call` directly with `debt_to_cover` = $500 (50% of $1000).
3. **Result 1:** Debt is reduced to $500. Seized $500 worth of collateral (+ bonus).
4. **Step 2:** Attacker calls `KineticRouter.liquidation_call` again in the same TX with `debt_to_cover` = $250 (50% of the *remaining* $500).
5. **Result 2:** Debt is reduced to $250.
6. **Iteration:** Attacker continues until the remaining debt is negligible or the collateral is exhausted.
7. **Bypass:** The `LiquidationEngine`'s tracking of `USER_LIQUIDATED_THIS_TX` is never invoked, so it never blocks the subsequent calls.

## Recommended Mitigation
Restrict `KineticRouter.liquidation_call` so that it can only be called by the authorized `LiquidationEngine` contract. This ensures that all liquidations must pass through the `LiquidationEngine`, where the cumulative close factor enforcement is correctly implemented."""


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

    async def type_text(self, selector: str, text: str):
        escaped = text.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        await self.eval(f"""
            (function() {{
                const el = document.querySelector('{selector}');
                if (el) {{
                    el.focus();
                    const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value') ? 
                                   Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set :
                                   Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
                    if(setter) {{
                        setter.call(el, `{escaped}`);
                    }} else {{
                        el.value = `{escaped}`;
                    }}
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

    async def close(self):
        if self.ws:
            await self.ws.close()


async def strike():
    print("\n" + "═" * 60)
    print("  K2 LENDING — CODE4RENA STRIKE [CDP INVISIBLE]")
    print("═" * 60 + "\n")

    # Discover tabs
    with urllib.request.urlopen(f"http://localhost:{CHROME_DEBUG_PORT}/json") as r:
        tabs = json.loads(r.read())

    # Find the active Code4rena tab
    c4_tabs = [t for t in tabs if "code4rena.com" in t.get("url", "")]
    if not c4_tabs:
        print("[STRIKE] ❌ No Code4rena tab found. Open the contest submission page first.")
        return

    # Use the first one or prioritize submission pages
    target = next((t for t in c4_tabs if "submit" in t.get("url", "")), c4_tabs[0])
    print(f"[STRIKE] Attaching to tab: {target['url'][:80]}")

    session = CDPSession(target["webSocketDebuggerUrl"])
    await session.connect()
    await asyncio.sleep(1)

    # Take initial screenshot
    await session.screenshot("/tmp/c4_strike_0_initial.png")

    if "submit" not in target.get("url", ""):
        print("[STRIKE] ⚠️ Currently not on a '/submit' URL. Please navigate to the contest submission form.")
        await session.close()
        return

    print("[STRIKE] Step 1: Injecting Title...")
    await session.type_text("input[name='title'], input[placeholder*='Title']", TITLE)
    await asyncio.sleep(0.5)

    print("[STRIKE] Step 2: Injecting Report Body...")
    escaped_body = REPORT_BODY.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    await session.eval(f"""
        (function() {{
            const ta = document.querySelector('textarea[name="body"], textarea[placeholder*="body"], textarea[placeholder*="details"]');
            if (ta) {{
                ta.focus();
                const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
                if(setter) setter.call(ta, `{escaped_body}`);
                else ta.value = `{escaped_body}`;
                ta.dispatchEvent(new Event('input', {{bubbles:true}}));
                ta.dispatchEvent(new Event('change', {{bubbles:true}}));
            }}
        }})()
    """)
    await asyncio.sleep(0.5)

    print("[STRIKE] Step 3: Setting Severity to High...")
    # C4 usually has a select or radio buttons for severity
    await session.eval("""
        (function() {
            // Try select
            const sel = document.querySelector('select[name="risk"], select[name="severity"]');
            if (sel) {
                for(let i=0; i<sel.options.length; i++) {
                    if (sel.options[i].text.includes('High')) {
                        sel.selectedIndex = i;
                        sel.dispatchEvent(new Event('change', {bubbles:true}));
                        return;
                    }
                }
            }
            // Try radio/buttons
            const items = document.querySelectorAll('input[type="radio"], button, label');
            for(const item of items) {
                if (item.textContent.trim() === 'High Risk' || item.value === '3') { // 3 usually means high in C4
                    item.click();
                    return;
                }
            }
        })()
    """)
    await asyncio.sleep(1)

    await session.screenshot("/tmp/c4_strike_1_filled.png")

    print("\n" + "═" * 60)
    print("  CODE4RENA STRIKE — FORM POPULATED")
    print("  Screenshots: /tmp/c4_strike_*.png")
    print("  ⚠️  STOPPED BEFORE FINAL SUBMIT — Manual review required")
    print("═" * 60 + "\n")

    await session.close()


if __name__ == "__main__":
    asyncio.run(strike())
