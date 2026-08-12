import asyncio
import aiohttp
import time
import uuid

BASE_URL = "http://localhost:8000"
NUM_AGENTS = 1000
SEMAPHORE_LIMIT = 500  # FastAPI+asyncpg handles up to 200 concurrent DB threads perfectly, but we can push Uvicorn concurrency to 500

async def swarm_agent_lifecycle(session, agent_index, semaphore, success_tracker):
    async with semaphore:
        # Each agent generates a strictly isolated identity
        agent_id = f"legion_agent_{uuid.uuid4().hex[:8]}"
        user_id = "legion_commander"
        
        # 1. Store localized memory
        memories = [
            f"Agent {agent_index} objective: Secure sector 7G",
            f"Agent {agent_index} telemetry: Online, optimal exergy"
        ]
        
        for mem in memories:
            async with session.post(
                f"{BASE_URL}/memory/add",
                json={"user_id": user_id, "agent_id": agent_id, "content": mem}
            ) as response:
                assert response.status == 200, await response.text()
        
        # 2. Query localized memory
        async with session.post(
            f"{BASE_URL}/memory/query",
            json={"user_id": user_id, "agent_id": agent_id, "query": "What is my current telemetry and objective?", "limit": 2}
        ) as response:
            assert response.status == 200, await response.text()
            data = await response.json()
            
            # Verify correct isolation: this agent should only retrieve its own logs
            for result in data.get("results", []):
                if f"Agent {agent_index}" not in result["content"]:
                    print(f"ISOLATION BREACH! Agent {agent_index} received: {result['content']}")
                    return
            
            success_tracker.append(1)

async def deploy_legion_1000():
    print(f"Deploying Legion Swarm: {NUM_AGENTS} Agents")
    print("Initiating C5-REAL Zero-Ask Execution Protocol...")
    
    start_time = time.perf_counter()
    success_tracker = []
    semaphore = asyncio.Semaphore(SEMAPHORE_LIMIT)
    
    async with aiohttp.ClientSession() as session:
        tasks = [
            asyncio.create_task(swarm_agent_lifecycle(session, i, semaphore, success_tracker))
            for i in range(NUM_AGENTS)
        ]
        await asyncio.gather(*tasks)
        
    total_time = time.perf_counter() - start_time
    success_rate = (len(success_tracker) / NUM_AGENTS) * 100
    
    print("\n--- LEGION 1000 EXECUTION REPORT ---")
    print(f"Total Agents Orchestrated: {NUM_AGENTS}")
    print(f"Total API Operations: {NUM_AGENTS * 3}")  # 2 Add + 1 Query per agent
    print(f"Execution Time: {total_time:.2f} seconds")
    print(f"Effective RPS: {(NUM_AGENTS * 3) / total_time:.2f} req/s")
    print(f"Isolation & Execution Success: {success_rate:.1f}%")

if __name__ == "__main__":
    asyncio.run(deploy_legion_1000())
