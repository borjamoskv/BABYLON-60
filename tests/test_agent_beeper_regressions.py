"""C0278/C0279: observable pager delivery and single-broadcast rejection."""

import asyncio

import pytest

from scripts.c5_sharur.agent_beeper import AgentPager


async def receive(task):
    return await asyncio.wait_for(task, timeout=0.5)


@pytest.mark.parametrize("second", ["first", "replacement"])
async def test_second_broadcast_is_rejected_without_replacing_first(second):
    pager = AgentPager()
    pager.beep_swarm("first")
    with pytest.raises(RuntimeError, match="already emitted"):
        pager.beep_swarm(second)
    assert await receive(pager.wait_for_beep(1)) == "first"


async def test_unicast_wakes_an_already_suspended_receiver():
    pager = AgentPager()
    waiter = asyncio.create_task(pager.wait_for_beep(1))
    await asyncio.sleep(0)
    assert not waiter.done()
    pager.beep_agent(1, "addressed")
    assert await receive(waiter) == "addressed"


async def test_unicast_before_wait_is_consumed_once_and_can_repeat():
    pager = AgentPager()
    pager.register_agent(1)
    pager.beep_agent(1, "queued")
    assert await receive(pager.wait_for_beep(1)) == "queued"
    waiter = asyncio.create_task(pager.wait_for_beep(1))
    await asyncio.sleep(0)
    assert not waiter.done()
    pager.beep_agent(1, "next")
    assert await receive(waiter) == "next"


async def test_unicast_does_not_release_another_tenant():
    pager = AgentPager()
    addressed = asyncio.create_task(pager.wait_for_beep(1))
    other = asyncio.create_task(pager.wait_for_beep(2))
    try:
        await asyncio.sleep(0)
        pager.beep_agent(1, "private")
        assert await receive(addressed) == "private"
        assert not other.done()
        pager.beep_swarm("global")
        assert await receive(other) == "global"
    finally:
        other.cancel()
        await asyncio.gather(other, return_exceptions=True)


async def test_broadcast_reaches_current_late_and_repeated_waiters():
    pager = AgentPager()
    waiters = [asyncio.create_task(pager.wait_for_beep(i)) for i in range(32)]
    await asyncio.sleep(0)
    pager.beep_swarm("broadcast")
    assert await receive(asyncio.gather(*waiters)) == ["broadcast"] * 32
    assert await receive(pager.wait_for_beep(33)) == "broadcast"
    assert await receive(pager.wait_for_beep(0)) == "broadcast"


async def test_a_new_instance_waits_for_its_own_round():
    first, second = AgentPager(), AgentPager()
    first.beep_swarm("first")
    waiter = asyncio.create_task(second.wait_for_beep(1))
    await asyncio.sleep(0)
    assert not waiter.done()
    second.beep_swarm("second")
    assert await receive(waiter) == "second"
    assert await receive(first.wait_for_beep(1)) == "first"


async def test_cancelled_wait_can_be_replaced():
    pager = AgentPager()
    waiter = asyncio.create_task(pager.wait_for_beep(1))
    await asyncio.sleep(0)
    waiter.cancel()
    with pytest.raises(asyncio.CancelledError):
        await waiter
    replacement = asyncio.create_task(pager.wait_for_beep(1))
    await asyncio.sleep(0)
    pager.beep_agent(1, "after cancellation")
    assert await receive(replacement) == "after cancellation"


@pytest.mark.parametrize("register_again", [False, True])
async def test_deregistration_releases_old_wait_without_crossing_registration(register_again):
    pager = AgentPager()
    waiter = asyncio.create_task(pager.wait_for_beep(1))
    await asyncio.sleep(0)
    pager.deregister_agent(1)
    if register_again:
        pager.register_agent(1)
        pager.beep_agent(1, "new registration")
    with pytest.raises(RuntimeError, match="deregistered"):
        await receive(waiter)
    if register_again:
        assert await receive(pager.wait_for_beep(1)) == "new registration"


async def test_one_unicast_has_one_consumer_among_same_tenant_waiters():
    pager = AgentPager()
    waiters = [asyncio.create_task(pager.wait_for_beep(1)) for _ in range(2)]
    try:
        await asyncio.sleep(0)
        pager.beep_agent(1, "private")
        await asyncio.sleep(0)
        assert sum(w.done() for w in waiters) == 1
        pager.beep_swarm("global")
        assert sorted(await receive(asyncio.gather(*waiters))) == ["global", "private"]
    finally:
        for waiter in waiters:
            waiter.cancel()
        await asyncio.gather(*waiters, return_exceptions=True)


async def test_pending_unicast_precedes_retained_broadcast():
    pager = AgentPager()
    pager.register_agent(1)
    pager.beep_agent(1, "private")
    pager.beep_swarm("global")
    assert await receive(pager.wait_for_beep(1)) == "private"
    assert await receive(pager.wait_for_beep(1)) == "global"


async def test_concurrent_broadcast_attempts_have_one_winner():
    pager = AgentPager()

    async def emit(index):
        await asyncio.sleep(0)
        try:
            pager.beep_swarm(index)
            return index
        except RuntimeError:
            return None

    results = await asyncio.gather(*(emit(i) for i in range(32)))
    winners = [r for r in results if r is not None]
    assert len(winners) == 1
    assert await receive(pager.wait_for_beep(1)) == winners[0]


async def test_mixed_delivery_with_warmup_and_repeated_fresh_rounds():
    async def round_trip():
        pager = AgentPager()
        waiters = [asyncio.create_task(pager.wait_for_beep(i)) for i in range(32)]
        await asyncio.sleep(0)
        for i in range(0, 32, 2):
            pager.beep_agent(i, f"private-{i}")
        await asyncio.sleep(0)
        assert all(waiters[i].done() for i in range(0, 32, 2))
        assert all(not waiters[i].done() for i in range(1, 32, 2))
        pager.beep_swarm("global")
        result = await receive(asyncio.gather(*waiters))
        assert result == [f"private-{i}" if i % 2 == 0 else "global" for i in range(32)]

    for _ in range(3):
        await round_trip()
    for _ in range(20):
        await round_trip()
