# secretary_router.py — Nodo 4 (Secretario/Skill Router) for ULTRATHINK Swarm
# C5-REAL EXERGY CERTIFIED : KERNEL MOSKV-1 APEX
# Invariant: INV_C5_34 (Enrutamiento), Ω38 (Sharding), Ω160 (Stateful Load Shedding)

"""Nodo 4: El Secretario — Skill Router for the ULTRATHINK 9-Node Swarm.

Routes operator intent to the minimal subset of skills required by each Worker
(Nodo 5), preventing KV-Cache necrosis from monolithic skill loading.

Architecture:
    Oráculo (Nodo 1) → Ejecutivos (Nodo 2) → Secretario (Nodo 4) → Workers (Nodo 5)
                                                    ↓
                                          skill_registry.json
                                          (2_Nucleo_Estatico/)

The Secretario NEVER loads skills into its own context. It emits routing
descriptors — structured signatures of fixed bandwidth — that Workers consume
to activate the precise skill set needed for their task.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

log = logging.getLogger("ultrathink.secretary")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
# Find root of repo (Teorema-Robinson-Moskv) by checking parent directories for 2_Nucleo_Estatico
def _find_repo_root() -> Path:
    curr = Path(__file__).resolve()
    for parent in [curr] + list(curr.parents):
        if (parent / "2_Nucleo_Estatico").exists():
            return parent
    return curr.parents[3]

REPO_ROOT = _find_repo_root()
DEFAULT_REGISTRY_PATH = REPO_ROOT / "2_Nucleo_Estatico" / "skill_registry.json"
MAX_SKILLS_PER_WORKER = 3
TOKEN_BUDGET_PER_WORKER = 25_000  # bytes ≈ tokens * 4, conservative estimate


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SkillDescriptor:
    """Minimal descriptor for a skill in the registry."""
    name: str
    description: str
    plugin: str
    skill_dir_name: str
    skill_md_path: str
    size_bytes: int
    keywords: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, d: dict) -> "SkillDescriptor":
        return cls(
            name=d["name"],
            description=d["description"],
            plugin=d["plugin"],
            skill_dir_name=d["skill_dir_name"],
            skill_md_path=d["skill_md_path"],
            size_bytes=d["size_bytes"],
            keywords=tuple(d.get("keywords", ())),
        )


@dataclass
class RoutingResult:
    """Output of the Secretario: a routing descriptor for a Worker."""
    intent: str
    selected_skills: list[SkillDescriptor]
    total_bytes: int
    rejection_reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "intent": self.intent,
            "selected_skills": [asdict(s) for s in self.selected_skills],
            "total_bytes": self.total_bytes,
            "rejection_reason": self.rejection_reason,
        }


# ---------------------------------------------------------------------------
# Registry loader
# ---------------------------------------------------------------------------
class SkillRegistry:
    """Loads and indexes the skill registry for fast lookup.

    The registry is a JSON file containing an array of skill descriptors.
    On load, it builds an inverted index of keywords → skill descriptors
    for O(k) lookup where k = number of keywords in the intent.
    """

    def __init__(self, registry_path: Path = DEFAULT_REGISTRY_PATH):
        self._path = registry_path
        self._skills: list[SkillDescriptor] = []
        self._keyword_index: dict[str, list[int]] = {}
        self._loaded = False

    def load(self) -> None:
        """Load registry from disk and build inverted index."""
        if not self._path.exists():
            raise FileNotFoundError(
                f"Skill registry not found at {self._path}. "
                "Run the registry builder first."
            )
        with open(self._path, encoding="utf-8") as f:
            raw = json.load(f)

        self._skills = [SkillDescriptor.from_dict(entry) for entry in raw]
        self._build_index()
        self._loaded = True
        log.info(
            "Loaded %d skills from registry at %s",
            len(self._skills),
            self._path,
        )

    def _build_index(self) -> None:
        """Build inverted keyword index from skill names, descriptions, and explicit keywords."""
        self._keyword_index = {}
        for idx, skill in enumerate(self._skills):
            tokens = self._extract_tokens(skill)
            for token in tokens:
                if token not in self._keyword_index:
                    self._keyword_index[token] = []
                self._keyword_index[token].append(idx)

    # Minimum relevance score to include a skill in results.
    # Prevents noise from single-keyword cross-domain matches.
    MIN_RELEVANCE = 0.12

    @staticmethod
    def _extract_tokens(skill: SkillDescriptor) -> set[str]:
        """Extract normalized keyword tokens from a skill descriptor."""
        text = f"{skill.name} {skill.description} {' '.join(skill.keywords)} {skill.plugin}"
        return SkillRegistry._tokenize(text)

    # Shared stopword set for both registry and intent tokenization
    _STOPWORDS = {
        # English stopwords
        "the", "and", "for", "use", "when", "this", "that", "with",
        "from", "you", "are", "not", "has", "will", "can", "its",
        "also", "into", "was", "been", "have", "does", "did",
        # Domain-agnostic action verbs (cause cross-domain false positives)
        "fetch", "get", "set", "run", "add", "create", "build",
        "setup", "configure", "check", "find", "resolve", "using",
        "optimize", "debug", "fix", "update", "deploy", "manage",
        "based", "provides", "retrieve", "specific", "support",
        "guide", "helps", "ensure", "detect", "trigger",
        "analyze", "diagnose", "implement", "generate", "write",
        # Generic nouns that leak across domains
        "skill", "database", "query", "data", "search", "user",
        "file", "project", "config", "setting", "tool", "server",
        "request", "response", "error", "output", "input",
        "structure", "performance", "applications", "platform",
        "reports", "wants", "like", "high", "usage", "needs",
        "code", "scripts", "command", "line", "building",
        "testing", "running", "existing", "working", "package",
    }

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        """Normalize and tokenize text, filtering stopwords."""
        raw_tokens = re.split(r"[^a-z0-9]+", text.lower())
        return {t for t in raw_tokens if len(t) >= 3 and t not in SkillRegistry._STOPWORDS}

    @property
    def skills(self) -> list[SkillDescriptor]:
        return list(self._skills)

    def match(self, intent: str, max_results: int = MAX_SKILLS_PER_WORKER) -> list[tuple[SkillDescriptor, float]]:
        """Match an intent string against the registry.

        Returns skills sorted by relevance score (descending).
        Score = (matched_keywords / total_intent_keywords) * (1 / log2(size_bytes))
        to prefer smaller, more focused skills.

        Args:
            intent: The operator's goal or task description.
            max_results: Maximum number of skills to return.

        Returns:
            List of (SkillDescriptor, score) tuples.
        """
        if not self._loaded:
            self.load()

        # Apply the SAME stopword filtering to intent tokens
        intent_tokens = list(self._tokenize(intent))

        if not intent_tokens:
            return []

        # Phase 1: Raw keyword overlap scoring
        scores: dict[int, float] = {}
        for token in intent_tokens:
            if token in self._keyword_index:
                for idx in self._keyword_index[token]:
                    scores[idx] = scores.get(idx, 0) + 1.0

        if not scores:
            return []

        # Phase 2: Domain affinity — identify dominant plugin(s)
        # Count how many keyword hits each plugin receives
        plugin_hits: dict[str, float] = {}
        for idx, raw_score in scores.items():
            plugin = self._skills[idx].plugin
            plugin_hits[plugin] = plugin_hits.get(plugin, 0) + raw_score

        # The dominant plugin is the one with the most keyword hits
        dominant_plugin = max(plugin_hits, key=plugin_hits.get) if plugin_hits else None
        dominant_score = plugin_hits.get(dominant_plugin, 0) if dominant_plugin else 0

        # Phase 3: Score with domain affinity and size penalty
        import math
        DOMAIN_PENALTY = 0.3  # Out-of-domain skills get 30% of their score
        scored = []
        for idx, raw_score in scores.items():
            skill = self._skills[idx]
            # Relevance: fraction of intent tokens matched
            relevance = raw_score / len(intent_tokens)
            # Filter out low-relevance noise (Ω160: Stateful Load Shedding)
            if relevance < self.MIN_RELEVANCE:
                continue
            # Size penalty: prefer smaller skills (log2 scale)
            size_factor = 1.0 / max(1.0, math.log2(max(1, skill.size_bytes)))
            # Domain affinity: penalize out-of-domain skills when there's
            # a clear dominant domain (prevents cross-domain contamination
            # from shared tokens like 'structure', 'analyze', 'performance')
            domain_factor = 1.0
            if dominant_plugin and dominant_score >= 2.0 and skill.plugin != dominant_plugin:
                domain_factor = DOMAIN_PENALTY
            final_score = relevance * size_factor * domain_factor
            scored.append((skill, final_score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:max_results]


# ---------------------------------------------------------------------------
# Secretario (Nodo 4) — The Router
# ---------------------------------------------------------------------------
class SecretaryRouter:
    """Nodo 4: El Secretario.

    Receives operator intent, queries the SkillRegistry, and emits
    a RoutingResult that Workers (Nodo 5) consume to load the minimal
    skill set for their task.

    Invariants enforced:
        - MAX_SKILLS_PER_WORKER: No worker receives more than 3 skills
        - TOKEN_BUDGET_PER_WORKER: Total skill bytes cannot exceed budget
        - Stateful Load Shedding (Ω160): If budget is exceeded, skills are
          shed in order of lowest relevance score
    """

    def __init__(
        self,
        registry: Optional[SkillRegistry] = None,
        max_skills: int = MAX_SKILLS_PER_WORKER,
        token_budget: int = TOKEN_BUDGET_PER_WORKER,
    ):
        self._registry = registry or SkillRegistry()
        self._max_skills = max_skills
        self._token_budget = token_budget

    def route(self, intent: str) -> RoutingResult:
        """Route an operator intent to the minimal skill set.

        Args:
            intent: Natural language description of the task.

        Returns:
            RoutingResult with selected skills and metadata.
        """
        if not intent or not intent.strip():
            return RoutingResult(
                intent=intent,
                selected_skills=[],
                total_bytes=0,
                rejection_reason="Empty intent received. No routing possible.",
            )

        # Phase 1: Match against registry
        candidates = self._registry.match(intent, max_results=self._max_skills * 2)

        if not candidates:
            return RoutingResult(
                intent=intent,
                selected_skills=[],
                total_bytes=0,
                rejection_reason="No skills matched the intent. Worker operates in bare mode.",
            )

        # Phase 2: Budget-constrained selection (Ω160 Stateful Load Shedding)
        selected: list[SkillDescriptor] = []
        total_bytes = 0

        for skill, _score in candidates:
            if len(selected) >= self._max_skills:
                break
            if total_bytes + skill.size_bytes > self._token_budget:
                log.warning(
                    "Budget exceeded: dropping skill %s (%d bytes)",
                    skill.name,
                    skill.size_bytes,
                )
                continue
            selected.append(skill)
            total_bytes += skill.size_bytes

        rejection = None
        if not selected and candidates:
            rejection = (
                f"All {len(candidates)} candidate skills exceeded the token budget "
                f"of {self._token_budget} bytes."
            )

        return RoutingResult(
            intent=intent,
            selected_skills=selected,
            total_bytes=total_bytes,
            rejection_reason=rejection,
        )

    def route_to_yaml(self, intent: str) -> str:
        """Route and format the result as a YAML routing descriptor.

        This is the primary interface consumed by the scheduler and adapters.
        """
        result = self.route(intent)
        import yaml
        return yaml.dump(result.to_dict(), default_flow_style=False, allow_unicode=True)

    def route_to_json(self, intent: str) -> str:
        """Route and format the result as JSON."""
        result = self.route(intent)
        return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# CLI interface
# ---------------------------------------------------------------------------
def main() -> None:
    """CLI entry point for testing the Secretario router."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if len(sys.argv) < 2:
        print("Usage: python secretary_router.py <intent>")
        print("Example: python secretary_router.py 'fetch AlphaFold structure for P12345'")
        sys.exit(1)

    intent = " ".join(sys.argv[1:])
    router = SecretaryRouter()

    try:
        result = router.route(intent)
    except FileNotFoundError as e:
        print(f"\033[91m[C5-REAL ABORT]\033[0m {e}")
        sys.exit(1)

    print(f"\033[94m[NODO 4 — SECRETARIO]\033[0m Routing intent: {intent!r}")
    print(f"\033[94m[NODO 4]\033[0m Matched {len(result.selected_skills)} skills ({result.total_bytes} bytes)")

    if result.rejection_reason:
        print(f"\033[93m[NODO 4 WARNING]\033[0m {result.rejection_reason}")

    for i, skill in enumerate(result.selected_skills, 1):
        print(f"  [{i}] {skill.name} ({skill.plugin}) — {skill.size_bytes} bytes")
        print(f"      {skill.skill_md_path}")

    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
