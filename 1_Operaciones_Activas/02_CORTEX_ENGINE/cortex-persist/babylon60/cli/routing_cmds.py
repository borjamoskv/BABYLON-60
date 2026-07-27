# [C5-REAL] Exergy-Maximized
"""CORTEX CLI - LLM Routing Commands (Industrial Noir).

Exposes the tier/cost-aware routing matrix to the terminal.

Usage:
    cortex routing matrix              # Full intent→provider→model matrix
    cortex routing resolve gemini architect  # Resolve a single model
    cortex routing agents              # Show all agents with resolved models
    cortex routing cheapest code       # Cheapest providers for an intent
    cortex routing frontier architect  # Frontier providers only
"""

from __future__ import annotations

import click
from rich.table import Table
from rich.text import Text

from babylon60.cli.common import cli, console

# Industrial Noir Palette
_CYBER = "#CCFF00"
_GOLD = "#D4AF37"
_VIOLET = "#6600FF"
_EMERALD = "#06d6a0"
_RED = "#FF3366"
_DIM = "dim"

# Tier colors
_TIER_STYLE: dict[str, str] = {
    "frontier": f"bold {_CYBER}",
    "high": _GOLD,
    "local": _DIM,
}
# Cost colors
_COST_STYLE: dict[str, str] = {
    "free": f"bold {_EMERALD}",
    "low": _EMERALD,
    "medium": _GOLD,
    "variable": _VIOLET,
    "high": _RED,
}


@cli.group()
def routing() -> None:
    """LLM routing - tier/cost-aware provider selection."""


@routing.command("matrix")
@click.option("--intent", default=None, help="Filter by intent (code, reasoning, architect...)")
def routing_matrix(intent: str | None) -> None:
    """Show the full intent→provider→model routing matrix."""
    from babylon60.extensions.llm._presets import load_presets

    presets = load_presets()
    intents = ["code", "reasoning", "creative", "architect", "general"]

    table = Table(
        title="⚡ LLM Routing Matrix",
        title_style=f"bold {_CYBER}",
        border_style=_VIOLET,
        show_lines=True,
    )
    table.add_column("Provider", style=f"bold {_GOLD}", min_width=12)
    table.add_column("Tier", min_width=8)
    table.add_column("Cost", min_width=6)

    display_intents = [intent] if intent and intent in intents else intents
    for i in display_intents:
        table.add_column(i.capitalize(), min_width=14)

    for name, config in sorted(presets.items()):
        intent_map = config.get("intent_model_map", {})
        if not intent_map and not intent:
            continue  # Skip providers without routing for matrix view

        tier = config.get("tier", "?")
        cost = config.get("cost_class", "?")
        tier_style = _TIER_STYLE.get(tier, "white")
        cost_style = _COST_STYLE.get(cost, "white")

        row = [
            name,
            Text(tier, style=tier_style),
            Text(cost, style=cost_style),
        ]

        for i in display_intents:
            model = intent_map.get(i, "-")
            style = "white" if model != "-" else _DIM
            row.append(Text(model, style=style))

        table.add_row(*row)

    console.print(table)
    console.print(
        f"\n  [{_DIM}]{len(presets)} providers"
        f" · {sum(1 for p in presets.values() if p.get('intent_model_map'))}"
        f" with intent routing[/]"
    )


@routing.command("resolve")
@click.argument("provider")
@click.argument("intent")
def routing_resolve(provider: str, intent: str) -> None:
    """Resolve the best model for a provider+intent pair."""
    from babylon60.extensions.llm._presets import resolve_model

    model = resolve_model(provider, intent)
    if model:
        console.print(f"  [{_CYBER}]{provider}[/].{intent} → [bold white]{model}[/]")
    else:
        console.print(f"  [{_RED}]No model found for {provider}.{intent}[/]")


@routing.command("cheapest")
@click.argument("intent", default="general")
@click.option("--limit", "-n", default=10, help="Max results")
def routing_cheapest(intent: str, limit: int) -> None:
    """Show cheapest providers for an intent."""
    from babylon60.extensions.llm._presets import cheapest_providers, get_preset_info

    results = cheapest_providers(intent)[:limit]

    table = Table(
        title=f"💰 Cheapest Providers for '{intent}'",
        title_style=f"bold {_CYBER}",
        border_style=_VIOLET,
    )
    table.add_column("#", style=_DIM, width=3)
    table.add_column("Provider", style=f"bold {_GOLD}", min_width=12)
    table.add_column("Model", style="white", min_width=20)
    table.add_column("Cost", min_width=6)
    table.add_column("Tier", min_width=8)

    for i, (name, model) in enumerate(results, 1):
        info = get_preset_info(name) or {}
        cost = info.get("cost_class", "?")
        tier = info.get("tier", "?")
        table.add_row(
            str(i),
            name,
            model,
            Text(cost, style=_COST_STYLE.get(cost, "white")),
            Text(tier, style=_TIER_STYLE.get(tier, "white")),
        )

    console.print(table)


