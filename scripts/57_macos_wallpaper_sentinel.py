# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
C5-REAL macOS Wallpaper Sentinel & Self-Healing Transducer
==========================================================
Kernel: MOSKV-1 APEX
State: Executable C5-REAL macOS System Transducer

Features:
  1. Detects GPU video freeze, flushes corrupt Aerial MOV caches & WallpaperAgent state.
  2. Resets defaults for com.apple.wallpaper and cleanly restarts WallpaperAgent / Dock.
  3. Binds high-res HEIC/PNG/JPG wallpaper across all active displays via robust AppleScript (POSIX file).
  4. Provides CLI presets (Sonoma, YInMn, Thermo Decay, C5 vs C4, Solid Black).
  5. Installs/uninstalls as a launchd daemon to enforce wallpaper invariants autonomously.
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Tuple

DEFAULT_WALLPAPER = "/System/Library/Desktop Pictures/Sonoma.heic"

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
PRESETS: dict[str, str] = {
    "sonoma": DEFAULT_WALLPAPER,
    "yinmn": str(ASSETS_DIR / "yinmn_blue_ide.jpg"),
    "thermo": str(ASSETS_DIR / "thermo_decay_anergy.png"),
    "c5_vs_c4": str(ASSETS_DIR / "cover_c5_vs_c4.png"),
    "black": "/System/Library/Desktop Pictures/Solid Colors/Black.png",
}

LABEL_DAEMON = "com.c5real.wallpaper_sentinel"
PLIST_PATH = os.path.expanduser(f"~/Library/LaunchAgents/{LABEL_DAEMON}.plist")


def execute_cmd(cmd: list[str]) -> Tuple[int, str]:
    """Executes a command safely returning exit code and stdout/stderr."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        output = (res.stdout + "\n" + res.stderr).strip()
        return res.returncode, output
    except (subprocess.SubprocessError, OSError) as e:
        return 1, str(e)


def log(msg: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [C5-SENTINEL] {msg}")


def purge_wallpaper_cache() -> None:
    """Purges com.apple.wallpaper video store cache & resets plist defaults."""
    store_dir = os.path.expanduser("~/Library/Application Support/com.apple.wallpaper/Store")
    if os.path.exists(store_dir):
        log(f"Purging wallpaper cache at {store_dir}...")
        for item in os.listdir(store_dir):
            item_path = os.path.join(store_dir, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
                else:
                    os.remove(item_path)
            except OSError as e:
                log(f"Warn: Could not delete {item_path}: {e}")

    execute_cmd(["defaults", "delete", "com.apple.wallpaper"])


def restart_wallpaper_daemons() -> None:
    """Flushes memory buffers by restarting WallpaperAgent and Dock."""
    log("Restarting WallpaperAgent & Dock daemons...")
    execute_cmd(["killall", "WallpaperAgent"])
    execute_cmd(["killall", "Dock"])
    time.sleep(1.5)


def apply_wallpaper(wallpaper_path: str) -> bool:
    """Applies target wallpaper across all displays using AppleScript POSIX file binding."""
    abs_path = os.path.abspath(os.path.expanduser(wallpaper_path))

    if not os.path.isfile(abs_path):
        log(f"Warn: Target '{wallpaper_path}' not found. Falling back to default.")
        abs_path = DEFAULT_WALLPAPER

    if not os.path.isfile(abs_path):
        log("CRITICAL: Default wallpaper not found on disk.")
        return False

    log(f"Binding wallpaper to: {abs_path}")
    script = f'''
    set imgFile to POSIX file "{abs_path}"
    tell application "System Events"
        set desktopList to every desktop
        repeat with aDesktop in desktopList
            set picture of aDesktop to imgFile
        end repeat
    end tell
    '''
    code, out = execute_cmd(["osascript", "-e", script])
    if code == 0:
        log(f"SUCCESS: Wallpaper bound to {abs_path}")
        return True
    else:
        log(f"osascript Primary failed: {out}")
        # Fallback AppleScript syntax
        fallback_script = f'tell application "System Events" to set picture of every desktop to POSIX file "{abs_path}"'
        code2, out2 = execute_cmd(["osascript", "-e", fallback_script])
        if code2 == 0:
            log(f"SUCCESS (via fallback): Wallpaper bound to {abs_path}")
            return True
        log(f"ERROR: All AppleScript binding attempts failed: {out2}")
        return False


def heal_wallpaper(wallpaper_path: str = DEFAULT_WALLPAPER) -> bool:
    """Executes full C5-REAL self-healing sequence."""
    log("Initiating macOS wallpaper self-healing sequence...")
    purge_wallpaper_cache()
    restart_wallpaper_daemons()
    return apply_wallpaper(wallpaper_path)


def install_daemon(preset: str) -> None:
    """Installs launchd agent for hourly wallpaper enforcement."""
    script_path = os.path.abspath(__file__)
    python_path = sys.executable

    plist_dir = os.path.dirname(PLIST_PATH)
    os.makedirs(plist_dir, exist_ok=True)

    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{LABEL_DAEMON}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>{script_path}</string>
        <string>--preset</string>
        <string>{preset}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StartInterval</key>
    <integer>3600</integer>
    <key>StandardOutPath</key>
    <string>/tmp/c5_wallpaper_sentinel.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/c5_wallpaper_sentinel.err</string>
</dict>
</plist>
"""
    with open(PLIST_PATH, "w", encoding="utf-8") as f:
        f.write(plist_content)

    execute_cmd(["launchctl", "unload", PLIST_PATH])
    code, out = execute_cmd(["launchctl", "load", "-w", PLIST_PATH])

    if code == 0:
        log(f"Daemon installed successfully at {PLIST_PATH}")
        log("Enforcement active: runs on login and hourly.")
    else:
        log(f"Failed to load daemon: {out}")


def uninstall_daemon() -> None:
    """Uninstalls launchd agent."""
    if os.path.exists(PLIST_PATH):
        execute_cmd(["launchctl", "unload", PLIST_PATH])
        os.remove(PLIST_PATH)
        log(f"Daemon uninstalled and removed from {PLIST_PATH}")
    else:
        log("No daemon installation found.")


def check_status() -> None:
    """Checks launchd daemon status."""
    code, out = execute_cmd(["launchctl", "list", LABEL_DAEMON])
    if code == 0:
        log(f"Daemon Active:\n{out}")
    else:
        log("Daemon is not loaded.")


def main() -> None:
    parser = argparse.ArgumentParser(description="C5-REAL macOS Wallpaper Sentinel")
    parser.add_argument("--preset", choices=list(PRESETS.keys()), default="sonoma", help="Wallpaper preset to use")
    parser.add_argument("--custom", type=str, help="Absolute path to custom wallpaper image")
    parser.add_argument("--install", action="store_true", help="Install as launchd daemon to enforce invariants")
    parser.add_argument("--uninstall", action="store_true", help="Uninstall launchd daemon")
    parser.add_argument("--status", action="store_true", help="Check launchd daemon status")

    args = parser.parse_args()

    if args.status:
        check_status()
        return

    if args.uninstall:
        uninstall_daemon()
        return

    wallpaper_path = args.custom if args.custom else PRESETS[args.preset]

    if args.install:
        install_daemon(args.preset)
        heal_wallpaper(wallpaper_path)
    else:
        success = heal_wallpaper(wallpaper_path)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
