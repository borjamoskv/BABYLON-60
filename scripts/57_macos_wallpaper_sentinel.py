#!/usr/bin/env python3
"""
C5-REAL macOS Wallpaper Sentinel & Self-Healing Transducer
==========================================================
Kernel: MOSKV-1 APEX
State: Executable C5-REAL macOS System Transducer

Features:
  1. Purges corrupt Aerial MOV/MP4 caches & WallpaperAgent state in ~/Library/Application Support/com.apple.wallpaper/Store
  2. Resets defaults for com.apple.wallpaper and kills WallpaperAgent / Dock daemons cleanly.
  3. Binds high-res HEIC/PNG/JPG wallpaper across all active displays via osascript + AppleScript JIT compilation.
  4. Supports robust path expansion, fallback defaults, and zero-shell wildcard bugs.
"""

import os
import sys
import shutil
import subprocess
import time
from typing import Tuple, Optional


DEFAULT_WALLPAPER = "/System/Library/Desktop Pictures/Sonoma.heic"
FALLBACK_WALLPAPER = "/System/Library/Desktop Pictures/Graphic.heic"


def execute_cmd(cmd: list[str]) -> Tuple[int, str, str]:
    """Executes a command safely without shell expansion vulnerabilities."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def purge_wallpaper_cache() -> None:
    """Safely purges com.apple.wallpaper store directory using Python filesystem primitives."""
    store_dir = os.path.expanduser("~/Library/Application Support/com.apple.wallpaper/Store")
    if os.path.exists(store_dir):
        print(f"[C5-SENTINEL] Purging wallpaper cache at {store_dir}...")
        for item in os.listdir(store_dir):
            item_path = os.path.join(store_dir, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
                else:
                    os.remove(item_path)
            except OSError as e:
                print(f"[C5-SENTINEL] Warning clearing {item_path}: {e}")

    # Purge plist state
    execute_cmd(["defaults", "delete", "com.apple.wallpaper"])


def restart_wallpaper_daemons() -> None:
    """Restarts WallpaperAgent and Dock daemons to flush memory buffers."""
    print("[C5-SENTINEL] Restarting WallpaperAgent & Dock daemons...")
    execute_cmd(["killall", "WallpaperAgent"])
    execute_cmd(["killall", "Dock"])
    time.sleep(0.5)


def apply_wallpaper(target_path: str) -> bool:
    """Applies target wallpaper across all active displays via System Events osascript."""
    abs_path = os.path.abspath(os.path.expanduser(target_path))

    if not os.path.isfile(abs_path):
        print(f"[C5-SENTINEL] Warning: Target image '{target_path}' not found on disk.")
        if os.path.isfile(DEFAULT_WALLPAPER):
            abs_path = DEFAULT_WALLPAPER
            print(f"[C5-SENTINEL] Falling back to default wallpaper: {abs_path}")
        elif os.path.isfile(FALLBACK_WALLPAPER):
            abs_path = FALLBACK_WALLPAPER
            print(f"[C5-SENTINEL] Falling back to secondary default: {abs_path}")
        else:
            print("[C5-SENTINEL] CRITICAL: No valid wallpaper files found!")
            return False

    print(f"[C5-SENTINEL] Binding wallpaper to: {abs_path}")
    applescript = f'''
    tell application "System Events"
        set desktopCount to count of desktops
        repeat with i from 1 to desktopCount
            set picture of desktop i to "{abs_path}"
        end repeat
    end tell
    '''

    code, out, err = execute_cmd(["osascript", "-e", applescript])
    if code == 0:
        print(f"[C5-SENTINEL] SUCCESS: Wallpaper applied to all active displays ({abs_path}).")
        return True
    else:
        print(f"[C5-SENTINEL] osascript error (code {code}): {err or out}")
        # Fallback simpler single command
        fallback_script = f'tell application "System Events" to set picture of every desktop to "{abs_path}"'
        code2, out2, err2 = execute_cmd(["osascript", "-e", fallback_script])
        if code2 == 0:
            print(f"[C5-SENTINEL] SUCCESS (via fallback script): Wallpaper bound to {abs_path}")
            return True
        print(f"[C5-SENTINEL] ERROR: All AppleScript binding attempts failed.")
        return False


def heal_wallpaper(wallpaper_path: Optional[str] = None) -> bool:
    """Full self-healing pipeline for macOS Wallpaper."""
    print("==========================================================")
    print(" [C5-REAL] macOS Wallpaper Sentinel & Transducer Ignited ")
    print("==========================================================")

    target = wallpaper_path or DEFAULT_WALLPAPER
    purge_wallpaper_cache()
    restart_wallpaper_daemons()
    success = apply_wallpaper(target)

    if success:
        print("[C5-SENTINEL] Transduction Complete — Desktop State Restored (C5-REAL).")
    else:
        print("[C5-SENTINEL] Transduction Failed — Degraded Desktop State.")

    return success


if __name__ == "__main__":
    target_img = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_WALLPAPER
    if target_img == "/ruta/a/tu/imagen.jpg":
        target_img = DEFAULT_WALLPAPER
    
    ok = heal_wallpaper(target_img)
    sys.exit(0 if ok else 1)
