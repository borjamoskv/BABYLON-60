.PHONY: help install dev test lint format clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install BABYLON-60 (Zero Anergy)
	curl -sSL https://raw.githubusercontent.com/borjamoskv/BABYLON-60/main/bootstrap.sh | bash

dev: ## Install with dev dependencies
	uv pip install -e ".[dev]"

test: ## Run strict determinism tests
	.venv/bin/pytest tests/ -v

lint: ## Run linter
	ruff check babylon60/ tests/

format: ## Auto-format code
	ruff format babylon60/ tests/

clean: ## Purge entropy
	rm -rf dist/ build/ *.egg-info site/ .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
