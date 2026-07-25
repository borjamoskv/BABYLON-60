.PHONY: all check test lint type-check typecheck format backend build clean audit rust-test rust-clippy seal

all: lint type-check test

check: lint typecheck

test:
	.venv/bin/python -m pytest tests/ -x --tb=short -q

lint:
	.venv/bin/ruff check .

format:
	.venv/bin/ruff format .

type-check:
	.venv/bin/mypy babylon60/ --ignore-missing-imports

typecheck: type-check

build:
	.venv/bin/python -m build

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +

audit:
	.venv/bin/python scripts/exergy_optimizer_agent.py
	.venv/bin/python scripts/autodetect_invariants.py

rust-test:
	cd strike_rs && cargo test

rust-clippy:
	cd strike_rs && cargo clippy -- -D warnings

seal:
	.venv/bin/python scripts/terminal_seal.py

backend:
	python3 run_backend.py
