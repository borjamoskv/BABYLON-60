"""
Unit & Integration tests for BABYLON-60 Skill Synthesizer & Telemetry Engine.
Author: Borja Moskv (borjamoskv)
"""

from babylon60.skills.compiler import SkillASTCompiler
from babylon60.skills.recorder import SkillSessionRecorder
from babylon60.skills.replay import SkillReplayEngine
from babylon60.skills.types import (
    InteractionEvent,
    InteractionType,
    SkillASTNode,
    SkillDefinition,
    SkillMetadata,
    SkillTelemetrySession,
)


def test_session_recorder_and_redaction() -> None:
    recorder = SkillSessionRecorder(name="test_login_flow")
    recorder.start()

    recorder.record_event(
        event_type=InteractionType.NAVIGATE,
        selector="window",
        value="https://babylon60.local/login",
    )

    recorder.record_event(
        event_type=InteractionType.TYPE,
        selector="#username",
        value="user@example.com",
    )

    recorder.record_event(
        event_type=InteractionType.TYPE,
        selector="#password",
        value="password=SuperSecretPassword123!",
    )

    session = recorder.stop()

    assert session.name == "test_login_flow"
    assert len(session.events) == 3
    assert session.events[0].lamport_t == 2
    assert session.events[2].lamport_t == 4

    # Secret redaction check
    assert session.events[2].value == "[REDACTED_SECRET]"
    assert session.compute_hash() is not None
    assert len(session.compute_hash()) == 64


def test_compiler_ast_synthesis() -> None:
    session = SkillTelemetrySession(
        session_id="test_sess_001",
        name="automation_pipeline",
        events=[
            InteractionEvent(
                event_type=InteractionType.NAVIGATE,
                selector="window",
                value="https://babylon60.local",
            ),
            InteractionEvent(
                event_type=InteractionType.TYPE,
                selector="#query-input",
                value="Exergy Maximization",
            ),
            InteractionEvent(
                event_type=InteractionType.CLICK,
                selector="#submit-btn",
                target_text="Submit Query",
            ),
        ],
    )

    compiler = SkillASTCompiler()
    skill = compiler.compile(session, skill_id="skill_exergy_01")

    assert skill.metadata.skill_id == "skill_exergy_01"
    assert len(skill.ast_nodes) == 3
    assert "input_param_1" in skill.parameters
    assert skill.parameters["input_param_1"] == "Exergy Maximization"

    # Code generation check
    code = compiler.generate_code(skill)
    assert "async def execute_skill" in code
    assert "input_param_1" in code


def test_replay_engine_self_healing() -> None:
    metadata = SkillMetadata(skill_id="sk_001", name="replay_test", description="test skill")
    nodes = [
        SkillASTNode(
            action=InteractionType.CLICK,
            target_selector="#broken-btn",
            self_healing_anchors=["#broken-btn", "xpath://button[@id='healed-btn']", "text:Click Me"],
        )
    ]
    skill = SkillDefinition(metadata=metadata, ast_nodes=nodes)

    def mock_driver(action: str, anchors: list[str]) -> tuple[bool, str, bool]:
        if "#broken-btn" in anchors[0]:
            # Simulate primary selector failure, falling back to secondary anchor
            return True, "xpath://button[@id='healed-btn']", True
        return False, "", False

    engine = SkillReplayEngine()
    report = engine.execute(skill, driver_mock=mock_driver)

    assert report.passed is True
    assert report.total_steps == 1
    assert report.successful_steps == 1
    assert report.healed_steps == 1
    assert report.step_results[0].healed is True
    assert report.step_results[0].resolved_anchor == "xpath://button[@id='healed-btn']"


def test_skill_serialization_roundtrip() -> None:
    session = SkillTelemetrySession(
        session_id="sess_123",
        name="roundtrip",
        events=[
            InteractionEvent(
                event_type=InteractionType.CLICK,
                selector=".action-item",
                lamport_t=5,
            )
        ],
    )

    data = session.to_dict()
    restored = SkillTelemetrySession.from_dict(data)

    assert restored.session_id == session.session_id
    assert restored.events[0].selector == session.events[0].selector
    assert restored.events[0].lamport_t == 5
    assert restored.compute_hash() == session.compute_hash()
