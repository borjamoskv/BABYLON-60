import ast
import re
import sys
import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any


# ==========================================
# 1. ESTADO DEL PROYECTO (STATE)
# ==========================================
@dataclass
class ProjectState:
    root_path: str
    files: list[str] = field(default_factory=list)
    stack: dict[str, Any] = field(default_factory=dict)
    code_structure: dict[str, Any] = field(default_factory=dict)
    dependency_graph: dict[str, Any] = field(default_factory=dict)
    summaries: dict[str, str] = field(default_factory=dict)
    features: list[dict] = field(default_factory=list)
    conflicts: list[dict] = field(default_factory=list)
    technical_debt: list[dict] = field(default_factory=list)
    current_architecture: dict[str, Any] = field(default_factory=dict)
    recommended_architecture: dict[str, Any] = field(default_factory=dict)
    tasks: list[dict] = field(default_factory=list)


# ==========================================
# 2. CORE: PARSER, GRAPH, PATTERNS & HEALTH
# ==========================================
class CodeParser:
    def parse_python(self, code: str) -> dict[str, list[str]]:
        result = {"classes": [], "functions": [], "imports": []}  # type: ignore
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    result["classes"].append(node.name)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    result["functions"].append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        result["imports"].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        result["imports"].append(node.module)
        except SyntaxError:
            pass
        return result

    def parse_js(self, code: str) -> dict[str, list[str]]:
        functions = re.findall(
            r"function\s+([A-Za-z0-9_]+)|const\s+([A-Za-z0-9_]+)\s*=\s*\(", code
        )
        imports = re.findall(
            r'import\s+.*?from\s+[\'"](.+?)[\'"]|require\([\'"](.+?)[\'"]\)', code
        )
        return {
            "classes": re.findall(r"class\s+([A-Za-z0-9_]+)", code),
            "functions": [f[0] or f[1] for f in functions if f],
            "imports": [i[0] or i[1] for i in imports if i],
        }


def detect_cycles(dependency_graph: dict) -> list[list[str]]:
    visited, rec_stack, cycles = set(), set(), []

    def dfs(node: str, path: list[str], depth: int = 0) -> None:
        if depth > 100:  # Recursion guard
            return
        visited.add(node)
        rec_stack.add(node)
        for neighbor in dependency_graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor, path + [neighbor], depth + 1)
            elif neighbor in rec_stack:
                cycle_start = path.index(neighbor) if neighbor in path else 0
                cycles.append(path[cycle_start:] + [neighbor])
        rec_stack.discard(node)

    for node in dependency_graph:
        if node not in visited:
            dfs(node, [node])
    return cycles


def generate_mermaid(dependency_graph: dict, max_nodes: int = 30) -> str:
    lines = ["graph TD"]
    for file in list(dependency_graph.keys())[:max_nodes]:
        imports = dependency_graph.get(file, [])
        src = file.replace("/", "_").replace(".", "_").replace("-", "_")
        if not imports:
            lines.append(f"    {src}")
            continue
        for imp in imports[:5]:
            dst = imp.replace("/", "_").replace(".", "_").replace("-", "_")
            lines.append(f"    {src} --> {dst}")
    return "\n".join(lines)


def detect_pattern(state: ProjectState) -> dict[str, Any]:
    files_lower = [f.lower() for f in state.files]
    modules = state.current_architecture.get("modules_detected", [])
    modules_lower = [m.lower() for m in modules]

    scores = {
        "MVC": 0,
        "Clean Architecture": 0,
        "Monolito Modular": 0,
        "Script-based": 0,
        "Microservices": 0,
    }

    if any(kw in f for kw in ["controller", "view", "model"] for f in files_lower):
        scores["MVC"] += 2
    if any(
        kw in m for kw in ["usecase", "repository", "domain"] for m in modules_lower
    ):
        scores["Clean Architecture"] += 2
    if len(modules) >= 4:
        scores["Monolito Modular"] += 3

    if (
        state.current_architecture.get("total_functions", 0)
        > state.current_architecture.get("total_classes", 0) * 2
    ):
        scores["Script-based"] += 3

    detected = max(scores, key=lambda k: scores[k])
    return {"pattern": detected, "confidence_score": scores[detected]}


