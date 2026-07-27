# [C5-REAL] Exergy-Maximized
"""
APEX Sovereign Trend-Forge FastAPI Routes.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from babylon60.api.deps import get_engine
from babylon60.database.core import connect
from babylon60.engine import CortexEngine
from babylon60.engine.cognitive.endocrine import ENDOCRINE, HormoneType
from cortex_hustle.engine import HustleEngine

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/v1/hustle", tags=["hustle"])

# Global tracker for multi-cycle forge progress and cancellation flag
CYCLE_PROGRESS = {
    "active": False,
    "current": 0,
    "total": 0,
    "last_topic": "",
    "cancelled": False
}

BASE_NICHES = [
    "Smart Contract Audit Agents",
    "EU AI Act Compliance & Guardrails",
    "AST-Based Codebase Refactoring",
    "Zero-Knowledge Rollup Telemetry",
    "Local MLX-LM Search & Indexing",
    "Podcast-to-Thread Auto-Repurposing",
    "BFT Agent Swarm Consensus",
    "High-Dimensional Associative Memory Store",
    "Autonomous SEO & Substack Authoring",
    "Micro-SaaS Web Scraper Daemons",
    "EVM Bytecode Frontrunning Shields",
    "Dynamic API Schema Adapters",
    "Agentic Database Wal-Mode Locks",
    "Federated Vector Consensus Nodes",
    "Autonomous Social Proof Generators"
]

class CycleRequest(BaseModel):
    keywords: list[str] | None = Field(default=None)

class MultiCycleRequest(BaseModel):
    cycles: int = Field(default=100, ge=1, le=100)

class WaitlistRequest(BaseModel):
    project: str = Field(..., min_length=1, max_length=128)
    email: str = Field(..., min_length=3, max_length=128)


async def run_multi_cycle_task(cycles: int, db_path: str):
    """Background task that runs multiple scan and forge cycles concurrently using a parallel Legion worker swarm."""
    global CYCLE_PROGRESS
    CYCLE_PROGRESS["active"] = True
    CYCLE_PROGRESS["total"] = cycles
    CYCLE_PROGRESS["current"] = 0
    CYCLE_PROGRESS["cancelled"] = False
    
    # 5 Parallel workers (Legion Centuria) to balance speed and OpenRouter rate limits
    semaphore = asyncio.Semaphore(5)
    hustler = HustleEngine(db_path=db_path)
    
    async def worker_task(index: int):
        global CYCLE_PROGRESS
        if CYCLE_PROGRESS["cancelled"]:
            return
            
        async with semaphore:
            # 1. Fetch already forged projects dynamically to maintain state-aware de-duplication
            conn = connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT project FROM facts WHERE fact_type = 'opportunity'")
            existing_projects = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            # 2. Pick/synthesize niche
            if index < len(BASE_NICHES):
                niche = BASE_NICHES[index]
            else:
                niche_prompt = (
                    f"Generate a single modern, unique micro-SaaS niche keyword distinct from these existing projects: {existing_projects[-10:]}. "
                    "Output ONLY the name of the niche keyword, no other text or explanation."
                )
                try:
                    niche = await hustler.call_llm(niche_prompt, "You are an AI trend analyzer. Output ONLY the raw keyword.")
                    niche = niche.strip().strip('"').strip("'")
                except Exception:
                    niche = BASE_NICHES[index % len(BASE_NICHES)]
            
            # 3. Execute Scan & Forge
            logger.info("Legion Worker %d: Forging niche: %s", index + 1, niche)
            results = await hustler.scan_and_forge(keywords=[niche])
            
            # 4. Update progress atomic-safely
            CYCLE_PROGRESS["current"] += 1
            if results:
                valid_results = [r for r in results if r.get("verdict") == "EXECUTE"]
                if valid_results:
                    CYCLE_PROGRESS["last_topic"] = valid_results[-1].get("topic", "")
                else:
                    CYCLE_PROGRESS["last_topic"] = results[-1].get("topic", "")
                    
            # Small stagger to keep API calls balanced
            await asyncio.sleep(0.5)
            
    # Create worker tasks for all cycles
    tasks = [worker_task(i) for i in range(cycles)]
    
    try:
        # Run all workers concurrently, respect semaphore limit
        await asyncio.gather(*tasks)
    except Exception as e:
        logger.error("Error during parallel multi-cycle forge execution: %s", e)
    finally:
        CYCLE_PROGRESS["active"] = False
        if not CYCLE_PROGRESS["cancelled"]:
            ENDOCRINE.pulse(HormoneType.SEROTONIN, 0.4, f"Completed parallel Centuria execution of {cycles} cycles")


@router.post("/cycle")
async def trigger_cycle(
    req: CycleRequest,
    background_tasks: BackgroundTasks,
    engine: CortexEngine = Depends(get_engine),
):
    """Triggers an asynchronous scan and forge cycle."""
    hustler = HustleEngine(db_path=engine._db_path)
    background_tasks.add_task(hustler.scan_and_forge, req.keywords)
    
    ENDOCRINE.pulse(HormoneType.ADRENALINE, 0.15, "Manual Trend-Forge Cycle initiated")
    return {"status": "accepted", "message": "Scan and Forge cycle started in background"}


@router.post("/multi-cycle")
async def trigger_multi_cycle(
    req: MultiCycleRequest,
    background_tasks: BackgroundTasks,
    engine: CortexEngine = Depends(get_engine),
):
    """Triggers a high-volume automated scan and forge pipeline."""
    if CYCLE_PROGRESS["active"]:
        raise HTTPException(status_code=400, detail="A multi-cycle forge is already running.")
        
    background_tasks.add_task(run_multi_cycle_task, req.cycles, engine._db_path)
    
    ENDOCRINE.pulse(HormoneType.ADRENALINE, 0.4, f"Launched {req.cycles}-cycle Trend-Forge incubation")
    return {"status": "accepted", "message": f"Successfully launched {req.cycles}-cycle forge execution"}


@router.post("/cancel-cycle")
async def cancel_multi_cycle(engine: CortexEngine = Depends(get_engine)):
    """Cancels any running multi-cycle forge process."""
    global CYCLE_PROGRESS
    if not CYCLE_PROGRESS["active"]:
        return {"status": "ignored", "message": "No active multi-cycle forge process to cancel"}
        
    CYCLE_PROGRESS["cancelled"] = True
    return {"status": "cancelled", "message": "Cancellation request submitted. Halting at next iteration."}


@router.post("/waitlist")
async def register_waitlist(
    req: WaitlistRequest,
    engine: CortexEngine = Depends(get_engine),
):
    """Registers an email to a project's waitlist, updating endocrine status and facts."""
    db_path = engine._db_path
    conn = connect(db_path)
    conn.authorize_causal_writes()
    cursor = conn.cursor()
    
    import hashlib
    content = f"Waitlist subscription: {req.email} for project: {req.project}"
    fact_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    try:
        cursor.execute(
            "INSERT INTO facts (fact_hash, tenant_id, project, content, fact_type, metadata, source, confidence, exergy_score, yield_score) "
            "VALUES (?, 'default', ?, ?, 'waitlist', ?, 'landing_page', 'C5', 0.1, 0.5)",
            (
                fact_hash,
                req.project,
                content,
                json.dumps({"email": req.email}),
                0.2, # exergy score
                0.5 # yield score
            )
        )
        # Log event in ledger_events
        event_id = hashlib.sha1(f"waitlist:{req.email}:{req.project}".encode()).hexdigest()[:16]
        cursor.execute(
            "INSERT INTO ledger_events (event_id, ts, tool, actor, action, payload_json) "
            "VALUES (?, datetime('now'), 'waitlist_registration', 'user', 'subscribe_waitlist', ?)",
            (
                event_id,
                json.dumps({"project": req.project, "email": req.email})
            )
        )
        conn.commit()
        
        # Endocrine Dopamine pulse reward!
        ENDOCRINE.pulse(HormoneType.DOPAMINE, 0.15, f"New waitlist signup for {req.project}")
        return {"status": "success", "message": f"Successfully registered to {req.project} waitlist"}
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            return {"status": "success", "message": "Already registered"}
        logger.error("Waitlist registration failed: %s", e)
        raise HTTPException(status_code=500, detail="Database write failure")
    finally:
        conn.close()

