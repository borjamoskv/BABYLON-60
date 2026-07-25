import shutil
import subprocess
from pathlib import Path


def run_cmd(cmd: list[str]) -> None:
    print(f"[*] Executing: {' '.join(cmd)}")
    subprocess.run(cmd, capture_output=True, text=True)

def kinetic_purge() -> None:
    run_cmd(['osascript', '-e', 'do shell script "purge"'])
    rogue_daemons = ['studentd', 'mediaanalysisd', 'parsecd', 'CoreDuetd', 'knowledge-agent']
    for daemon in rogue_daemons:
        run_cmd(['killall', '-9', daemon])
    root = Path(__file__).resolve().parent.parent
    caches = [root / '.venv', root / 'strike_rs' / 'target', root / 'target']
    for cache in caches:
        if cache.exists():
            print(f'[*] Wiping cache: {cache}')
            shutil.rmtree(cache, ignore_errors=True)
    for pycache in root.rglob('__pycache__'):
        print(f'[*] Wiping pycache: {pycache}')
        shutil.rmtree(pycache, ignore_errors=True)
    run_cmd(['launchctl', 'setenv', 'CG_PDF_VERBOSE', '1'])
    run_cmd(['launchctl', 'setenv', 'MTL_HUD_ENABLED', '0'])
if __name__ == '__main__':
    kinetic_purge()