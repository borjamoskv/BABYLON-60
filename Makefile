.PHONY: all check test lint typecheck format backend install-hooks

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

backend:
	python3 run_backend.py

# Purga Entropía v3 — activa el ENTROPY GUARD (pre-commit)
install-hooks:
	chmod +x .githooks/pre-commit
	git config core.hooksPath .githooks
	@echo "ENTROPY GUARD activo — los commits pasan por .githooks/pre-commit"
