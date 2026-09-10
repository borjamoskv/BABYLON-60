# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ BROWSER CDP NATIVE ENGINE | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
browser_cdp_engine.py — Native Headless Browser CDP Engine for BABYLON-60.
Transduced from CORTEX skills into native Python standard library + async execution.
Provides zero-dependency CDP (Chrome DevTools Protocol) JSON-RPC interaction over WebSockets.
"""

import asyncio
import base64
import json
import logging
import os
import shutil
import subprocess
import tempfile
import urllib.request
from typing import Any, Dict, List, Optional

logger = logging.getLogger("babylon60.kernel.browser_cdp")

try:
    import websockets

    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False
    logger.warning("`websockets` package not found. CDP WebSocket functions will require `websockets`.")


class CDPPage:
    """Represents a single browser tab controlled via Chrome DevTools Protocol (CDP)."""

    def __init__(self, target_id: str, ws_url: str):
        self.target_id = target_id
        self.ws_url = ws_url
        self.ws: Optional[Any] = None
        self._msg_id = 0
        self._pending_requests: Dict[int, asyncio.Future] = {}
        self._event_listeners: Dict[str, List[Any]] = {}
        self._recv_task: Optional[asyncio.Task] = None
        self.network_logs: List[Dict[str, Any]] = []

    async def connect(self, enable_stealth: bool = True):
        """Establish WebSocket connection to the page target."""
        if not HAS_WEBSOCKETS:
            raise RuntimeError("`websockets` package is required for CDPPage communication.")
        self.ws = await websockets.connect(self.ws_url, max_size=50 * 1024 * 1024)
        self._recv_task = asyncio.create_task(self._listen_loop())

        # Enable core domains
        await self.send("Page.enable")
        await self.send("DOM.enable")
        await self.send("Runtime.enable")
        await self.send("Network.enable")

        if enable_stealth:
            await self.apply_stealth_scripts()

    async def apply_stealth_scripts(self):
        """Inject anti-fingerprinting scripts before page scripts execute."""
        stealth_js = """
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        window.chrome = { runtime: {} };
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en', 'es'] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        """
        await self.send("Page.addScriptToEvaluateOnNewDocument", {"source": stealth_js})

    async def _listen_loop(self):
        """Background loop reading WebSocket messages."""
        try:
            async for raw_msg in self.ws:
                msg = json.loads(raw_msg)
                msg_id = msg.get("id")
                if msg_id is not None and msg_id in self._pending_requests:
                    fut = self._pending_requests.pop(msg_id)
                    if not fut.done():
                        if "error" in msg:
                            fut.set_exception(RuntimeError(f"CDP Error {msg['error']}"))
                        else:
                            fut.set_result(msg.get("result", {}))
                elif "method" in msg:
                    method = msg["method"]
                    params = msg.get("params", {})
                    if method == "Network.responseReceived":
                        resp = params.get("response", {})
                        self.network_logs.append(
                            {
                                "url": resp.get("url"),
                                "status": resp.get("status"),
                                "mimeType": resp.get("mimeType"),
                            }
                        )
                    for cb in self._event_listeners.get(method, []):
                        if asyncio.iscoroutinefunction(cb):
                            asyncio.create_task(cb(params))
                        else:
                            cb(params)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.debug("CDP listen loop terminated: %s", e)

    async def send(self, method: str, params: Optional[Dict[str, Any]] = None, timeout: float = 30.0) -> Dict[str, Any]:
        """Send a JSON-RPC command over CDP and return the result."""
        if not self.ws:
            raise RuntimeError("CDPPage is not connected. Call connect() first.")
        self._msg_id += 1
        current_id = self._msg_id
        payload = {"id": current_id, "method": method, "params": params or {}}
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        self._pending_requests[current_id] = fut
        await self.ws.send(json.dumps(payload))
        return await asyncio.wait_for(fut, timeout=timeout)

    async def navigate(self, url: str, wait_until_load: bool = True, timeout: float = 30.0) -> Dict[str, Any]:
        """Navigate tab to the specified URL."""
        if wait_until_load:
            loaded_fut = asyncio.get_running_loop().create_future()

            def _on_load(params):
                if not loaded_fut.done():
                    loaded_fut.set_result(True)

            self.on("Page.loadEventFired", _on_load)
            res = await self.send("Page.navigate", {"url": url}, timeout=timeout)

            # Check if page is already completely loaded
            try:
                ready_state = await self.evaluate("document.readyState")
                if ready_state == "complete":
                    return res
            except Exception as e:
                import logging

                logging.warning(f"CDP ReadyState Error: {e}")

            try:
                await asyncio.wait_for(loaded_fut, timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning("Page load event timed out after %s seconds for %s", timeout, url)
            return res
        else:
            return await self.send("Page.navigate", {"url": url}, timeout=timeout)

    async def evaluate(self, expression: str) -> Any:
        """Evaluate a JavaScript expression in the page context."""
        res = await self.send(
            "Runtime.evaluate", {"expression": expression, "returnByValue": True, "awaitPromise": True}
        )
        result_obj = res.get("result", {})
        if "exceptionDetails" in res:
            raise RuntimeError(f"JS Execution Exception: {res['exceptionDetails']}")
        return result_obj.get("value")

    async def wait_for_selector(self, selector: str, timeout: float = 10.0, poll_interval: float = 0.2) -> bool:
        """Wait for an element matching CSS selector to appear in DOM."""
        end_time = asyncio.get_running_loop().time() + timeout
        js_check = f"Boolean(document.querySelector({json.dumps(selector)}))"
        while asyncio.get_running_loop().time() < end_time:
            if await self.evaluate(js_check):
                return True
            await asyncio.sleep(poll_interval)
        raise TimeoutError(f"Element '{selector}' not found within {timeout}s.")

    async def click(self, selector: str, timeout: float = 10.0) -> bool:
        """Click an element identified by CSS selector using trusted CDP events."""
        await self.wait_for_selector(selector, timeout=timeout)
        js_click = f"""
        (() => {{
            const el = document.querySelector({json.dumps(selector)});
            if (!el) return null;
            el.scrollIntoView({{ block: 'center', inline: 'center' }});
            const rect = el.getBoundingClientRect();
            return {{ x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 }};
        }})()
        """
        coords = await self.evaluate(js_click)
        if not coords:
            return False

        x, y = coords["x"], coords["y"]
        # Dispatch mouse press & release
        await self.send(
            "Input.dispatchMouseEvent", {"type": "mousePressed", "x": x, "y": y, "button": "left", "clickCount": 1}
        )
        await self.send(
            "Input.dispatchMouseEvent", {"type": "mouseReleased", "x": x, "y": y, "button": "left", "clickCount": 1}
        )
        return True

    async def type(self, selector: str, text: str, delay_ms: float = 20.0, timeout: float = 10.0) -> bool:
        """Focus an element and type text using keyboard events."""
        await self.wait_for_selector(selector, timeout=timeout)
        await self.evaluate(f"document.querySelector({json.dumps(selector)}).focus()")
        for char in text:
            await self.send("Input.dispatchKeyEvent", {"type": "keyDown", "text": char})
            await self.send("Input.dispatchKeyEvent", {"type": "keyUp", "text": char})
            if delay_ms > 0:
                await asyncio.sleep(delay_ms / 1000.0)
        return True

    async def get_content(self) -> str:
        """Extract the full HTML content of the page."""
        doc = await self.send("DOM.getDocument", {"depth": -1})
        root_id = doc["root"]["nodeId"]
        html_res = await self.send("DOM.getOuterHTML", {"nodeId": root_id})
        return html_res.get("outerHTML", "")

    async def get_text(self) -> str:
        """Extract plain text of document body."""
        return await self.evaluate("document.body ? document.body.innerText : ''")

    async def extract_links(self) -> List[Dict[str, str]]:
        """Extract all hyper-links from the current document."""
        js = """
        Array.from(document.querySelectorAll('a[href]')).map(a => ({
            href: a.href,
            text: (a.innerText || '').trim() || a.getAttribute('title') || ''
        }))
        """
        return await self.evaluate(js) or []

    async def extract_metadata(self) -> Dict[str, Any]:
        """Extract structured page metadata (Title, OpenGraph, Meta description)."""
        js = """
        (() => {
            const getMeta = (name) => {
                const el = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
                return el ? el.getAttribute('content') : '';
            };
            return {
                title: document.title,
                description: getMeta('description') || getMeta('og:description'),
                ogTitle: getMeta('og:title'),
                ogImage: getMeta('og:image'),
                canonical: (document.querySelector('link[rel="canonical"]') || {}).href || '',
            };
        })()
        """
        return await self.evaluate(js) or {}

    async def screenshot(
        self, path: Optional[str] = None, format: str = "png", quality: Optional[int] = None, full_page: bool = False
    ) -> bytes:
        """Capture a screenshot of the page, supporting full-page capture."""
        if full_page:
            layout = await self.send("Page.getLayoutMetrics")
            content_size = layout.get("contentSize", layout.get("cssContentSize", {}))
            width = content_size.get("width", 1280)
            height = content_size.get("height", 800)
            await self.send(
                "Emulation.setDeviceMetricsOverride",
                {"width": int(width), "height": int(height), "deviceScaleFactor": 1, "mobile": False},
            )

        params: Dict[str, Any] = {"format": format}
        if quality and format in ("jpeg", "webp"):
            params["quality"] = quality

        res = await self.send("Page.captureScreenshot", params)
        data_b64 = res.get("data", "")
        img_bytes = base64.b64decode(data_b64)
        if path:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "wb") as f:
                f.write(img_bytes)
            logger.info("Screenshot saved to %s", path)
        return img_bytes

    async def pdf(self, path: Optional[str] = None) -> bytes:
        """Export page as PDF document."""
        res = await self.send("Page.printToPDF", {"printBackground": True})
        pdf_bytes = base64.b64decode(res.get("data", ""))
        if path:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "wb") as f:
                f.write(pdf_bytes)
            logger.info("PDF saved to %s", path)
        return pdf_bytes

    def on(self, event_name: str, callback: Any):
        """Register an event listener for a CDP event."""
        if event_name not in self._event_listeners:
            self._event_listeners[event_name] = []
        self._event_listeners[event_name].append(callback)

    async def close(self):
        """Close the target page tab and disconnect WebSocket."""
        if self._recv_task and not self._recv_task.done():
            self._recv_task.cancel()
        if self.ws:
            try:
                await self.send("Target.closeTarget", {"targetId": self.target_id})
            except Exception as e:
                import logging

                logging.warning(f"CDP ReadyState Error: {e}")
            await self.ws.close()
            self.ws = None


