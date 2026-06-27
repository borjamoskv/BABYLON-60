import sys
import asyncio
sys.path.append('$CORTEX_ROOT/.gemini/config/skills/Sortu-APEX/scripts')
from sortu import SortuForgeX1000

async def main():
    forge = SortuForgeX1000()
    res = await forge.forge(
        intent="Initialize Shard [0-2000]. Lock lowpass filters and prepare for DOM frame rendering at 100% capacity.",
        skill_name="DOM-Renderer-Omega",
        hours_saved=2.0,
        dependency_depth=1,
        complexity=0.8
    )
    print(f"Status: {res.state}, Exergy: {res.net_exergy}, Reason: {res.abort_reason}")

if __name__ == "__main__":
    asyncio.run(main())
