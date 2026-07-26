# C5-REAL EXERGY CERTIFIED
"""Cortex Ontological Lexicon Transducer (cortex/lexicon.py)

Executable transducer for loading, verifying, and programmatically querying the
Sovereign Lexicon / Glosario (glosario.md) and Kernel Invariants (Ω0 - Ω187).
Converts natural language terms and invariant IDs into deterministic AST objects.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, TypedDict

# Pre-compilación exergética en el espacio de nombres global (evita re-compilar en cada init)
RE_GLOSARIO = re.compile(
    r"\*\*(?P<term>[^\*\(\n]+)(?:\s*\((?P<symbol>[^\)]+)\))?\*\*\nTipo:\s*(?P<category>[^\n]+)\n(?P<desc>.*?)(?=\n\*\*|\n---|\Z)",
    re.DOTALL
)
RE_INVARIANTES = re.compile(r"-\s*\*\*(?P<id>Ω\d+)\s*·\s*(?P<title>[^\*\:]+)\:\*\*\s*(?P<desc>[^\n]+)")

class LexiconDict(TypedDict):
    key: str
    term: str
    category: str
    description: str

class LexiconEntry:
    """Estructura de memoria optimizada mediante __slots__ (Cero overhead de __dict__)."""
    __slots__ = ("key", "term", "category", "description")

    def __init__(self, key: str, term: str, category: str, description: str) -> None:
        self.key: str = key
        self.term: str = term
        self.category: str = category
        self.description: str = description

    def to_dict(self) -> LexiconDict:
        return {
            "key": self.key,
            "term": self.term,
            "category": self.category,
            "description": self.description,
        }

class LexiconEngine:
    """Motor optimizado de carga única para la ontología C5-REAL."""
    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self.root_dir: Path = root_dir or Path.cwd()
        self.glosario_path: Path = self.root_dir / "glosario.md"
        self.agents_path: Path = self.root_dir / "AGENTS.md"
        self.terms: Dict[str, LexiconEntry] = {}
        self.invariants: Dict[str, str] = {}
        self._load_lexicon()
        self._load_invariants()

    def _load_lexicon(self) -> None:
        if not self.glosario_path.exists():
            return
        # Lectura directa de bytes mapeados si es posible para optimizar I/O
        content = self.glosario_path.read_text(encoding="utf-8", errors="replace")
        for m in RE_GLOSARIO.finditer(content):
            term = m.group("term").strip()
            key = term.lower().replace(" ", "_")
            self.terms[key] = LexiconEntry(
                key=key,
                term=term,
                category=m.group("category").strip(),
                description=m.group("desc").strip()
            )

    def _load_invariants(self) -> None:
        if not self.agents_path.exists():
            return
        content = self.agents_path.read_text(encoding="utf-8", errors="replace")
        for m in RE_INVARIANTES.finditer(content):
            self.invariants[m.group("id").strip().upper()] = f"{m.group('title').strip()}: {m.group('desc').strip()}"

    def get_term(self, key: str) -> Optional[LexiconEntry]:
        return self.terms.get(key.lower().replace(" ", "_"))

    def get_invariant(self, inv_id: str) -> Optional[str]:
        return self.invariants.get(inv_id.upper())

    def search(self, query: str) -> List[LexiconEntry]:
        q = query.lower()
        return [entry for entry in self.terms.values() if q in entry.key or q in entry.description.lower()]

# Singleton de ejecución inmediata
default_lexicon = LexiconEngine()

def lookup_term(term: str) -> Optional[LexiconDict]:
    entry = default_lexicon.get_term(term)
    return entry.to_dict() if entry else None

def lookup_invariant(inv_id: str) -> Optional[str]:
    return default_lexicon.get_invariant(inv_id)
