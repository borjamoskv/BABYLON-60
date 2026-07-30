# [C5-REAL] Exergy-Maximized Unit Test
import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest
import aiosqlite

from babylon60.guards.ouroboros_entropy_guard import OuroborosEntropyGuard


@pytest.mark.asyncio
async def test_ouroboros_entropy_guard_happy_path():
    guard = OuroborosEntropyGuard(max_tasks=10, repetition_threshold=0.8)
    conn = MagicMock(spec=aiosqlite.Connection)

    # Happy path: normal content, no event loop overload
    await guard.check(
        content="This is some normal content with high shannon entropy to pass the check.",
        project="test_proj",
        fact_type="decision",
        meta={},
        conn=conn,
    )


@pytest.mark.asyncio
async def test_ouroboros_entropy_guard_task_limit():
    guard = OuroborosEntropyGuard(max_tasks=1, repetition_threshold=0.8)
    conn = MagicMock(spec=aiosqlite.Connection)

    # Spawn dummy tasks to exceed limit of 1
    async def dummy():
        await asyncio.sleep(1)

    t1 = asyncio.create_task(dummy())
    t2 = asyncio.create_task(dummy())

    try:
        with pytest.raises(ValueError, match="Async task limit exceeded"):
            await guard.check(
                content="Some normal content",
                project="test_proj",
                fact_type="decision",
                meta={},
                conn=conn,
            )
    finally:
        t1.cancel()
        t2.cancel()


@pytest.mark.asyncio
async def test_ouroboros_entropy_guard_task_repetition():
    guard = OuroborosEntropyGuard(max_tasks=50, repetition_threshold=0.5)
    conn = MagicMock(spec=aiosqlite.Connection)

    # We need to mock asyncio.all_tasks to return tasks with repetitive signatures
    loop = asyncio.get_running_loop()

    tasks = []
    for _i in range(10):
        t = MagicMock()
        t.get_name.return_value = "repetitive_task_name"
        t.get_coro.return_value = MagicMock(__name__="repetitive_coro_name")
        tasks.append(t)

    original_all_tasks = asyncio.all_tasks
    asyncio.all_tasks = lambda loop: set(tasks)

    try:
        with pytest.raises(ValueError, match="Infinite loop detected in async tasks"):
            await guard.check(
                content="Some normal content",
                project="test_proj",
                fact_type="decision",
                meta={},
                conn=conn,
            )
    finally:
        asyncio.all_tasks = original_all_tasks


@pytest.mark.asyncio
async def test_ouroboros_entropy_guard_low_entropy():
    guard = OuroborosEntropyGuard(max_tasks=50, repetition_threshold=0.8)
    conn = MagicMock(spec=aiosqlite.Connection)

    # Low entropy payload (repeating 'a')
    low_entropy_content = "a" * 150

    with pytest.raises(ValueError, match="abnormally low Shannon entropy"):
        await guard.check(
            content=low_entropy_content,
            project="test_proj",
            fact_type="decision",
            meta={},
            conn=conn,
        )


@pytest.mark.asyncio
async def test_ouroboros_entropy_guard_tick_latency():
    guard = OuroborosEntropyGuard(latency_threshold=0.03)

    # We want to test task cancellation when latency is triggered
    loop = asyncio.get_running_loop()

    # Create a dummy task that we want to cancel
    cancelled_triggered = False

    async def target_task():
        nonlocal cancelled_triggered
        try:
            await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            cancelled_triggered = True
            raise

    task = asyncio.create_task(target_task())

    # Start the guard monitoring
    guard.start(loop)

    # Let the loop run to initialize the tick
    await asyncio.sleep(0.01)

    # Simulate a blocking event loop tick
    import time

    time.sleep(0.08)  # Block the loop for 80ms (> 30ms latency_threshold)

    try:
        # Give the monitor thread a brief moment to process the latency and call cancel
        await asyncio.sleep(0.05)
    except asyncio.CancelledError:
        pass

    try:
        assert (
            cancelled_triggered is True
            or task.cancelled()
            or (hasattr(task, "cancelling") and task.cancelling())
        )
    finally:
        guard.stop()
        if not task.done():
            task.cancel()
