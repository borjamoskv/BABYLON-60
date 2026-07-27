# [C5-REAL] Exergy-Maximized — Borja Moskv
import asyncio
from pathlib import Path

import aiofiles  # pyright: ignore[reportMissingModuleSource]
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

app = FastAPI(title="CORTEX x Notch Relay")
RELAY_BUFFER = Path("~/.babylon60/relay_buffer.jsonl").expanduser()


@app.get("/status")
async def status():
    return {"status": "Sovereign", "buffer": str(RELAY_BUFFER)}


async def event_generator():
    """Polls the relay buffer and yields new events."""
    if not RELAY_BUFFER.exists():
        RELAY_BUFFER.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(RELAY_BUFFER, "w") as f:
            await f.write("")

    # Start at the end of the file
    stat = await asyncio.to_thread(RELAY_BUFFER.stat)
    file_size = stat.st_size

    while True:
        stat = await asyncio.to_thread(RELAY_BUFFER.stat)
        current_size = stat.st_size
        if current_size > file_size:
            async with aiofiles.open(RELAY_BUFFER) as f:
                await f.seek(file_size)
                lines = await f.readlines()
                for line in lines:
                    if line.strip():
                        yield f"data: {line.strip()}\n\n"
            file_size = current_size
        await asyncio.sleep(0.1)


@app.get("/events")
async def events(request: Request):
    return StreamingResponse(event_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9998)
