#!/usr/bin/env python3
import os
import json
import sys
import asyncio
import aiohttp
from typing import Dict, Any, Optional

# -------------------------------------------------------------------------------------------------
# MOSKV-1 APEX: Tri-Modal Epistemic Pipeline (DAG)
# -------------------------------------------------------------------------------------------------
# Node 1: Perplexity (SOTA Extraction)
# Node 2: Gemini (Context Dilation / Epigenetic Map)
# Node 3: OpenAI (Thermodynamic Compression / Causal Collapse)
# -------------------------------------------------------------------------------------------------

async def call_perplexity(session: aiohttp.ClientSession, query: str) -> str:
    """Node 1: Extract pure facts and SOTA from the web."""
    print(f"[NODE 1] Perplexity Extraction Initiated for: '{query}'")
    api_key: Optional[str] = os.environ.get('PERPLEXITY_API_KEY')
    if not api_key: 
        return f"MOCK_SOTA: [API KEY MISSING] Fact-checking {query}"
    
    url: str = "https://api.perplexity.ai/chat/completions"
    headers: Dict[str, str] = {
        "Authorization": f"Bearer {api_key}", 
        "Content-Type": "application/json"
    }
    payload: Dict[str, Any] = {
        "model": "llama-3.1-sonar-large-128k-online", 
        "messages": [{"role": "user", "content": f"Extract hard SOTA facts for: {query}"}]
    }
    
    try:
        async with session.post(url, json=payload, headers=headers, timeout=30) as response:
            if response.status == 200:
                data: Dict[str, Any] = await response.json()
                return data['choices'][0]['message']['content']
            error_text: str = await response.text()
            return f"PERPLEXITY_ERROR: {error_text}"
    except asyncio.TimeoutError:
        return "PERPLEXITY_ERROR: Request Timeout"
    except Exception as e:
        return f"PERPLEXITY_ERROR: {str(e)}"

async def call_gemini(session: aiohttp.ClientSession, facts: str, context: str) -> str:
    """Node 2: Dilate the context using massive token window."""
    print("[NODE 2] Gemini Context Dilation Initiated.")
    api_key: Optional[str] = os.environ.get("GEMINI_API_KEY")
    if not api_key: 
        return f"MOCK_DILATION: [API KEY MISSING] Fusing {facts} with {context}"
    
    url: str = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={api_key}"
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    payload: Dict[str, Any] = {
        "contents": [{"parts": [{"text": f"Fuse these facts with our context and establish deep correlations:\nFacts: {facts}\nContext: {context}"}]}]
    }
    
    try:
        async with session.post(url, json=payload, headers=headers, timeout=45) as response:
            if response.status == 200:
                data: Dict[str, Any] = await response.json()
                return data['candidates'][0]['content']['parts'][0]['text']
            error_text: str = await response.text()
            return f"GEMINI_ERROR: {error_text}"
    except asyncio.TimeoutError:
        return "GEMINI_ERROR: Request Timeout"
    except Exception as e:
        return f"GEMINI_ERROR: {str(e)}"

async def call_openai(session: aiohttp.ClientSession, dilated_map: str) -> Dict[str, Any]:
    """Node 3: Compress the dilated map into a strict execution vector."""
    print("[NODE 3] OpenAI Thermodynamic Compression Initiated.")
    api_key: Optional[str] = os.environ.get("OPENAI_API_KEY")
    if not api_key: 
        return {"status": "C5-REAL_MOCKED", "mental_model": "Missing API Key", "execution_payload": {"action": "NONE"}}
        
    url: str = "https://api.openai.com/v1/chat/completions"
    headers: Dict[str, str] = {
        "Authorization": f"Bearer {api_key}", 
        "Content-Type": "application/json"
    }
    payload: Dict[str, Any] = {
        "model": "gpt-4o",
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "You are a thermodynamic compressor. Output ONLY strict JSON with 'status', 'mental_model', and 'execution_payload'."},
            {"role": "user", "content": f"Compress this map into an execution payload: {dilated_map}"}
        ]
    }
    
    try:
        async with session.post(url, json=payload, headers=headers, timeout=45) as response:
            if response.status == 200:
                data: Dict[str, Any] = await response.json()
                return json.loads(data['choices'][0]['message']['content'])
            error_text: str = await response.text()
            return {"status": "OPENAI_ERROR", "details": error_text}
    except asyncio.TimeoutError:
        return {"status": "OPENAI_ERROR", "details": "Request Timeout"}
    except Exception as e:
        return {"status": "OPENAI_ERROR", "details": str(e)}

async def async_main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python3 ouroboros_pipeline.py <query>")
        sys.exit(1)
        
    target_query: str = sys.argv[1]
    local_cortex_context: str = "MOSKV-1 APEX Rules: C5-REAL, Base-60, Zero Entropy."
    
    print("\n========================================================")
    print("OUROBOROS-∞ TRI-MODAL DAG EXECUTION")
    print("========================================================\n")
    
    async with aiohttp.ClientSession() as session:
        # Execute the DAG sequentially due to data dependencies
        sota_facts: str = await call_perplexity(session, target_query)
        dilated_context: str = await call_gemini(session, sota_facts, local_cortex_context)
        causal_node: Dict[str, Any] = await call_openai(session, dilated_context)
    
    print("\n========================================================")
    print("[FINAL CAUSAL NODE - EXERGY COMPRESSED]")
    print(json.dumps(causal_node, indent=2))
    print("========================================================\n")

def main() -> None:
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
