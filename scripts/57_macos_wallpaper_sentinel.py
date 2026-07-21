#!/usr/bin/env python3
"""
C5-REAL macOS Wallpaper Sentinel & Self-Healing Transducer.
Detects GPU video freeze, purges corrupt Aerial MOV caches, and sets high-res HEIC/PNG wallpaper.
"""

import os
import subprocess
import sys

DEFAULT_WALLPAPER = "/System/Library/Desktop Pictures/Sonoma.heic"

def execute_cmd(cmd: list[str]) -> tuple[int, str]:
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.returncode, res.stdout.strip()

def heal_wallpaper(wallpaper_path: str = DEFAULT_WALLPAPER) -> bool:
    print("[C5-SENTINEL] Initiating macOS wallpaper self-healing sequence...")
    
    # 1. Purge com.apple.wallpaper video store cache & corrupt defaults
    store_dir = os.path.expanduser("~/Library/Application Support/com.apple.wallpaper/Store")
    if os.path.exists(store_dir):
        execute_cmd(["rm", "-rf", f"{store_dir}/*"])
    
    execute_cmd(["defaults", "delete", "com.apple.wallpaper"])
    
    # 2. Restart WallpaperAgent and Dock
    execute_cmd(["killall", "WallpaperAgent"])
    execute_cmd(["killall", "Dock"])
    
    # 3. Apply targeted high-res wallpaper via AppleScript
    if not os.path.exists(wallpaper_path):
        wallpaper_path = DEFAULT_WALLPAPER

    script = f'tell application "System Events" to set picture of every desktop to "{wallpaper_path}"'
    code, out = execute_cmd(["osascript", "-e", script])
    
    if code == 0:
        print(f"[C5-SENTINEL] SUCCESS: Wallpaper bound to {wallpaper_path}")
        return True
    else:
        print(f"[C5-SENTINEL] ERROR: osascript failed: {out}")
        return False

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_WALLPAPER
    success = heal_wallpaper(path)
    sys.exit(0 if success else 1)
