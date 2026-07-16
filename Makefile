.PHONY: all check test lint typecheck format

all: format lint typecheck test

check: lint typecheck

lint:
	ruff check babylon60 tests
	ruff format --check babylon60 tests

format:
	ruff check --fix babylon60 tests
	ruff format babylon60 tests

typecheck:
	mypy babylon60 tests --strict --ignore-missing-imports

test:
	pytest tests/ -v
