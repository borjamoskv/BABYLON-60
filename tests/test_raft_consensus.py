import pytest
import asyncio
from babylon60.extensions.ha.raft import RaftNode, NodeRole, NodeRegistry, PreVoteResult

@pytest.mark.asyncio
async def test_prevote_result_quorum():
    res = PreVoteResult(granted=2, total=3)
    assert res.quorum_reachable is True

    res_fail = PreVoteResult(granted=0, total=3)
    assert res_fail.quorum_reachable is False

@pytest.mark.asyncio
async def test_raft_node_registry():
    NodeRegistry.reset()
    assert NodeRegistry.get("node1") is None
