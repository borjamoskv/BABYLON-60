# [C5-REAL] Exergy-Maximized
"""
cat_id: check-hook
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""

import asyncio

from google.antigravity import Agent, types
from google.antigravity.connections.local import LocalAgentConfig
from google.antigravity.hooks import hooks


@hooks.pre_turn
async def my_hook(data):
    with open("hook_output.txt", "w") as f:
        f.write(f"TYPE: {type(data)}\nDIR: {dir(data)}\nDATA: {data}")
    return types.HookResult(allow=False)


async def main():
    config = LocalAgentConfig(model="gemini-2.5-pro", hooks=[my_hook])
    async with Agent(config) as agent:
        await agent.chat("cortex --force-sync origin")


asyncio.run(main())
