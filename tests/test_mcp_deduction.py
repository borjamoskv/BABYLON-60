"""
BABYLON-60 Test Suite: Dynamic MCP Deduction & Synthesis Pipeline (C5-REAL)
"""

import os
import pytest
import tempfile
from babylon60.kernel.mcp_deductive_engine import McpDeductiveEngine
from babylon60.kernel.mcp_scaffolder import McpCodeScaffolder
from babylon60.kernel.mcp_sandbox_validator import McpSandboxValidator
from babylon60.kernel.mcp_lifecycle_manager import McpLifecycleManager


def test_mcp_deductive_engine() -> None:
    engine = McpDeductiveEngine(friction_threshold=0.40)

    # 1. Sin fricción
    assert engine.calculate_friction([]) == 0.0
    assert not engine.should_deduce_mcp([])

    # 2. Con alta fricción y errores repetidos
    high_friction_steps = [
        {"tokens": 1200, "status": "ERROR"},
        {"tokens": 1500, "status": "ERROR"},
        {"tokens": 2000, "status": "SUCCESS"},
        {"tokens": 1800, "status": "SUCCESS"},
    ]
    friction = engine.calculate_friction(high_friction_steps)
    assert friction >= 0.40
    assert engine.should_deduce_mcp(high_friction_steps)

    # 3. Deducir contrato
    sample_calls = [{"args": {"query": "SELECT * FROM users", "limit": 10}}]
    contract = engine.deduce_contract("DatabaseQuery", sample_calls)
    assert contract.server_name == "DatabasequeryBridge"
    assert contract.tool_name == "databasequery_action"
    assert len(contract.parameters) == 2
    assert contract.parameters[0].name == "query"
    assert contract.parameters[0].param_type == "string"


@pytest.mark.asyncio
async def test_full_mcp_scaffolding_sandbox_and_lifecycle() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test_causal_gate.db")

        # 1. Deducción
        engine = McpDeductiveEngine()
        contract = engine.deduce_contract("SystemInfo", [{"args": {"target_host": "localhost"}}])

        # 2. Scaffolding
        scaffolder = McpCodeScaffolder(output_dir=tmp_dir)
        script_path = scaffolder.scaffold_fastmcp_python(contract)
        assert os.path.exists(script_path)

        # 3. Validación Sandbox stdio
        validator = McpSandboxValidator()
        validation_result = await validator.validate_mcp_server(script_path, contract)
        assert validation_result["is_valid"] is True
        assert validation_result["server_name"] == "SysteminfoBridge"
        assert contract.tool_name in validation_result["tools_found"]
        assert validation_result["latency_ms"] > 0.0

        # 4. Lifecycle Management
        lifecycle = McpLifecycleManager(db_path=db_path)
        reg_res = lifecycle.register_mcp(contract, script_path, scope="EPH_EPHEMERAL")
        assert reg_res["status"] == "SUCCESS"

        active_mcps = lifecycle.list_active_mcps()
        assert len(active_mcps) == 1
        assert active_mcps[0]["server_name"] == "SysteminfoBridge"

        # 5. Purga de anergía (EPH_EPHEMERAL)
        purged = lifecycle.purge_ephemeral_mcps()
        assert purged == 1
        assert not os.path.exists(script_path)
        assert len(lifecycle.list_active_mcps()) == 0


def test_mcp_bomb_synthesize_execute_and_detonate() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test_causal_gate.db")
        lifecycle = McpLifecycleManager(db_path=db_path)

        receipt = lifecycle.synthesize_and_detonate_bomb(
            domain_name="VectorNorm",
            implementation_body="return {'hypot': round(math.hypot(x, y), 4), 'manhattan': abs(x) + abs(y)}",
            call_arguments={"x": 3, "y": 4},
            description="Calcula norma euclídea y manhattan en un MCP efímero autodestructible.",
            output_dir=tmp_dir,
        )

        assert receipt["status"] == "SUCCESS"
        assert receipt["is_valid"] is True
        assert receipt["self_destruct_verified"] is True
        assert len(receipt["code_hash"]) == 64
        assert receipt["tool_output"]["result"] == {"hypot": 5.0, "manhattan": 7}
        assert receipt["tool_output"]["self_destruct_triggered"] is True
        assert len(lifecycle.list_active_mcps()) == 0


def test_mcp_bomb_ast_security_gate_blocks_escapes() -> None:
    with pytest.raises(ValueError, match="AX-0 AST GATE"):
        McpCodeScaffolder.validate_implementation_ast("import subprocess\nreturn subprocess.check_output(['id'])")

    with pytest.raises(ValueError, match="AX-0 AST GATE"):
        McpCodeScaffolder.validate_implementation_ast("return eval('2 + 2')")

    with pytest.raises(ValueError, match="AX-0 AST GATE"):
        McpCodeScaffolder.validate_implementation_ast("return __import__('os').system('ls')")
