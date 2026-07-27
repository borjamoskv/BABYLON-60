"""Cortex swarm — SubagentRunner, AgentRegistry and built-in handlers."""

import asyncio
import threading

from babylon60.swarm.autopulse import process_queue as autopulse


def start_swarm_daemon():
    """Start the Swarm Autopoiesis engine in a background thread."""

    def run():
        asyncio.run(autopulse())

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread
