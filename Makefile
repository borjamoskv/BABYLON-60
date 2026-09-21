.PHONY: all check test test-python test-rust test-quality test-sovereign lint typecheck format sovereign quality

all: format lint typecheck test-rust test-python test-quality test-sovereign

check: lint typecheck

lint:
	ruff check 01_KISH_ENGINE/babylon60 02_EDIN_SWARMS/agents_archi tests
	ruff format --check 01_KISH_ENGINE/babylon60 02_EDIN_SWARMS/agents_archi tests

format:
	ruff check --fix 01_KISH_ENGINE/babylon60 02_EDIN_SWARMS/agents_archi tests
	ruff format 01_KISH_ENGINE/babylon60 02_EDIN_SWARMS/agents_archi tests

typecheck:
	mypy 01_KISH_ENGINE/babylon60 02_EDIN_SWARMS/agents_archi tests --strict --ignore-missing-imports

test-python:
	pytest tests/ -q

test-rust:
	cargo test --workspace --quiet

test-quality:
	python3 scripts/c5_quality_gates/lint_doc_aesthetics.py
	python3 scripts/c5_quality_gates/secret_swarm_auditor.py

test-sovereign:
	python3 scripts/c5_demos/c5_sovereign_compliance_orchestrator.py

test: test-rust test-python

sovereign: test-sovereign
quality: test-quality
