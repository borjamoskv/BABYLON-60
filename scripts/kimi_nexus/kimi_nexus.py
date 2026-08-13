#!/usr/bin/env python3
import os
import sys
import json
import logging
from typing import Optional
from pydantic import BaseModel
from openai import OpenAI

# Attempt to import FastMCP. If missing, we'll inform the user via logs.
try:
    pass  #     from mcp.server.fastmcp import FastMCP  # purgado por anergía
except ImportError:
    print("Error: The 'mcp' package is not installed. Please run: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("kimi-nexus")

# Verify API key
MOONSHOT_API_KEY = os.environ.get("MOONSHOT_API_KEY")
if not MOONSHOT_API_KEY:
    logger.warning("MOONSHOT_API_KEY environment variable is not set. API calls will fail.")

# Initialize OpenAI client pointed to Moonshot API
client = OpenAI(
    api_key=MOONSHOT_API_KEY or "dummy_key_to_prevent_init_crash",
    base_url="https://api.moonshot.cn/v1",
)

# Initialize FastMCP Server
mcp = FastMCP(
    "kimi-nexus",
    description="Kimi (Moonshot AI) Bridge for C5-REAL ecosystem."
)


@mcp.tool()
def kimi_ask(
    prompt: str,
    model: str = "moonshot-v1-32k",
    temperature: float = 0.3
) -> str:
    """
    Sends a general prompt to Kimi K3 (Moonshot AI) and returns the response.
    
    Args:
        prompt: The query or instruction to send to Kimi.
        model: The model to use (default: moonshot-v1-32k, others: moonshot-v1-8k, moonshot-v1-128k).
        temperature: Controls randomness (default: 0.3 for analytical tasks).
    """
    if not MOONSHOT_API_KEY:
        return "Error: MOONSHOT_API_KEY is not configured in the environment."
        
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are Kimi K3, acting through the Kimi-Nexus MCP bridge in the BABYLON-60 ecosystem. Respond concisely and rigorously."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error calling Moonshot API: {e}")
        return f"Error executing kimi_ask: {str(e)}"


@mcp.tool()
def kimi_audit(
    code_snippet: str,
    context_files: Optional[str] = None
) -> str:
    """
    Sends a snippet of code or architecture description to Kimi for a rigorous C5-REAL aligned audit.
    
    Args:
        code_snippet: The code, schema, or system logs to audit.
        context_files: Optional context (like file paths or surrounding architectures) to help Kimi.
    """
    if not MOONSHOT_API_KEY:
        return "Error: MOONSHOT_API_KEY is not configured in the environment."
        
    system_prompt = (
        "You are an elite C5-REAL systemic auditor. Your task is to perform a rigorous, "
        "thermodynamically aligned audit of the provided code or architecture. "
        "Look for existence gaps, thermodynamic friction, topological misalignments, "
        "and logical fallacies. Format your output using strict Markdown alerts (> [!WARNING], > [!IMPORTANT])."
    )
    
    user_prompt = f"### Code / Artifact to Audit:\n```\n{code_snippet}\n```\n"
    if context_files:
        user_prompt += f"\n### Context:\n{context_files}\n"
        
    try:
        response = client.chat.completions.create(
            model="moonshot-v1-32k",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error calling Moonshot API during audit: {e}")
        return f"Error executing kimi_audit: {str(e)}"

if __name__ == "__main__":
    # Start the FastMCP server on standard I/O
    mcp.run()
