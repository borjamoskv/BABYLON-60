"""
Skill AST Compiler transducing raw interaction streams into optimized, parameterizable SkillDefinitions.
Author: Borja Moskv (borjamoskv)
"""

import uuid

from babylon60.skills.types import (
    InteractionEvent,
    InteractionType,
    SkillASTNode,
    SkillDefinition,
    SkillMetadata,
    SkillTelemetrySession,
)


class SkillASTCompiler:
    """
    Compiler that transduces recorded telemetry streams into optimized AST definitions,
    synthesizing self-healing locator anchors and parameter mappings.
    """

    def compile(
        self,
        session: SkillTelemetrySession,
        skill_id: str | None = None,
        description: str = "",
    ) -> SkillDefinition:
        skill_uuid = skill_id or f"skill_{uuid.uuid4().hex[:8]}"

        metadata = SkillMetadata(
            skill_id=skill_uuid,
            name=session.name,
            description=description or f"Synthesized skill from session '{session.name}'",
            author="borjamoskv",
            version="1.0.0",
            created_at=session.created_at,
            tags=["synthesized", "c5-real"],
        )

        ast_nodes: list[SkillASTNode] = []
        parameters: dict[str, str] = {}

        type_counter = 1

        for event in session.events:
            anchors: list[str] = self._extract_anchors(event)
            param_key = ""
            default_val = ""

            if event.event_type == InteractionType.TYPE and event.value:
                param_key = f"input_param_{type_counter}"
                default_val = event.value
                parameters[param_key] = default_val
                type_counter += 1

            invariant = self._derive_invariant(event)

            node = SkillASTNode(
                action=event.event_type,
                target_selector=event.selector,
                target_text=event.target_text,
                parameter_key=param_key,
                default_value=default_val,
                self_healing_anchors=anchors,
                assertion_invariant=invariant,
            )
            ast_nodes.append(node)

        return SkillDefinition(
            metadata=metadata,
            ast_nodes=ast_nodes,
            parameters=parameters,
            causal_taint="borjamoskv:skill_compiler:v1",
        )

    def generate_code(self, skill: SkillDefinition) -> str:
        """
        Generates executable Python / CDP script code for the skill.
        """
        lines: list[str] = [
            "# Auto-generated Skill Script — BABYLON-60 C5-REAL Kernel",
            f"# Skill ID: {skill.metadata.skill_id}",
            f"# Name: {skill.metadata.name}",
            "import asyncio",
            "from typing import Any",
            "",
            "async def execute_skill(driver: Any, params: dict[str, str] | None = None) -> bool:",
            "    params = params or {}",
        ]

        for i, node in enumerate(skill.ast_nodes, 1):
            lines.append(f"    # Step {i}: {node.action.value} on {node.target_selector or node.target_text}")

            if node.parameter_key:
                val_expr = f'params.get("{node.parameter_key}", "{node.default_value}")'
            else:
                val_expr = f'"{node.default_value}"'

            lines.append(
                f"    await driver.execute_action("
                f'action="{node.action.value}", '
                f'selector="{node.target_selector}", '
                f'target_text="{node.target_text}", '
                f"value={val_expr}, "
                f"anchors={node.self_healing_anchors})"
            )
            lines.append(f"    # Invariant: {node.assertion_invariant}")

        lines.append("    return True")
        return "\n".join(lines)

    def _extract_anchors(self, event: InteractionEvent) -> list[str]:
        anchors: list[str] = []

        if event.selector:
            anchors.append(f"css:{event.selector}")
            anchors.append(f"xpath://*[@id='{event.selector.lstrip('#')}']")

        if event.target_text:
            anchors.append(f"text:{event.target_text}")
            anchors.append(f"aria:{event.target_text}")

        return anchors

    def _derive_invariant(self, event: InteractionEvent) -> str:
        if event.event_type == InteractionType.CLICK:
            return f"ASSERT_ELEMENT_CLICKABLE({event.selector or event.target_text})"
        elif event.event_type == InteractionType.TYPE:
            return f"ASSERT_INPUT_VALUE({event.selector}, [PARAM])"
        elif event.event_type == InteractionType.NAVIGATE:
            return f"ASSERT_URL_CONTAINS({event.value})"
        else:
            return f"ASSERT_STATE_STABLE({event.selector or 'page'})"
