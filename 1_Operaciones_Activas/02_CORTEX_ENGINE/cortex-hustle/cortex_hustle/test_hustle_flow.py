import asyncio
import os

os.environ["CORTEX_NO_TAINT_ENFORCE"] = "1"

from pathlib import Path

from babylon60.database.core import connect
from cortex_hustle.engine import HustleEngine


async def main():
    print("=== Testing APEX Sovereign Trend-Forge ===")
    
    # Initialize engine
    hustler = HustleEngine()
    
    # Let's mock the LLM calls to prevent burning API quota during local test,
    # or let's run it with a simple mock query to verify the engine pipeline works.
    # We can override call_llm temporarily to return mock responses.
    async def mock_call_llm(prompt, sys_instruction=""):
        print(f"Mocking LLM call for prompt length: {len(prompt)}")
        if "suggest exactly 3" in prompt.lower():
            return """[
                {"topic": "LockerGuard AI", "target_audience": "DeFi Protocols", "core_value_prop": "Autonomous security audit agent for EVM smart contracts.", "slug": "lockerguard-ai"}
            ]"""
        elif "evaluate the micro-saas" in prompt.lower():
            return """{
                "tam": 22.5,
                "competition": 20.0,
                "advantage": 21.0,
                "ttm": 18.0,
                "total": 81.5,
                "verdict": "EXECUTE",
                "headline": "Autonomous Smart Contract Protection Agent",
                "description": "Secure your liquidity pools with continuous BFT audit vectors and automated ZK guards.",
                "features": [
                    "Continuous bytecode analysis",
                    "Autonomous transaction frontrunning protection",
                    "Immediate security alerts via Telegram"
                ]
            }"""
        elif "write a fully complete astro landing page" in prompt.lower():
            return """---
import SiteLayout from '../../layouts/SiteLayout.astro';
---
<SiteLayout title="LockerGuard AI - Early Access" description="Autonomous Smart Contract Protection Agent">
  <div class="hero">
    <h1>LockerGuard AI</h1>
    <p>Autonomous Smart Contract Protection Agent</p>
  </div>
</SiteLayout>"""
        return ""

    hustler.call_llm = mock_call_llm
    
    # Run scan & forge
    print("1. Running scan & forge cycle...")
    results = await hustler.scan_and_forge(keywords=["smart contract security"])
    print(f"Results: {results}")
    
    # Assertions
    assert len(results) > 0, "No opportunities processed"
    forged_slug = results[0]["slug"]
    expected_file = Path("/Users/borjafernandezangulo/30_BABYLON-60/src/pages/mvp") / f"{forged_slug}.astro"
    assert expected_file.exists(), f"Astro landing page file {expected_file} was not forged!"
    print(f"✓ Landing page file created at {expected_file}")

    # Check fact insertion
    print("2. Verifying database fact insertions...")
    conn = connect(hustler.db_path)
    conn.authorize_causal_writes()
    cursor = conn.cursor()
    cursor.execute("SELECT project, fact_type, content, exergy_score FROM facts WHERE project = 'LockerGuard AI'")
    rows = cursor.fetchall()
    assert len(rows) > 0, "Fact was not written to database!"
    print(f"✓ Stored opportunity fact in DB: {rows[0]}")
    
    # Clean up generated file so we keep the git tree clean
    if expected_file.exists():
        expected_file.unlink()
        print("✓ Cleaned up generated test page file")
        
    # Delete from DB
    cursor.execute("DELETE FROM facts WHERE project = 'LockerGuard AI'")
    cursor.execute("DELETE FROM ledger_events WHERE payload_json LIKE '%LockerGuard AI%'")
    conn.commit()
    conn.close()
    print("✓ Cleaned up test database facts")
    
    print("\n=== All Trend-Forge local unit tests PASSED! ===")

if __name__ == "__main__":
    asyncio.run(main())
