#!/usr/bin/env python3
import sys
import os

# Add SDK path to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "../sdk/python"))
from cortex import CortexClient

def mock_llm_response(prompt: str):
    """
    Simulates a smart response to a prompt.
    """
    print("--- Prompt Sent to LLM ---")
    print(prompt)
    print("--------------------------")
    
    # Simple rule-based mock matching the prompt context
    if "distributed systems" in prompt.lower() or "infra" in prompt.lower():
        return "I should suggest focusing on building lock-free queues, ring buffers, and vector storage engines with pgvector."
    return "I recommend starting with a simple FastAPI skeleton."

def main():
    client = CortexClient()
    user_id = "user_42"
    agent_id = "agent_omega"
    
    # 1. Ask a question WITHOUT memory context
    query = "Recommend an engineering project for me to build."
    print(f"[*] Querying WITHOUT memory: '{query}'")
    
    no_mem_prompt = f"User asks: {query}\nProvide a recommendation."
    response = mock_llm_response(no_mem_prompt)
    print(f"\n[Agent Response (Stateless)]:\n{response}\n")
    
    # 2. Add memories to Cortex
    print(f"[*] Adding memories to Cortex for {user_id}...")
    client.add(user_id, agent_id, "User is a senior infrastructure engineer.")
    client.add(user_id, agent_id, "User loves building high-performance lock-free distributed systems.")
    
    # 3. Retrieve memory context for the query
    print(f"\n[*] Querying WITH memory: '{query}'")
    memories = client.query(user_id, query).get("results", [])
    
    # Inject memories into the system/user prompt context
    memory_context = "\n".join([f"- {m}" for m in memories])
    
    mem_prompt = f"""You are an advanced co-pilot.
Below is the retrieved long-term memory of this user:
{memory_context}

User asks: {query}
Provide a tailored recommendation based on their profile."""
    
    response_with_mem = mock_llm_response(mem_prompt)
    print(f"\n[Agent Response (Stateful)]:\n{response_with_mem}\n")

if __name__ == "__main__":
    main()
