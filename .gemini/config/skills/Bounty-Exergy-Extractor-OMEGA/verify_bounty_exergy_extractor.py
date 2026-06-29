# [C5-REAL] Exergy-Maximized
import asyncio
import logging
import sys

# Ensure cortex is in path
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../30_CORTEX")))

from cortex.engine.forensic.bounty_extractor import BountyExergyExtractor

logging.basicConfig(level=logging.INFO)

async def run_extraction():
    extractor = BountyExergyExtractor(target_source="immunefi")
    report = await extractor.run()
    
    if report.get("status") == "no_targets":
        print("No targets extracted.")
        sys.exit(0)
        
    print("\n==============================================")
    print("🔥 [OMEGA-SKILL] BOUNTY EXTRACTION SUCCESSFUL 🔥")
    print("==============================================")
    for mission_name, data in report["mission_results"].items():
        print(f" -> Mission: {mission_name} | Agents: {data['agents']} | Confidence: {data['confidence']:.2f}")
    
    sys.exit(0)

if __name__ == "__main__":
    asyncio.run(run_extraction())
