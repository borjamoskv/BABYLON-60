# C5-REAL EXERGY CERTIFIED
"""Cortex Ontological Lexicon Transducer (cortex/lexicon.py)

Executable transducer for loading, verifying, and programmatically querying the
Sovereign Lexicon / Glosario (glosario.md) and Kernel Invariants (Ω0 - Ω179).
Converts natural language terms and invariant IDs into deterministic AST objects.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional


class LexiconEntry:
    """Represents a validated term or invariant within the C5-REAL ontology."""

    def __init__(self, key: str, term: str, category: str, description: str):
        self.key = key
        self.term = term
        self.category = category
        self.description = description

    def to_dict(self) -> Dict[str, str]:
        return {
            "key": self.key,
            "term": self.term,
            "category": self.category,
            "description": self.description,
        }


class LexiconEngine:
    """Engine for loading and querying C5-REAL ontology and invariant definitions."""

    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = root_dir or Path.cwd()
        self.glosario_path = self.root_dir / "glosario.md"
        self.agents_path = self.root_dir / ".agents" / "AGENTS.md"
        self.terms: Dict[str, LexiconEntry] = {}
        self.invariants: Dict[str, str] = {}
        self._load_lexicon()
        self._load_invariants()

    def _load_lexicon(self) -> None:
        if not self.glosario_path.exists():
            return
        content = self.glosario_path.read_text(encoding="utf-8", errors="replace")
        # Match pattern: **Term (Symbol)** \n Tipo: Category \n Description...
        pattern = re.compile(
            r"\*\*(?P<term>[^\*\(\n]+)(?:\s*\((?P<symbol>[^\)]+)\))?\*\*\nTipo:\s*(?P<category>[^\n]+)\n(?P<desc>.*?)(?=\n\*\*|\n---|\Z)",
            re.DOTALL,
        )
        for m in pattern.finditer(content):
            term = m.group("term").strip()
            category = m.group("category").strip()
            desc = m.group("desc").strip()
            key = term.lower().replace(" ", "_")
            self.terms[key] = LexiconEntry(
                key=key, term=term, category=category, description=desc
            )

    def _load_invariants(self) -> None:
        if not self.agents_path.exists():
            return
        content = self.agents_path.read_text(encoding="utf-8", errors="replace")
        pattern = re.compile(
            r"-\s*\*\*(?P<id>Ω\d+)\s*·\s*(?P<title>[^\*\:]+)\:\*\*\s*(?P<desc>[^\n]+)"
        )
        for m in pattern.finditer(content):
            inv_id = m.group("id").strip()
            title = m.group("title").strip()
            desc = m.group("desc").strip()
            self.invariants[inv_id] = f"{title}: {desc}"

    def get_term(self, key: str) -> Optional[LexiconEntry]:
        return self.terms.get(key.lower().replace(" ", "_"))

    def get_invariant(self, inv_id: str) -> Optional[str]:
        return self.invariants.get(inv_id.upper())

    def search(self, query: str) -> List[LexiconEntry]:
        q = query.lower()
        return [
            entry
            for entry in self.terms.values()
            if q in entry.term.lower() or q in entry.description.lower()
        ]


# Singleton instance for quick execution
default_lexicon = LexiconEngine()


def lookup_term(term: str) -> Optional[Dict[str, str]]:
    entry = default_lexicon.get_term(term)
    return entry.to_dict() if entry else None


def lookup_invariant(inv_id: str) -> Optional[str]:
    return default_lexicon.get_invariant(inv_id)
