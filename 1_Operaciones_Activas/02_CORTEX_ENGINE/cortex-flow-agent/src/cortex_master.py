import asyncio
import os
import sys

from src.browser_worker.playwright_engine import BrowserWorker
from src.mac_worker.hammerspoon_bridge import MacWorker

class CortexFlowAgent:
    def __init__(self, target_url: str):
        self.target_url = target_url
        self.browser = BrowserWorker()
        self.mac = MacWorker()
        # C5-REAL Initialization
        print(f"[CORTEX] C5-REAL Agent Instantiated. Target: {self.target_url}")

    async def execute_flow(self):
        print("[CORTEX] Orchestrating Dual-Worker Protocol...")
        # 1. Mac worker prepares the environment / files
        await self.mac.prepare_assets()
        
        # 2. Browser worker navigates and mutates DOM
        await self.browser.navigate(self.target_url)
        await self.browser.create_project()
        
        print("[CORTEX] Flow execution completed successfully.")

if __name__ == "__main__":
    url = os.environ.get("FLOW_URL", "https://labs.google/fx/tools/image-fx")
    agent = CortexFlowAgent(url)
    asyncio.run(agent.execute_flow())
