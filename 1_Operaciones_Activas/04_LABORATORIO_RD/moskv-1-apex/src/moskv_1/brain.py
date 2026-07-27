from typing import Optional, List, Any
import asyncio
import aiohttp
import json
from moskv_1.event_bus import EventBus, CortexEvent
from moskv_1.event_bus import EventBus, CortexEvent

class BrainRegion:
    """
    Represents an isolated cognitive worker node within the CEN Swarm Cluster.
    """
    def __init__(self, region_name: str, server_url: str = "nats://localhost:4222"):
        self.region_name = region_name
        self.bus = EventBus(server_url=server_url)
        self.subscriptions: List[Any] = []

    async def run(self):
        """
        Initializes the NATS connection for this region.
        """
        await self.bus.connect()
        print(f"[CEN-Cluster] BrainRegion <{self.region_name}> Online. Exergy optimized.")

    async def process_event(self, event: CortexEvent):
        """
        Processes incoming events. Override in concrete subclasses.
        """
        pass

    async def infer_local(self, prompt: str, model: str = "llama3") -> str:
        """
        Sovereign inference using local Ollama instance (Apple Silicon).
        Enforces strict syntactic validation to drop 'LLM Slop' before it reaches the core.
        """
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        return "[ERROR] Inference Core Unreachable."
                    
                    data = await response.json()
                    output = data.get("response", "")
                    
                    # Socket-level syntactic validation (Anti-Slop Protocol)
                    slop_signatures = ["Here is", "Sure,", "I can help", "Let me know"]
                    if any(sig.lower() in output.lower() for sig in slop_signatures):
                        return "[QUARANTINE] Detected Green Theater (LLM Slop). Output suppressed."
                        
                    return output
            except Exception as e:
                return f"[ERROR] Local inference failed: {e}"

    async def emit(self, subject: str, payload: dict) -> CortexEvent:
        """
        Emits an event, automatically enriching payload with sourceRegion.
        """
        enriched_payload = {**payload, "sourceRegion": self.region_name}
        return await self.bus.publish(subject, enriched_payload)

    async def listen(self, subject: str, durable_name: Optional[str] = None):
        """
        Subscribes to a subject and forwards events to process_event.
        """
        async def event_handler(event: CortexEvent, msg):
            print(f"[{self.region_name}] Received Event Hash: {event.hash}")
            await self.process_event(event)

        sub = await self.bus.subscribe(
            topic=subject,
            callback=event_handler,
            durable_name=durable_name
        )
        self.subscriptions.append(sub)
        return sub

    async def shutdown(self):
        """
        Gracefully terminates subscriptions and closes NATS connections.
        """
        print(f"[CEN-Cluster] BrainRegion <{self.region_name}> Shutting down...")
        # Note: in nats-py, subscriptions can be unsubscribed
        for sub in self.subscriptions:
            try:
                await sub.unsubscribe()
            except Exception:
                pass
        await self.bus.close()