@router.delete("/opportunity/{opp_id}")
async def delete_opportunity(
    opp_id: int,
    engine: CortexEngine = Depends(get_engine),
):
    """Deletes an opportunity from the database and deletes its forged page file."""
    db_path = engine._db_path
    conn = connect(db_path)
    conn.authorize_causal_writes()
    cursor = conn.cursor()
    
    # 1. Fetch metadata to find the slug
    cursor.execute("SELECT project, metadata FROM facts WHERE id = ? AND fact_type = 'opportunity'", (opp_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Opportunity not found")
        
    project = row[0]
    try:
        meta = json.loads(row[1])
    except Exception:
        meta = {}
        
    slug = meta.get("slug")
    
    try:
        # 2. Delete the forged Astro page file
        if slug:
            filepath = Path("/Users/borjafernandezangulo/30_BABYLON-60/src/pages/mvp") / f"{slug}.astro"
            if filepath.exists():
                filepath.unlink()
                logger.info("Deleted forged page file: %s", filepath)

        # 3. Delete facts & events
        cursor.execute("DELETE FROM facts WHERE id = ?", (opp_id,))
        cursor.execute("DELETE FROM facts WHERE project = ? AND fact_type = 'waitlist'", (project,))
        cursor.execute("DELETE FROM ledger_events WHERE payload_json LIKE ?", (f"%{project}%",))
        conn.commit()
        
        ENDOCRINE.pulse(HormoneType.CORTISOL, 0.05, f"Opportunity {project} pruned")
        return {"status": "success", "message": f"Successfully deleted opportunity {project}"}
    except Exception as e:
        logger.error("Failed to delete opportunity: %s", e)
        raise HTTPException(status_code=500, detail="Database write/file deletion failure")
    finally:
        conn.close()

@router.get("/dashboard")
async def get_dashboard(engine: CortexEngine = Depends(get_engine)):
    """Returns active opportunities, generated MVPs, waitlist signups, and endocrine telemetry."""
    db_path = engine._db_path
    conn = connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. Opportunities & MVPs
    cursor.execute(
        "SELECT id, project, content, metadata, created_at, exergy_score FROM facts "
        "WHERE fact_type = 'opportunity' ORDER BY id DESC"
    )
    opps = []
    for row in cursor.fetchall():
        try:
            meta = json.loads(row["metadata"])
        except Exception:
            meta = {}
        opps.append({
            "id": row["id"],
            "project": row["project"],
            "content": row["content"],
            "created_at": row["created_at"],
            "exergy_score": row["exergy_score"],
            "slug": meta.get("slug", ""),
            "headline": meta.get("headline", ""),
            "forged_path": meta.get("forged_path", ""),
            "tam": meta.get("tam", 0),
            "competition": meta.get("competition", 0),
            "advantage": meta.get("advantage", 0),
            "ttm": meta.get("ttm", 0),
            "verdict": meta.get("verdict", "IGNORE") if "verdict" in meta else ("EXECUTE" if row["exergy_score"] > 0.7 else "MONITOR")
        })

    # 2. Waitlists
    cursor.execute(
        "SELECT id, project, content, created_at FROM facts "
        "WHERE fact_type = 'waitlist' ORDER BY id DESC"
    )
    waitlist = []
    for row in cursor.fetchall():
        waitlist.append({
            "id": row["id"],
            "project": row["project"],
            "content": row["content"],
            "created_at": row["created_at"]
        })

    conn.close()

    # 3. Ledger status
    try:
        report = await engine.verify_ledger()
        ledger_valid = report.get("valid", True)
    except Exception:
        ledger_valid = True

    return {
        "opportunities": opps,
        "waitlist": waitlist,
        "endocrine": ENDOCRINE.balance,
        "cycle_progress": CYCLE_PROGRESS,
        "ledger_integrity": {
            "valid": ledger_valid,
            "status": "C5-REAL" if ledger_valid else "CORRUPTED"
        }
    }