@routing.command("frontier")
@click.argument("intent", default="general")
def routing_frontier(intent: str) -> None:
    """Show frontier-tier providers for an intent."""
    from babylon60.extensions.llm._presets import frontier_providers, get_preset_info

    results = frontier_providers(intent)

    table = Table(
        title=f"🏆 Frontier Providers for '{intent}'",
        title_style=f"bold {_CYBER}",
        border_style=_VIOLET,
    )
    table.add_column("#", style=_DIM, width=3)
    table.add_column("Provider", style=f"bold {_GOLD}", min_width=12)
    table.add_column("Model", style="white", min_width=20)
    table.add_column("Cost", min_width=6)

    for i, (name, model) in enumerate(results, 1):
        info = get_preset_info(name) or {}
        cost = info.get("cost_class", "?")
        table.add_row(
            str(i),
            name,
            model,
            Text(cost, style=_COST_STYLE.get(cost, "white")),
        )

    console.print(table)


@routing.command("status")
def routing_status() -> None:
    """Show LLM provider readiness and API key status. [STATUS_CLI]"""
    from babylon60.extensions.llm._presets import provider_inventory

    inventory = provider_inventory()

    table = Table(
        title="📡 LLM Provider Readiness",
        title_style=f"bold {_CYBER}",
        border_style=_VIOLET,
    )
    table.add_column("Provider", style=f"bold {_GOLD}", min_width=12)
    table.add_column("Ready", justify="center", width=8)
    table.add_column("Status", min_width=15)
    table.add_column("Tier", min_width=10)
    table.add_column("Reason", style=_DIM, min_width=20)

    for p in sorted(inventory, key=lambda x: x["name"]):
        ready = p["ready"]
        ready_text = "✅" if ready else "❌"
        status_style = _EMERALD if ready else _RED

        table.add_row(
            p["name"],
            ready_text,
            Text(p["status"], style=status_style),
            Text(p["tier"], style=_TIER_STYLE.get(p["tier"], "white")),
            p["reason"] or "-",
        )

    console.print(table)


@routing.command("agents")
def routing_agents() -> None:
    """Show all registered agents with resolved models."""
    from babylon60.extensions.agents.registry import AgentCatalogLoader

    registry = AgentCatalogLoader()
    registry.clear()
    registry.load_all()

    table = Table(
        title="🧬 Sovereign Agents - Model Resolution",
        title_style=f"bold {_CYBER}",
        border_style=_VIOLET,
    )
    table.add_column("Agent", style=f"bold {_GOLD}", min_width=18)
    table.add_column("Provider", style=_VIOLET, min_width=10)
    table.add_column("Intent", style="white", min_width=10)
    table.add_column("Static Model", style=_DIM, min_width=16)
    table.add_column("→ Resolved", style=f"bold {_CYBER}", min_width=16)
    table.add_column("", width=3)

    for _, agent in sorted(registry.agents.items()):
        static = agent.model
        resolved = agent.resolved_model
        is_dynamic = resolved != static and agent.provider
        indicator = "⚡" if is_dynamic else "📌"

        table.add_row(
            agent.name,
            agent.provider or "-",
            agent.intent or "-",
            static,
            resolved,
            indicator,
        )

    console.print(table)