def score_project(state: ProjectState) -> dict[str, Any]:
    score = 100
    penalties, bonuses = [], []

    orphans = state.current_architecture.get("possible_orphans", [])
    if orphans:
        p = min(len(orphans) * 3, 20)
        score -= p
        penalties.append(f"-{p} pts: {len(orphans)} módulos huérfanos")

    high_coupling = state.current_architecture.get("high_coupling_files", {})
    if high_coupling:
        p = min(len(high_coupling) * 4, 20)
        score -= p
        penalties.append(f"-{p} pts: {len(high_coupling)} archivos altamente acoplados")

    if state.technical_debt:
        p = min(len(state.technical_debt) * 2, 15)
        score -= p
        penalties.append(
            f"-{p} pts: {len(state.technical_debt)} items de deuda técnica"
        )

    if state.stack.get("markdown_docs"):
        score += 5
        bonuses.append("+5 pts: Documentación markdown presente")

    if state.current_architecture.get("total_functions", 0) > 0:
        score += 5
        bonuses.append("+5 pts: Código funcional detectado")

    score = max(0, min(100, score))
    label = (
        "🟢 SALUDABLE"
        if score >= 80
        else ("🟡 NECESITA ATENCIÓN" if score >= 50 else "🔴 CRÍTICO")
    )
    return {"score": score, "label": label, "penalties": penalties, "bonuses": bonuses}


# ==========================================
# 3. AGENTES (SCOUT, STRUCTURE, ANALYST, ARCHITECT, PLANNER)
# ==========================================
class ScoutAgent:
    def run(self, state: ProjectState) -> ProjectState:
        root = Path(state.root_path)
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in [
                ".py",
                ".js",
                ".ts",
                ".tsx",
                ".md",
                ".json",
                ".yaml",
            ]:
                state.files.append(str(path.relative_to(root)))

        state.stack = {
            "python": any(f.endswith(".py") for f in state.files),
            "node": any("package.json" in f for f in state.files),
            "react": any(f.endswith(".tsx") for f in state.files),
            "markdown_docs": any(f.endswith(".md") for f in state.files),
        }
        return state


class StructureAgent:
    def __init__(self) -> None:
        self.parser = CodeParser()

    def run(self, state: ProjectState) -> ProjectState:
        root = Path(state.root_path)
        for file in state.files:
            try:
                content = (root / file).read_text(errors="ignore")
                if file.endswith(".py"):
                    state.code_structure[file] = self.parser.parse_python(content)
                elif file.endswith((".js", ".ts", ".tsx", ".jsx")):
                    state.code_structure[file] = self.parser.parse_js(content)
            except Exception:
                continue
        return state


class AnalystAgent:
    def run(self, state: ProjectState) -> ProjectState:
        root = Path(state.root_path)
        for file in state.files[:100]:
            try:
                content = (root / file).read_text(errors="ignore")[:3000]
                lc = content.lower()
                if "auth" in lc or "login" in lc:
                    state.features.append({"feature": "authentication", "source": file})
                if "todo" in lc:
                    state.technical_debt.append({"type": "TODO_found", "file": file})
            except Exception:
                continue
        return state