class BrowserEngine:
    """Sovereign Chrome/Chromium CDP Engine for Headless Automation."""

    def __init__(self, headless: bool = True, remote_debugging_port: int = 0, user_data_dir: Optional[str] = None):
        self.headless = headless
        self.requested_port = remote_debugging_port
        self.port = remote_debugging_port
        self.process: Optional[subprocess.Popen] = None
        self._temp_dir: Optional[tempfile.TemporaryDirectory] = None
        self.user_data_dir = user_data_dir

    def find_chrome_binary(self) -> Optional[str]:
        """Locate Chrome, Chromium, Brave, or Edge executable across platforms."""
        # 1. Environment variable override
        env_path = os.getenv("CHROME_PATH") or os.getenv("CHROMIUM_PATH")
        if env_path and os.path.exists(env_path):
            return env_path

        # 2. PATH search via shutil.which
        for cli_name in ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "brave", "msedge"]:
            path = shutil.which(cli_name)
            if path:
                return path

        # 3. Known absolute path candidates per OS
        candidates = [
            # macOS
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            # Linux
            "/usr/bin/google-chrome",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/snap/bin/chromium",
            # Windows
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%PROGRAMFILES%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return None

    async def launch(self) -> bool:
        """Launch headless/headed Chrome instance with remote debugging enabled."""
        binary = self.find_chrome_binary()
        if not binary:
            logger.warning("No Chrome/Chromium binary found on host system.")
            return False

        if not self.user_data_dir:
            self._temp_dir = tempfile.TemporaryDirectory(prefix="babylon60_cdp_")
            profile_dir = self._temp_dir.name
        else:
            profile_dir = self.user_data_dir

        cmd = [
            binary,
            f"--remote-debugging-port={self.requested_port}",
            "--remote-debugging-address=127.0.0.1",
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-popup-blocking",
            "--disable-extensions",
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--no-sandbox",
        ]
        if self.headless:
            cmd.append("--headless=new")

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            # Detect port deterministically from Chrome's DevToolsActivePort file
            port_file = os.path.join(profile_dir, "DevToolsActivePort")
            for _ in range(40):
                await asyncio.sleep(0.1)
                if os.path.exists(port_file):
                    try:
                        with open(port_file, "r") as f:
                            lines = f.read().splitlines()
                            if lines and lines[0].isdigit():
                                self.port = int(lines[0])
                                ver = await self.get_version_info()
                                logger.info(
                                    "Chrome CDP instance launched successfully on port %d (%s)",
                                    self.port,
                                    ver.get("Browser", "Chrome"),
                                )
                                return True
                    except Exception as e:
                        import logging

                        logging.warning(f"CDP Wait Error: {e}")

            # Fallback HTTP check if DevToolsActivePort file is delayed
            if self.port != 0:
                for _ in range(20):
                    await asyncio.sleep(0.2)
                    ver = await self.get_version_info()
                    if "error" not in ver:
                        logger.info(
                            "Chrome CDP instance ready on port %d (%s)", self.port, ver.get("Browser", "Chrome")
                        )
                        return True

            logger.error("Timed out waiting for Chrome DevToolsActivePort / CDP endpoint.")
            return False
        except Exception as e:
            logger.error("Failed to launch Chrome CDP instance: %s", e)
            return False

    async def get_version_info(self) -> Dict[str, Any]:
        """Fetch version info from CDP HTTP endpoint."""
        url = f"http://127.0.0.1:{self.port}/json/version"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode())
                return data
        except Exception as e:
            return {"error": str(e)}

    async def list_targets(self) -> List[Dict[str, Any]]:
        """List active CDP page targets."""
        url = f"http://127.0.0.1:{self.port}/json/list"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            logger.error("Error listing CDP targets: %s", e)
            return []

    async def new_page(self, url: str = "about:blank") -> CDPPage:
        """Create a new browser tab target and return a connected CDPPage instance."""
        target_url = f"http://127.0.0.1:{self.port}/json/new?{urllib.parse.quote(url)}"
        req = urllib.request.Request(target_url, method="PUT")
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            target_data = json.loads(resp.read().decode())

        ws_url = target_data.get("webSocketDebuggerUrl")
        target_id = target_data.get("id")
        page = CDPPage(target_id=target_id, ws_url=ws_url)
        await page.connect()
        return page

    def close(self):
        """Gracefully terminate browser process and clean temp profile."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
            logger.info("Chrome CDP instance terminated.")

        if self._temp_dir:
            try:
                self._temp_dir.cleanup()
            except Exception as e:
                import logging

                logging.warning(f"CDP ReadyState Error: {e}")
            self._temp_dir = None

    async def __aenter__(self):
        launched = await self.launch()
        if not launched:
            raise RuntimeError("Failed to launch Chrome CDP Engine.")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.close()


async def run_standalone_demo():
    print("[BROWSER_CDP_ENGINE] Running Expanded Standalone Verification...")
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>C5-REAL Sovereign CDP Engine</title>
        <meta name="description" content="Native Headless CDP Browser Automation for BABYLON-60">
        <meta property="og:title" content="CDP Engine SOTA 2026">
    </head>
    <body style="font-family: sans-serif; padding: 20px;">
        <h1>Sovereign Engine Active</h1>
        <p>Testing interaction primitives and structured extraction.</p>
        <form onsubmit="event.preventDefault(); document.getElementById('out').innerText = 'Submitted: ' + document.getElementById('inp').value;">
            <input type="text" id="inp" placeholder="Type text here..." />
            <button type="submit" id="btn">Submit</button>
        </form>
        <div id="out" style="margin-top: 10px; font-weight: bold; color: green;"></div>
        <br/>
        <a href="https://example.com" title="Example Domain">Example Link</a>
    </body>
    </html>
    """
    try:
        async with BrowserEngine(headless=True) as engine:
            ver = await engine.get_version_info()
            print("  [+] Browser Version:", ver.get("Browser", "Unknown"))

            page = await engine.new_page()
            print("  [+] Created CDP page target with anti-fingerprint stealth")

            # 1. Navigate to inline HTML
            data_url = "data:text/html;base64," + base64.b64encode(test_html.encode()).decode()
            await page.send("Page.navigate", {"url": data_url})
            print("  [+] Loaded test HTML page")

            # 2. Extract metadata & links
            meta = await page.extract_metadata()
            print("  [+] Extracted Metadata:", meta.get("title"), "| Description:", meta.get("description"))
            links = await page.extract_links()
            print(f"  [+] Extracted Links ({len(links)}):", links)

            # 3. Interactive typing & clicking
            print("  [+] Typing into input selector '#inp'...")
            await page.type("#inp", "C5-REAL High Exergy Test")
            print("  [+] Clicking submit button '#btn'...")
            await page.click("#btn")

            output_text = await page.evaluate("document.getElementById('out').innerText")
            print("  [+] Form Result DOM Output:", output_text)

            # 4. Screenshot & PDF export
            img_bytes = await page.screenshot(full_page=True)
            print(f"  [+] Full-page Screenshot Captured: {len(img_bytes)} bytes")

            pdf_bytes = await page.pdf()
            print(f"  [+] PDF Document Exported: {len(pdf_bytes)} bytes")

            print(f"  [+] Network Logs Tracked: {len(page.network_logs)} requests")
            await page.close()
            print("[BROWSER_CDP_ENGINE] All Advanced Primitives Verified Successfully!")
    except Exception as e:
        print("[BROWSER_CDP_ENGINE] Verification Error:", e)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_standalone_demo())
