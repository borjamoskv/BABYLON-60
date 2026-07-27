import subprocess
import asyncio

class MacWorker:
    def __init__(self):
        print("[MAC] MacWorker C5-REAL Bridge Inicializado.")

    async def execute_applescript(self, script: str):
        process = await asyncio.create_subprocess_exec(
            "osascript", "-e", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return stdout.decode(), stderr.decode()

    async def prepare_assets(self):
        print("[MAC] Verificando entorno de archivos locales y buffers...")
        # Ejemplo: Asegurar que Finder no estorba
        await self.execute_applescript('tell application "Finder" to close every window')
        await asyncio.sleep(0.5)

    async def notify(self, message: str):
        script = f'display notification "{message}" with title "CORTEX_FLOW_AGENT"'
        await self.execute_applescript(script)