class ArchitectAgent:
    def run(self, state: ProjectState) -> ProjectState:
        dependency_graph = {
            f: s.get("imports", []) for f, s in state.code_structure.items()
        }
        state.dependency_graph = dependency_graph

        modules = set(f.split("/")[-2] for f in state.files if len(f.split("/")) > 1)
        total_classes = sum(
            len(s.get("classes", [])) for s in state.code_structure.values()
        )
        total_functions = sum(
            len(s.get("functions", [])) for s in state.code_structure.values()
        )

        coupling = {f: len(i) for f, i in dependency_graph.items()}
        high_coupling = {f: c for f, c in coupling.items() if c >= 8}
        orphans = [f for f, imps in dependency_graph.items() if not imps]

        state.current_architecture = {
            "modules_detected": sorted(list(modules)),
            "total_classes": total_classes,
            "total_functions": total_functions,
            "high_coupling_files": high_coupling,
            "possible_orphans": orphans[:20],
            "dependency_cycles": detect_cycles(dependency_graph)[:10],
        }
        state.recommended_architecture = detect_pattern(state)
        return state


class PlannerAgent:
    def run(self, state: ProjectState) -> ProjectState:
        for debt in state.technical_debt:
            state.tasks.append(
                {"title": f"Resolve TODO in {debt['file']}", "priority": "medium"}
            )
        if state.current_architecture.get("dependency_cycles"):
            state.tasks.append(
                {"title": "Resolve dependency cycles", "priority": "high"}
            )
        return state


# ==========================================
# 4. CONDUCTOR & EXPORT
# ==========================================
def generate_markdown(state: ProjectState, health: dict) -> str:
    lines = [
        "# PROJECT CANON\n",
        f"## Health Score: {health['score']}/100 {health['label']}\n",
    ]
    if health["penalties"]:
        lines.extend(["### Penalties"] + [f"- {p}" for p in health["penalties"]])
    if health["bonuses"]:
        lines.extend(["\n### Bonuses"] + [f"- {b}" for b in health["bonuses"]])

    lines.append("\n## Stack Detected")
    lines.extend([f"- {k}: {v}" for k, v in state.stack.items()])

    lines.append("\n## Architecture Detected")
    lines.extend([f"- {k}: {v}" for k, v in state.current_architecture.items()])
    lines.append(
        f"\n## Recommended Architecture: {state.recommended_architecture.get('pattern')}"
    )

    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python vibe_consolidator.py /path/to/project")
        return

    BABYLON_SCRIPTS = os.path.expandvars("$CORTEX_ROOT/10_PROJECTS/babylon-60/scripts")
    if BABYLON_SCRIPTS not in sys.path:
        sys.path.append(BABYLON_SCRIPTS)
    try:
        from c5_guarded_action import boot_sequence, guarded_action  # type: ignore
    except ImportError:
        def boot_sequence(compensators):
            return None, None
        def guarded_action(conn, key, action_name, effect_fn):
            effect_fn()

    state = ProjectState(root_path=sys.argv[1])
    agents: list[Any] = [
        ScoutAgent(),
        StructureAgent(),
        AnalystAgent(),
        ArchitectAgent(),
        PlannerAgent(),
    ]
    for agent in agents:
        state = agent.run(state)

    health = score_project(state)
    mermaid = generate_mermaid(state.dependency_graph)

    out_dir = Path("outputs")
    out_dir.mkdir(exist_ok=True)

    conn, key = None, None
    execute = True
    if execute:
        compensators = {
            "VIBE_CONSOLIDATE_": lambda p: print(
                f"         [SAGA] Validando consolidación idempotente: {p}"
            )
        }
        try:
            conn, key = boot_sequence(compensators)
        except Exception:
            pass

    def _effect():
        (out_dir / "PROJECT_CANON.md").write_text(generate_markdown(state, health))
        (out_dir / "DIAGRAM.md").write_text(f"```mermaid\n{mermaid}\n```")
        (out_dir / "ARCHITECTURE.json").write_text(
            json.dumps(state.current_architecture, indent=2)
        )

    action_name = f"VIBE_CONSOLIDATE_{Path(sys.argv[1]).name}"
    if conn is not None:
        guarded_action(conn, key, action_name, _effect)
    else:
        _effect()

    print(f"✅ Consolidation complete. Health: {health['score']}/100 {health['label']}")
    print(f"Pattern: {state.recommended_architecture['pattern']}")


if __name__ == "__main__":
    main()
