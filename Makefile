.PHONY: help status test intel engine studio lab sync audit

help:
	@./moskv --help

status:
	@./moskv status

test:
	@./moskv test

intel:
	@./moskv intel

engine:
	@./moskv engine

studio:
	@./moskv studio

lab:
	@./moskv lab

sync:
	@./moskv sync

audit:
	@python3 /Users/borjafernandezangulo/.gemini/antigravity/scratch/legion_100_agents_audit.py

build-guard:
	@echo "[ULTRATHINK] Compiling Native C-Extension OUT-OF-TREE (/tmp/cortex_exergy_build)..."
	@mkdir -p /tmp/cortex_exergy_build
	@cd cortex_guard && uv run python setup.py build_ext --build-lib /tmp/cortex_exergy_build --build-temp /tmp/cortex_exergy_build/temp

