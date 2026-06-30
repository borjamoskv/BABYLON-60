#!/usr/bin/env python3
# [C5-REAL] Exergy-Maximized
"""
Sovereign Singularity Nexus Engine.
Orchestrates cross-project unification, git health checks, ghost synchronization, and pattern bridging.
"""

import os
import sys
import json
import time
import shutil
import asyncio
import argparse
import subprocess
from pathlib import Path

# Add cortex core to sys.path to allow native imports
CORTEX_CORE_PATH = Path("$CORTEX_ROOT/30_BABYLON-60")
if not CORTEX_CORE_PATH.exists():
    CORTEX_CORE_PATH = Path("$CORTEX_ROOT/30_CORTEX")
if str(CORTEX_CORE_PATH) not in sys.path:
    sys.path.insert(0, str(CORTEX_CORE_PATH))

try:
    from rich.console import Console
    from rich.table import Table
except ImportError:
    # Fallback to standard print if rich is not in virtual environment
    class DummyConsole:
        def print(self, *args, **kwargs):
            print(*args, **kwargs)
    Console = DummyConsole
    Table = None

console = Console()

def get_git_info(p_path: Path):
    """Safely extract git branch, status, latest commit date and message."""
    git_dir = p_path / ".git"
    if not git_dir.exists():
        return "Non-Git", "-", "Unknown", "-"
        
    try:
        # Branch
        branch = subprocess.check_output(
            ["git", "-C", str(p_path), "rev-parse", "--abbrev-ref", "HEAD"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        
        # Status
        status_out = subprocess.check_output(
            ["git", "-C", str(p_path), "status", "--porcelain"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        status = "Dirty" if status_out else "Clean"
        
        # Latest commit info
        log_out = subprocess.check_output(
            ["git", "-C", str(p_path), "log", "-n", "1", "--format=%cI|%s"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        
        if log_out:
            ts, msg = log_out.split("|", 1)
            last_act = ts.split("T")[0]
            latest_commit = msg[:30] + "..." if len(msg) > 30 else msg
        else:
            last_act = "Unknown"
            latest_commit = "No commits"
            
        return branch, status, last_act, latest_commit
    except Exception:
        return "Error", "Error", "Error", "Error"

def run_pulse():
    """System health audit across all projects under 10_PROJECTS."""
    console.print("\n[bold royal_blue]🌌 SINGULARITY NEXUS v∞: PULSE AUDIT[/bold royal_blue]\n")
    
    projects_dir = Path("$CORTEX_ROOT/10_PROJECTS")
    if not projects_dir.exists():
        console.print("[red]Error: Projects directory '$CORTEX_ROOT/10_PROJECTS' does not exist.[/]")
        return
        
    if Table:
        table = Table(title="Sovereign Project Registry", border_style="cyan")
        table.add_column("Project", style="bold white")
        table.add_column("Git Branch", style="green")
        table.add_column("Git Status", style="bold yellow")
        table.add_column("Last Activity", style="dim")
        table.add_column("Latest Commit", style="italic")
    else:
        print(f"{'Project':<25} | {'Branch':<15} | {'Status':<10} | {'Activity':<12} | {'Latest Commit'}")
        print("-" * 85)

    for p_path in sorted(projects_dir.iterdir()):
        if not p_path.is_dir() or p_path.name.startswith("."):
            continue
            
        project_name = p_path.name
        branch, status, last_act, latest_commit = get_git_info(p_path)
        
        if Table:
            status_style = "[red]Dirty[/red]" if status == "Dirty" else "[green]Clean[/green]" if status == "Clean" else status
            table.add_row(project_name, branch, status_style, last_act, latest_commit)
        else:
            print(f"{project_name:<25} | {branch:<15} | {status:<10} | {last_act:<12} | {latest_commit}")
            
    if Table:
        console.print(table)
    console.print("\n")
    
    # Recent mutations from the Nexus DB
    console.print("[bold white]🌀 Recent Cross-Domain Mutations (Nexus DB)[/bold white]")
    try:
        from cortex.extensions.nexus import NexusWorldModel
        
        async def query_db():
            nexus = NexusWorldModel()
            mutations = await nexus.query(limit=5)
            nexus.shutdown()
            return mutations
            
        mutations = asyncio.run(query_db())
        
        if mutations:
            if Table:
                mut_table = Table(border_style="dim")
                mut_table.add_column("Timestamp", style="dim")
                mut_table.add_column("Origin", style="cyan")
                mut_table.add_column("Intent", style="bold yellow")
                mut_table.add_column("Project", style="white")
                mut_table.add_column("Summary", style="italic")
                
                for m in mutations:
                    try:
                        payload = json.loads(m["payload_json"])
                        summary = payload.get("summary", "-")
                    except Exception:
                        summary = "-"
                    
                    import datetime
                    dt = datetime.datetime.fromtimestamp(m["timestamp"], tz=datetime.timezone.utc)
                    ts_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    
                    mut_table.add_row(ts_str, m["origin"], m["intent"], m["project"], summary)
                console.print(mut_table)
            else:
                for m in mutations:
                    import datetime
                    dt = datetime.datetime.fromtimestamp(m["timestamp"], tz=datetime.timezone.utc)
                    ts_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[{ts_str}] {m['origin']} -> {m['intent']} ({m['project']})")
        else:
            console.print("[dim]No mutations stored in Nexus DB.[/dim]")
    except Exception as e:
        console.print(f"[red]Error loading Nexus DB: {e}[/]")

def run_ghosts():
    """Sync ghosts.json based on active project state."""
    console.print("\n[bold royal_blue]👻 SYNCING GHOSTS ACROSS WORKSPACES[/bold royal_blue]\n")
    
    agent_dir = Path("$CORTEX_ROOT/.agent")
    memory_dir = agent_dir / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    ghosts_path = memory_dir / "ghosts.json"
    
    ghosts = {}
    if ghosts_path.exists():
        try:
            ghosts = json.loads(ghosts_path.read_text())
        except Exception:
            ghosts = {}
            
    projects_dir = Path("$CORTEX_ROOT/10_PROJECTS")
    if not projects_dir.exists():
        console.print("[red]Error: Projects directory does not exist.[/]")
        return
        
    updated_count = 0
    for p_path in projects_dir.iterdir():
        if not p_path.is_dir() or p_path.name.startswith("."):
            continue
            
        project_name = p_path.name
        git_dir = p_path / ".git"
        
        if git_dir.exists():
            try:
                log_out = subprocess.check_output(
                    ["git", "-C", str(p_path), "log", "-n", "1", "--format=%cI|%s|%an"],
                    text=True, stderr=subprocess.DEVNULL
                ).strip()
                if log_out:
                    ts, msg, author = log_out.split("|", 2)
                    
                    if project_name not in ghosts:
                        ghosts[project_name] = {}
                        
                    ghosts[project_name].update({
                        "timestamp": ts,
                        "mood": f"Author: {author} | Commit: {msg[:40]}",
                        "blocked_by": None
                    })
                    updated_count += 1
            except Exception:
                pass
                
    ghosts_path.write_text(json.dumps(ghosts, indent=2))
    console.print(f"[green]Successfully synced {updated_count} ghosts to {ghosts_path}[/green]")

def run_bridge(source_project: str, target_project: str, pattern: str):
    """Bridge a pattern from source_project to target_project."""
    console.print(f"\n[bold royal_blue]🌉 BRIDGING PATTERN '{pattern}'[/bold royal_blue]")
    console.print(f"Source: [cyan]{source_project}[/cyan] ➔ Target: [cyan]{target_project}[/cyan]\n")
    
    projects_dir = Path("$CORTEX_ROOT/10_PROJECTS")
    src_path = projects_dir / source_project
    tgt_path = projects_dir / target_project
    
    if not src_path.exists() or not src_path.is_dir():
        console.print(f"[red]Error: Source project '{source_project}' does not exist.[/]")
        sys.exit(1)
        
    if not tgt_path.exists() or not tgt_path.is_dir():
        console.print(f"[red]Error: Target project '{target_project}' does not exist.[/]")
        sys.exit(1)
        
    import fnmatch
    matches = []
    
    for root, dirnames, filenames in os.walk(src_path):
        if ".git" in root or ".venv" in root or "node_modules" in root or "__pycache__" in root:
            continue
        for filename in fnmatch.filter(filenames, pattern):
            matches.append(Path(root) / filename)
            
    if not matches:
        for root, dirnames, filenames in os.walk(src_path):
            if ".git" in root or ".venv" in root or "node_modules" in root or "__pycache__" in root:
                continue
            for dirname in fnmatch.filter(dirnames, pattern):
                matches.append(Path(root) / dirname)
                
    if not matches:
        console.print(f"[yellow]No files or directories matching '{pattern}' found in '{source_project}'.[/]")
        sys.exit(1)
        
    bridged_files = 0
    for match in matches:
        rel_path = match.relative_to(src_path)
        dest = tgt_path / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        if match.is_file():
            if dest.exists() or dest.is_symlink():
                dest.unlink()
            os.symlink(match.resolve(), dest)
            console.print(f"  [green]Bridge file (Symlink):[/green] {rel_path}")
            bridged_files += 1
        elif match.is_dir():
            if dest.exists() and not dest.is_symlink():
                shutil.rmtree(dest)
            elif dest.is_symlink():
                dest.unlink()
            os.symlink(match.resolve(), dest)
            console.print(f"  [green]Bridge directory (Symlink):[/green] {rel_path}")
            bridged_files += 1
            
    # Record in Nexus DB
    try:
        from cortex.extensions.nexus import NexusWorldModel, WorldMutation, DomainOrigin, IntentType, Priority
        
        async def record_mutation():
            nexus = NexusWorldModel()
            await nexus.mutate(
                WorldMutation(
                    origin=DomainOrigin.CORTEX_CORE,
                    intent=IntentType.BRIDGE_FORMED,
                    project=target_project,
                    priority=Priority.NORMAL,
                    payload={
                        "source": source_project,
                        "target": target_project,
                        "pattern": pattern,
                        "files_count": bridged_files,
                        "summary": f"Bridged '{pattern}' pattern from '{source_project}' to '{target_project}'"
                    }
                )
            )
            nexus.shutdown()
            
        asyncio.run(record_mutation())
    except Exception as e:
        console.print(f"[dim](Could not log mutation to Nexus DB: {e})[/dim]")
        
    console.print(f"\n[green]Bridge operation completed. Synced {bridged_files} items.[/green]")

def run_register(name: str, url: str, auth: str):
    """Register a service in the CORTEX registry."""
    console.print(f"\n[bold royal_blue]🌌 REGISTERING SERVICE: {name}[/bold royal_blue]")
    registry_dir = Path("$CORTEX_ROOT/10_PROJECTS/cortex-meta/registry")
    registry_dir.mkdir(parents=True, exist_ok=True)
    
    service_data = {
        "name": name,
        "url": url,
        "auth": auth,
        "registered_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "active"
    }
    
    file_path = registry_dir / f"{name}.json"
    file_path.write_text(json.dumps(service_data, indent=2))
    console.print(f"[green]Successfully registered service '{name}' to {file_path}[/green]\n")

def run_sync():
    """Run full sync pipeline: discover -> ghosts -> pulse."""
    console.print("[bold royal_blue]🌀 RUNNING FULL NEXUS UNIFICATION PIPELINE[/bold royal_blue]")
    run_ghosts()
    run_pulse()

def main():
    parser = argparse.ArgumentParser(description="Singularity Nexus Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Pulse
    subparsers.add_parser("pulse", help="System health audit")
    
    # Ghosts
    subparsers.add_parser("ghosts", help="Sync active project activity")
    
    # Bridge
    bridge_parser = subparsers.add_parser("bridge", help="Bridge pattern")
    bridge_parser.add_argument("source_project")
    bridge_parser.add_argument("target_project")
    bridge_parser.add_argument("pattern")
    
    # Sync
    subparsers.add_parser("sync", help="Run full unification")

    # Register
    register_parser = subparsers.add_parser("register", help="Register a service in CORTEX")
    register_parser.add_argument("--name", required=True)
    register_parser.add_argument("--url", required=True)
    register_parser.add_argument("--auth", default="jwt")
    
    args = parser.parse_args()
    
    if args.command == "pulse":
        run_pulse()
    elif args.command == "ghosts":
        run_ghosts()
    elif args.command == "bridge":
        run_bridge(args.source_project, args.target_project, args.pattern)
    elif args.command == "sync":
        run_sync()
    elif args.command == "register":
        run_register(args.name, args.url, args.auth)

if __name__ == "__main__":
    main()
