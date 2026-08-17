# Live LLM Runner for LUNA_SOL_GAP_BENCHMARK
import os
from typing import Tuple
import httpx
from benchmark.runners.base_runner import BaseRunner


class LLMRunner(BaseRunner):
    def __init__(self, model_name: str, api_key: str = None, base_url: str = None):
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("GEMINI_API_KEY") or ""
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"

    def generate(self, prompt: str, use_think: bool = False) -> Tuple[str, int]:
        if not self.api_key:
            raise ValueError(
                "API key missing. Set OPENAI_API_KEY environment variable or pass --mock to run offline benchmark."
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Format request payload
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "You are a precise technical model participating in an automated benchmark."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2 if not use_think else 0.7,
        }

        if use_think:
            payload["reasoning_effort"] = "high"

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", len(prompt.split()) + len(content.split()))
                return content, tokens
        except Exception as e:
            raise RuntimeError(f"LLM API call failed for model {self.model_name}: {str(e)}")