@routing.command("dispatch")
@click.argument("prompt")
@click.option(
    "--agent", "-a", default=None, help="Agent ID(s), comma-separated (e.g. 'zeus,athena')."
)
@click.option("--intent", "-i", default=None, help="Intent to route by (e.g. 'code', 'reasoning').")
@click.option("--tier", "-t", default="T1", help="Max tier to hydrate (T0, T1, T2).")
def routing_dispatch(prompt: str, agent: str | None, intent: str | None, tier: str) -> None:
    """Dispatch a prompt to sovereign agent(s) from the Pantheon."""
    import asyncio

    # Multi-agent parallel dispatch
    if agent and "," in agent:
        agent_ids = [a.strip() for a in agent.split(",") if a.strip()]
        console.print(
            f"[bold {_CYBER}]⚡ PARALLEL DISPATCH[/bold {_CYBER}] → "
            f"agents=[bold {_GOLD}]{', '.join(agent_ids)}[/bold {_GOLD}] | "
            f"tier=[{_VIOLET}]{tier}[/{_VIOLET}]"
        )

        async def _run_parallel() -> list[dict]:
            from babylon60.swarm.hydrate import dispatch_parallel

            return await dispatch_parallel(agent_ids, prompt, max_tier=tier)

        results = asyncio.run(_run_parallel())
        for res in results:
            aid = res.get("agent_id", "?")
            status = res.get("status", "?")
            style = f"bold {_CYBER}" if status == "OK" else "bold red"
            console.print(f"\n[{style}]─── {aid.upper()} ({status}) ───[/{style}]")
            if status == "OK":
                text = res.get("text", "")
                latency = res.get("latency_ms", 0)
                tokens = res.get("tokens_estimate", 0)
                console.print(f"[dim]⏱ {latency}ms | ~{tokens} tokens[/dim]")
                console.print(text)
            else:
                console.print(f"[red]{res.get('text', 'Unknown error')}[/red]")
        return

    # Single-agent dispatch
    from babylon60.swarm.hydrate import create_hydrated_runner
    from babylon60.swarm.runtime import SubagentRequest

    runner = create_hydrated_runner(max_tier=tier)

    if not runner.registry.all():
        console.print(f"[bold red]❌ No agents hydrated at tier {tier}.[/bold red]")
        return

    agents_loaded = len(runner.registry.all())
    console.print(
        f"[bold {_CYBER}]⚡ DISPATCH[/bold {_CYBER}] → "
        f"agent=[bold {_GOLD}]{agent or 'auto'}[/bold {_GOLD}] | "
        f"intent=[white]{intent or 'auto'}[/white] | "
        f"tier=[{_VIOLET}]{tier}[/{_VIOLET}] | "
        f"pool=[dim]{agents_loaded} agents[/dim]"
    )

    task_id = f"dispatch-{prompt[:16].replace(' ', '_')}"
    req = SubagentRequest(
        task_id=task_id,
        kind=intent or "reason",
        target_agent=agent or "",
        prompt=prompt,
    )

    async def _run() -> dict | str:
        resp = await runner.invoke_subagent(req)
        if not resp.ok:
            return f"❌ ERROR: {resp.error}"
        return resp.output

    result = asyncio.run(_run())

    console.print(f"\n[bold {_CYBER}]─── RESPONSE ───[/bold {_CYBER}]")

    if isinstance(result, dict):
        agent_name = result.get("agent_name", "?")
        latency = result.get("latency_ms", 0)
        tokens = result.get("tokens_estimate", 0)
        turn = result.get("turn", 0)
        usage_pct = result.get("guardrails", {}).get("usage_pct", 0)

        console.print(
            f"[dim]🧬 {agent_name} | ⏱ {latency}ms | "
            f"~{tokens} tokens (turn {turn}) | "
            f"session {usage_pct}% used[/dim]\n"
        )
        console.print(result.get("text", ""))
    else:
        console.print(f"\n{result}")


@routing.command("hydrate")
@click.option("--tier", "-t", default="T1", help="Max tier to show (T0, T1, T2).")
def routing_hydrate(tier: str) -> None:
    """Show which agents would be hydrated at a given tier."""
    from babylon60.swarm.hydrate import _classify_tier, create_hydrated_runner

    runner = create_hydrated_runner(max_tier=tier, enable_audit=False)

    table = Table(
        title=f"🧬 Hydrated Agents (max_tier={tier})",
        title_style=f"bold {_CYBER}",
        border_style=_VIOLET,
    )
    table.add_column("Agent", style=f"bold {_GOLD}", min_width=18)
    table.add_column("Tier", style=_VIOLET, min_width=4)
    table.add_column("Provider", style="white", min_width=10)
    table.add_column("Intent", style=_CYBER, min_width=10)
    table.add_column("Tools", style=_DIM, min_width=5)
    table.add_column("Max Tokens", style=_DIM, min_width=10)

    from babylon60.extensions.agents.registry import AgentCatalogLoader

    catalog = AgentCatalogLoader()
    for _agent_id, entry in sorted(catalog.agents.items()):
        agent_tier = _classify_tier(entry)
        tier_order = {"T0": 0, "T1": 1, "T2": 2}
        if tier_order.get(agent_tier, 2) > tier_order.get(tier, 1):
            continue
        table.add_row(
            entry.name,
            agent_tier,
            entry.provider or "-",
            entry.intent or "-",
            str(len(entry.tools)),
            str(entry.guardrails.max_session_tokens),
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(runner.registry.all())} agents hydrated[/dim]")
