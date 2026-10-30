.PHONY: all check docs-check test test-python test-rust test-quality test-sovereign lint typecheck format sovereign quality test-deps swarm-test swarm-audit swarm-batch-sign swarm-social swarm-top swarm-attestation

all: format lint typecheck test-rust test-python test-quality test-sovereign

check: lint typecheck

docs-check:
	python3 scripts/c5_quality_gates/sync_docs_index.py --check
	python3 scripts/c5_quality_gates/audit_semantic_contracts.py --workspace-only
	python3 scripts/c5_quality_gates/audit_token_budget.py --workspace-only --skip-ghost-listeners
	python3 scripts/guards/verify_active_topology.py

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

test-claims:
	python3 scripts/c5_quality_gates/verify_claims.py

test-swarm:
	python3 scripts/c5_quality_gates/swarm_100_stress_campaign.py

test-loom:
	cargo test --test seqlock_loom --release

test-lean:
	cd proof/lean && lake build

test-deps:
	cargo audit
	uv lock --check
	python3 scripts/c5_quality_gates/anti_slopsquatting_guard.py --all
	python3 scripts/c5_quality_gates/audit_license_compliance.py

test-quality: test-deps
	python3 scripts/c5_quality_gates/lint_doc_aesthetics.py
	python3 scripts/c5_quality_gates/secret_swarm_auditor.py
	python3 scripts/c5_quality_gates/audit_ring2_sqlite_isolation.py
	python3 scripts/c5_quality_gates/audit_domain_bleed.py

test-sovereign:
	python3 scripts/c5_demos/c5_sovereign_compliance_orchestrator.py

test: test-rust test-python test-claims test-swarm test-lean

sync-version:
	python3 scripts/c5_quality_gates/sync_version.py --sync

check-version:
	python3 scripts/c5_quality_gates/sync_version.py --check

release-manifest: sync-version test-claims
	python3 scripts/c5_quality_gates/compile_claims_manifest.py

sovereign: test-sovereign
quality: test-quality

swarm-test:
	pytest tests/test_distribution_and_social_swarms.py -v

swarm-audit:
	python3 tools/tamkarum_swarm_orchestrator.py --pipeline all --limit 10

swarm-batch-sign:
	python3 tools/tamkarum_batch_signer.py --campaign all

swarm-social:
	python3 tools/social_calendar_generator.py --validate-all

swarm-top:
	python3 tools/tamkarum_top.py --once

swarm-attestation:
	python3 tools/tamkarum_attestation_engine.py --emit
	python3 tools/tamkarum_attestation_engine.py --verify



ci-local:
	bash scripts/ci_local.sh

ship:
	bash scripts/c5_git_utils/c5_ship.sh "$(MSG)"

sellar: ship

estado:
	bash scripts/c5_git_utils/c5_ship.sh --status

status: estado
