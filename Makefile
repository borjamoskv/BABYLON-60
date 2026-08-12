.PHONY: all check test lint typecheck format backend

all: format lint typecheck test

check: lint typecheck

lint:
	ruff check packages/babylon60 tests
	ruff format --check packages/babylon60 tests

format:
	ruff check --fix packages/babylon60 tests
	ruff format packages/babylon60 tests

typecheck:
	mypy packages/babylon60 tests --strict --ignore-missing-imports

test:
	pytest tests/ -v

backend:
	python3 run_backend.py
