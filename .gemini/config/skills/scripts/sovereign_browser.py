# C5-REAL
# SafeToAutoRun = true

import os
import random
from contextlib import asynccontextmanager
from pathlib import Path


PROFILE_ROOT = Path(os.environ.get(
    "CORTEX_BROWSER_PROFILES",
    Path.home() / ".gemini" / "antigravity" / "browser-sessions"
))


PLATFORM_PROFILES: dict[str, str] = {
    "soundcloud":  "soundcloud",
    "suno":        "suno",
    "whatsapp":    "whatsapp",
    "moltbook":    "moltbook",
    "github":      "github",
    "default":     "default",
}


_UA_POOL = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
]


def profile_dir(platform: str) -> Path:
    key = PLATFORM_PROFILES.get(platform.lower(), "default")
    d = PROFILE_ROOT / key
    d.mkdir(parents=True, exist_ok=True)
    return d


@asynccontextmanager
async def sovereign_context(
    platform: str = "default",
    headless: bool = True,
    viewport: dict | None = None,
    stealth: bool = True,
    extra_args: list[str] | None = None,
):

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise RuntimeError("ERR: playwright missing")

    profile = str(profile_dir(platform))
    vp = viewport or {"width": 1508, "height": 827}
    ua = random.choice(_UA_POOL) if stealth else None

    chromium_args = [
        "--disable-blink-features=AutomationControlled",
        "--no-first-run",
        "--no-default-browser-check",
    ]
    if extra_args:
        chromium_args.extend(extra_args)

    async with async_playwright() as pw:
        ctx = await pw.chromium.launch_persistent_context(
            user_data_dir=profile,
            headless=headless,
            viewport=vp,
            user_agent=ua,
            args=chromium_args,
            ignore_default_args=["--enable-automation"],
        )
        try:
            yield ctx
        finally:
            await ctx.close()


@asynccontextmanager
async def sovereign_page(platform: str = "default", **kwargs):
    async with sovereign_context(platform, **kwargs) as ctx:
        pages = ctx.pages
        page = pages[0] if pages else await ctx.new_page()
        yield page


def list_profiles() -> dict[str, dict]:
    result = {}
    for platform, key in PLATFORM_PROFILES.items():
        d = PROFILE_ROOT / key
        if d.exists():
            size_mb = sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) / 1e6
            result[platform] = {"path": str(d), "size_mb": round(size_mb, 2)}
    return result


if __name__ == "__main__":
    import json
    print(json.dumps(list_profiles(), indent=2))
