# [C5-REAL] Exergy-Maximized — Borja Moskv
import asyncio
import io
import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import EventSourceResponse  # type: ignore[reportAttributeAccessIssue]

app = FastAPI(title="CORTEX Sovereign Relay")

# Enable CORS for the dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

RELAY_PATH = Path("~/.babylon60/relay_buffer.jsonl").expanduser()


@app.get("/stream")
async def message_stream(request: Request):
    """EventSource endpoint for real-time CORTEX signals."""

    async def event_generator():
        # Open the file and seek to the end
        if not RELAY_PATH.exists():
            RELAY_PATH.parent.mkdir(parents=True, exist_ok=True)
            RELAY_PATH.touch()

        with RELAY_PATH.open("r", encoding="utf-8") as f:
            f.seek(0, io.SEEK_END)
            while True:
                if await request.is_disconnected():
                    break

                line = f.readline()
                if not line:
                    await asyncio.sleep(0.1)
                    continue

                try:
                    event = json.loads(line)
                    yield {"event": "message", "data": json.dumps(event)}
                except (json.JSONDecodeError, ValueError):
                    continue

    return EventSourceResponse(event_generator())  # type: ignore[reportArgumentType]


@app.get("/status")
def get_status():
    """Return relay status."""
    return {"status": "ACTIVE", "source": "COTEX-RELAY-V5"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=9998)
