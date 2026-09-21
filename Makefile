.PHONY: all check test lint typecheck format

all: format lint typecheck test

check: lint typecheck

lint:
	ruff check 01_KISH_ENGINE/babylon60 02_EDIN_SWARMS/agents_archi tests
	ruff format --check 01_KISH_ENGINE/babylon60 02_EDIN_SWARMS/agents_archi tests

format:
	ruff check --fix 01_KISH_ENGINE/babylon60 02_EDIN_SWARMS/agents_archi tests
	ruff format 01_KISH_ENGINE/babylon60 02_EDIN_SWARMS/agents_archi tests

typecheck:
	mypy 01_KISH_ENGINE/babylon60 02_EDIN_SWARMS/agents_archi tests --strict --ignore-missing-imports

test:
	pytest tests/ -v
