"""C0001-C0003 regressions: the CDP engine must not leak futures, listeners or child processes.

Uses a fake websocket and a fixture child process; no browser is launched.
"""

import asyncio
import os
import stat

import pytest

from babylon60.kernel.browser_cdp_engine import BrowserEngine, CDPPage


class _SilentSocket:
    """Accepts frames and never answers."""

    def __init__(self, fail_send: bool = False) -> None:
        self.fail_send = fail_send

    async def send(self, _frame: str) -> None:
        if self.fail_send:
            raise ConnectionError("socket cerrado")


def _page(fail_send: bool = False) -> CDPPage:
    page = CDPPage(target_id="t", ws_url="ws://fixture")
    page.ws = _SilentSocket(fail_send=fail_send)
    return page


async def test_c0001_timeout_removes_pending_future():
    page = _page()
    with pytest.raises(asyncio.TimeoutError):
        await page.send("Page.enable", timeout=0.01)
    assert page._pending_requests == {}


async def test_c0001_failed_send_removes_pending_future():
    page = _page(fail_send=True)
    with pytest.raises(ConnectionError):
        await page.send("Page.enable", timeout=0.5)
    assert page._pending_requests == {}


async def test_c0001_cancelled_send_removes_pending_future():
    page = _page()
    task = asyncio.create_task(page.send("Page.enable", timeout=5))
    await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert page._pending_requests == {}


async def test_c0002_successive_navigations_do_not_accumulate_listeners(monkeypatch):
    page = _page()

    async def fake_send(method, params=None, timeout=30.0):
        return {"frameId": "f"}

    async def fake_evaluate(_expression):
        return "complete"

    monkeypatch.setattr(page, "send", fake_send)
    monkeypatch.setattr(page, "evaluate", fake_evaluate)
    for _ in range(3):
        await page.navigate("https://example.invalid/")
    assert page._event_listeners.get("Page.loadEventFired", []) == []


async def test_c0002_failed_navigation_removes_its_listener(monkeypatch):
    page = _page()

    async def failing_send(method, params=None, timeout=30.0):
        raise RuntimeError("navegación rechazada")

    monkeypatch.setattr(page, "send", failing_send)
    with pytest.raises(RuntimeError):
        await page.navigate("https://example.invalid/")
    assert page._event_listeners.get("Page.loadEventFired", []) == []


async def test_c0003_launch_timeout_terminates_its_own_child(tmp_path, monkeypatch):
    # Fixture "browser": ignores its arguments and never writes DevToolsActivePort.
    fake_browser = tmp_path / "fake_browser.sh"
    fake_browser.write_text("#!/bin/sh\nexec sleep 60\n", encoding="utf-8")
    fake_browser.chmod(fake_browser.stat().st_mode | stat.S_IXUSR)

    engine = BrowserEngine(user_data_dir=str(tmp_path / "profile"))
    monkeypatch.setattr(engine, "find_chrome_binary", lambda: str(fake_browser))
    spawned = []
    real_popen = __import__("subprocess").Popen

    def recording_popen(*args, **kwargs):
        proc = real_popen(*args, **kwargs)
        spawned.append(proc)
        return proc

    monkeypatch.setattr("babylon60.kernel.browser_cdp_engine.subprocess.Popen", recording_popen)
    try:
        assert await engine.launch() is False
        assert len(spawned) == 1
        assert spawned[0].poll() is not None, "el proceso hijo sigue vivo tras el timeout de launch"
        assert engine.process is None
    finally:
        for proc in spawned:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
    assert not os.path.exists(f"/proc/{spawned[0].pid}")


def _fake_browser(tmp_path):
    script = tmp_path / "fake_browser.sh"
    script.write_text("#!/bin/sh\nexec sleep 60\n", encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return script


def _recording_popen(monkeypatch, spawned):
    real_popen = __import__("subprocess").Popen

    def recording(*args, **kwargs):
        proc = real_popen(*args, **kwargs)
        spawned.append(proc)
        return proc

    monkeypatch.setattr("babylon60.kernel.browser_cdp_engine.subprocess.Popen", recording)


async def test_c0003_caller_cancellation_terminates_the_child(tmp_path, monkeypatch):
    engine = BrowserEngine(user_data_dir=str(tmp_path / "profile"))
    monkeypatch.setattr(engine, "find_chrome_binary", lambda: str(_fake_browser(tmp_path)))
    spawned = []
    _recording_popen(monkeypatch, spawned)
    try:
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(engine.launch(), timeout=0.3)
        assert len(spawned) == 1
        assert spawned[0].poll() is not None, "C0003: cancelar launch() dejó vivo el proceso hijo"
        assert engine.process is None
    finally:
        for proc in spawned:
            if proc.poll() is None:
                proc.kill()
                proc.wait()


async def test_c0003_failed_second_launch_does_not_kill_the_first_child(tmp_path, monkeypatch):
    engine = BrowserEngine(user_data_dir=str(tmp_path / "profile"))
    first = __import__("subprocess").Popen(["sleep", "60"])
    engine.process = first
    monkeypatch.setattr(engine, "find_chrome_binary", lambda: str(tmp_path / "does-not-exist"))
    try:
        assert await engine.launch() is False
        assert first.poll() is None, "C0003: un launch() fallido mató un proceso que no creó"
    finally:
        first.kill()
        first.wait()
