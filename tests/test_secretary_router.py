# tests/test_secretary_router.py — Unit tests for Nodo 4 (Secretario/Skill Router)
# C5-REAL EXERGY CERTIFIED

"""Tests for the SecretaryRouter and SkillRegistry.

Tests verify:
    - Registry loading from JSON
    - Keyword extraction and indexing
    - Intent matching with correct skill selection
    - Budget constraint enforcement (MAX_SKILLS, TOKEN_BUDGET)
    - Edge cases (empty intent, no matches, exact match)
    - Relevance threshold filtering (MIN_RELEVANCE)
"""

import json
import tempfile
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "1_Operaciones_Activas" / "BABYLON-60"))

from ultrathink.secretary_router import (
    SecretaryRouter,
    SkillDescriptor,
    SkillRegistry,
    RoutingResult,
    MAX_SKILLS_PER_WORKER,
    TOKEN_BUDGET_PER_WORKER,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
SAMPLE_REGISTRY = [
    {
        "name": "alphafold-database-fetch-and-analyze",
        "description": "Retrieve and analyze AlphaFold predicted structures for a protein.",
        "plugin": "science",
        "skill_dir_name": "alphafold_database_fetch_and_analyze",
        "skill_md_path": "/fake/path/alphafold/SKILL.md",
        "size_bytes": 4760,
        "keywords": ["alphafold", "protein", "structure", "plddt"],
    },
    {
        "name": "pubmed-database",
        "description": "Search PubMed for scientific literature, including published clinical trials.",
        "plugin": "science",
        "skill_dir_name": "pubmed_database",
        "skill_md_path": "/fake/path/pubmed/SKILL.md",
        "size_bytes": 8343,
        "keywords": ["pubmed", "literature", "clinical", "trials", "papers"],
    },
    {
        "name": "flutter-add-widget-test",
        "description": "Implement a component-level test using WidgetTester to verify UI rendering.",
        "plugin": "flutter",
        "skill_dir_name": "flutter_add_widget_test",
        "skill_md_path": "/fake/path/flutter_widget_test/SKILL.md",
        "size_bytes": 6511,
        "keywords": ["flutter", "widget", "test", "tester", "rendering"],
    },
    {
        "name": "firebase-auth-basics",
        "description": "Guide for setting up and using Firebase Authentication.",
        "plugin": "firebase",
        "skill_dir_name": "firebase_auth_basics",
        "skill_md_path": "/fake/path/firebase_auth/SKILL.md",
        "size_bytes": 4153,
        "keywords": ["firebase", "auth", "authentication", "sign"],
    },
    {
        "name": "bigquery-sql",
        "description": "Provides BigQuery SQL query optimization techniques.",
        "plugin": "data-agent-kit-plugin",
        "skill_dir_name": "bigquery_sql",
        "skill_md_path": "/fake/path/bigquery_sql/SKILL.md",
        "size_bytes": 1764,
        "keywords": ["bigquery", "sql", "optimization", "performance"],
    },
    {
        "name": "huge-skill-overflow",
        "description": "A massive skill that tests budget constraints.",
        "plugin": "test",
        "skill_dir_name": "huge_skill",
        "skill_md_path": "/fake/path/huge/SKILL.md",
        "size_bytes": 30000,
        "keywords": ["huge", "massive", "overflow"],
    },
]


@pytest.fixture
def registry_path(tmp_path: Path) -> Path:
    """Create a temporary registry JSON file."""
    registry_file = tmp_path / "skill_registry.json"
    registry_file.write_text(json.dumps(SAMPLE_REGISTRY), encoding="utf-8")
    return registry_file


@pytest.fixture
def registry(registry_path: Path) -> SkillRegistry:
    """Create a loaded SkillRegistry."""
    r = SkillRegistry(registry_path)
    r.load()
    return r


@pytest.fixture
def router(registry: SkillRegistry) -> SecretaryRouter:
    """Create a SecretaryRouter with the sample registry."""
    return SecretaryRouter(registry=registry)


# ---------------------------------------------------------------------------
# Registry Tests
# ---------------------------------------------------------------------------
class TestSkillRegistry:
    def test_load_counts(self, registry: SkillRegistry):
        """Registry loads all skills from JSON."""
        assert len(registry.skills) == len(SAMPLE_REGISTRY)

    def test_load_missing_file(self, tmp_path: Path):
        """Registry raises FileNotFoundError for missing file."""
        r = SkillRegistry(tmp_path / "nonexistent.json")
        with pytest.raises(FileNotFoundError):
            r.load()

    def test_keyword_index_populated(self, registry: SkillRegistry):
        """Keyword index is populated with domain-specific tokens."""
        # "alphafold" should be in the index
        assert "alphafold" in registry._keyword_index
        # "pubmed" should be in the index
        assert "pubmed" in registry._keyword_index
        # "flutter" should be in the index
        assert "flutter" in registry._keyword_index

    def test_stopwords_not_in_index(self, registry: SkillRegistry):
        """Stopwords should NOT appear in the keyword index."""
        for stopword in ["the", "and", "for", "fetch", "database", "search"]:
            assert stopword not in registry._keyword_index

    def test_match_alphafold(self, registry: SkillRegistry):
        """AlphaFold-related intent should match the alphafold skill."""
        matches = registry.match("analyze AlphaFold protein structure")
        assert len(matches) >= 1
        skill_names = [m[0].name for m in matches]
        assert "alphafold-database-fetch-and-analyze" in skill_names

    def test_match_pubmed(self, registry: SkillRegistry):
        """PubMed-related intent should match the pubmed skill."""
        matches = registry.match("find PubMed papers on gene therapy")
        assert len(matches) >= 1
        skill_names = [m[0].name for m in matches]
        assert "pubmed-database" in skill_names

    def test_match_no_results(self, registry: SkillRegistry):
        """Completely unrelated intent should return no matches."""
        matches = registry.match("solve Riemann hypothesis")
        assert len(matches) == 0

    def test_match_respects_max_results(self, registry: SkillRegistry):
        """Match should respect max_results parameter."""
        matches = registry.match("alphafold protein flutter widget", max_results=2)
        assert len(matches) <= 2


# ---------------------------------------------------------------------------
# Router Tests
# ---------------------------------------------------------------------------
class TestSecretaryRouter:
    def test_route_empty_intent(self, router: SecretaryRouter):
        """Empty intent should return empty result with rejection reason."""
        result = router.route("")
        assert result.selected_skills == []
        assert result.rejection_reason is not None
        assert "Empty" in result.rejection_reason

    def test_route_whitespace_intent(self, router: SecretaryRouter):
        """Whitespace-only intent should return empty result."""
        result = router.route("   ")
        assert result.selected_skills == []

    def test_route_flutter_intent(self, router: SecretaryRouter):
        """Flutter intent should route to Flutter skills."""
        result = router.route("add a widget test for Flutter")
        assert len(result.selected_skills) >= 1
        plugins = {s.plugin for s in result.selected_skills}
        assert "flutter" in plugins

    def test_route_no_match(self, router: SecretaryRouter):
        """Unrelated intent should return no skills."""
        result = router.route("compile Haskell program with GHC")
        assert result.selected_skills == []
        assert result.rejection_reason is not None

    def test_route_respects_max_skills(self, registry: SkillRegistry):
        """Router should never return more than max_skills."""
        router = SecretaryRouter(registry=registry, max_skills=1)
        result = router.route("alphafold protein flutter widget bigquery sql")
        assert len(result.selected_skills) <= 1

    def test_route_respects_token_budget(self, registry: SkillRegistry):
        """Router should enforce token budget constraint."""
        router = SecretaryRouter(registry=registry, token_budget=5000)
        result = router.route("alphafold protein structure")
        assert result.total_bytes <= 5000

    def test_route_total_bytes_correct(self, router: SecretaryRouter):
        """total_bytes should equal sum of selected skill sizes."""
        result = router.route("add a widget test for Flutter")
        expected = sum(s.size_bytes for s in result.selected_skills)
        assert result.total_bytes == expected

    def test_route_to_json(self, router: SecretaryRouter):
        """route_to_json should return valid JSON."""
        json_str = router.route_to_json("alphafold protein structure")
        parsed = json.loads(json_str)
        assert "intent" in parsed
        assert "selected_skills" in parsed
        assert isinstance(parsed["selected_skills"], list)


# ---------------------------------------------------------------------------
# SkillDescriptor Tests
# ---------------------------------------------------------------------------
class TestSkillDescriptor:
    def test_from_dict(self):
        """SkillDescriptor.from_dict should parse a registry entry."""
        d = SAMPLE_REGISTRY[0]
        skill = SkillDescriptor.from_dict(d)
        assert skill.name == "alphafold-database-fetch-and-analyze"
        assert skill.plugin == "science"
        assert skill.size_bytes == 4760

    def test_from_dict_missing_keywords(self):
        """SkillDescriptor.from_dict should handle missing keywords."""
        d = {
            "name": "test-skill",
            "description": "A test skill",
            "plugin": "test",
            "skill_dir_name": "test_skill",
            "skill_md_path": "/fake/path",
            "size_bytes": 100,
        }
        skill = SkillDescriptor.from_dict(d)
        assert skill.keywords == ()

    def test_frozen_immutable(self):
        """SkillDescriptor should be immutable (frozen dataclass)."""
        skill = SkillDescriptor.from_dict(SAMPLE_REGISTRY[0])
        with pytest.raises(AttributeError):
            skill.name = "modified"


# ---------------------------------------------------------------------------
# RoutingResult Tests
# ---------------------------------------------------------------------------
class TestRoutingResult:
    def test_to_dict(self):
        """RoutingResult.to_dict should produce a valid dictionary."""
        skill = SkillDescriptor.from_dict(SAMPLE_REGISTRY[0])
        result = RoutingResult(
            intent="test intent",
            selected_skills=[skill],
            total_bytes=skill.size_bytes,
        )
        d = result.to_dict()
        assert d["intent"] == "test intent"
        assert len(d["selected_skills"]) == 1
        assert d["total_bytes"] == 4760
        assert d["rejection_reason"] is None

    def test_to_dict_with_rejection(self):
        """RoutingResult.to_dict should include rejection_reason."""
        result = RoutingResult(
            intent="empty",
            selected_skills=[],
            total_bytes=0,
            rejection_reason="No match",
        )
        d = result.to_dict()
        assert d["rejection_reason"] == "No match"
