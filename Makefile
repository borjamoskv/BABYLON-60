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
