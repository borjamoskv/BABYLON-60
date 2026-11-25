.PHONY: all check test test-python test-python-nonative native-test-libs test-rust test-z3 test-loom test-quality test-sovereign lint typecheck format sovereign quality test-deps

all: format lint typecheck test-rust test-python test-quality test-sovereign

check: lint typecheck

# Use the project SDK and tools together; global mypy can resolve a different MCP API.
# Provision once with: uv sync --locked --extra dev --extra gemini
lint:
	uv run --no-sync ruff check 01_KISH_ENGINE/babylon60 02_EDIN_SWARMS/agents_archi tests
	uv run --no-sync ruff format --check 01_KISH_ENGINE/babylon60 02_EDIN_SWARMS/agents_archi tests

format:
	ruff check --fix 01_KISH_ENGINE/babylon60 02_EDIN_SWARMS/agents_archi tests
	ruff format 01_KISH_ENGINE/babylon60 02_EDIN_SWARMS/agents_archi tests

typecheck:
	uv run --no-sync mypy 01_KISH_ENGINE/babylon60 02_EDIN_SWARMS/agents_archi tests --strict --ignore-missing-imports

# Native libraries the Python suite needs; without them ~100+ tests skip
# ("native broker missing", "libb60_lang no compilada"). Same builds as
# python-tests.yml plus the geometry library of ci.yml; Landlock is not required.
# Explicit --target-dir keeps the paths below valid when CARGO_TARGET_DIR is set.
NATIVE_LIB_EXT := $(if $(filter Darwin,$(shell uname -s)),dylib,so)
NATIVE_DEFAULT_LIB := $(CURDIR)/target/debug/libbabylon60.$(NATIVE_LIB_EXT)
NATIVE_PY_LIB := $(CURDIR)/target/py/debug/libbabylon60.$(NATIVE_LIB_EXT)

native-test-libs:
	cargo build --locked -p babylon-attest -p babylon60_root --lib --bins --target-dir target
	cargo build --locked -p babylon60_root --lib --features python --target-dir target/py

test-python: native-test-libs
	BABYLON60_REQUIRE_NATIVE=1 \
	BABYLON60_DYLIB_PATH="$(NATIVE_DEFAULT_LIB)" \
	BABYLON60_TEST_CAPABILITY_LIBRARY="$(NATIVE_PY_LIB)" \
	CORTEX_MEMORY_BROKER_LIB="$(NATIVE_PY_LIB)" \
	BABYLON60_TEST_GEOMETRY_LIBRARY="$(NATIVE_PY_LIB)" \
	uv run --locked --no-sync pytest -q -rs --maxfail=0

# Fast path without the native build; native-dependent tests skip.
test-python-nonative:
	pytest -q

test-rust:
	cargo test --workspace --quiet

# Regressions that only pass with the audited Z3 binary (BLAKE3 pin in the
# babylon60-compiler test support); plain `cargo test` ignores them.
# Never --include-ignored: it would run replay_worker, which needs its own fixture.
# Keep this list in sync with the #[ignore] attributes: --exact runs nothing for a stale name.
BABYLON_Z3_BIN ?= /opt/homebrew/bin/z3

test-z3:
	BABYLON_Z3_BIN="$(BABYLON_Z3_BIN)" cargo test --locked -p babylon60-compiler \
		--test solver_trust --test semantic_solver_adapter --no-fail-fast -- --ignored --exact \
		approved_real_binary_runs_and_query_is_reserved_and_consumed_once \
		wrong_query_does_not_consume_the_correct_receipt \
		unknown_unsat_and_process_error_receipts_are_consumed_too \
		real_sat_and_unsat_reach_all_four_entropy_variants \
		real_unknown_retains_resource_reason_and_cannot_be_admitted \
		receipt_rejects_other_request_body_partition_and_policy \
		separate_processes_do_not_retain_previous_assertions \
		real_parser_handles_comments_quoted_symbols_and_strings \
		real_solver_parse_error_never_accepts_later_sat_output \
		negative_processes::temporary_io_failure_preserves_transport_error

test-claims:
	python3 scripts/c5_quality_gates/verify_claims.py

test-swarm:
	python3 scripts/c5_quality_gates/swarm_100_stress_campaign.py

test-loom:
	LOOM_MAX_PREEMPTIONS=2 RUSTFLAGS="--cfg loom" CARGO_TARGET_DIR="$${CARGO_TARGET_DIR:-target/loom}" cargo test --locked --test seqlock_loom --release
	LOOM_MAX_PREEMPTIONS=2 RUSTFLAGS="--cfg loom" CARGO_TARGET_DIR="$${CARGO_TARGET_DIR:-target/loom}" cargo test --locked --lib tamkarum --release

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
	python3 scripts/c5_quality_gates/detect_ghost_nodes.py --scope product

test-sovereign:
	python3 scripts/c5_demos/c5_sovereign_compliance_orchestrator.py

test: test-rust test-python test-claims test-swarm test-lean

sync-version:
	python3 scripts/c5_quality_gates/sync_version.py --sync

check-version:
	python3 scripts/c5_quality_gates/sync_version.py --check

release-manifest: sync-version test-claims
	python3 scripts/c5_quality_gates/compile_claims_manifest.py

# Tracked evidence on main after squash merges: report freshness, or regenerate it in the
# dedicated worktree .worktrees/evidence-refresh as one generated-only commit citing origin/main.
.PHONY: evidence-status evidence-refresh
evidence-status:
	python3 scripts/c5_quality_gates/refresh_tracked_evidence.py --check --fetch

evidence-refresh:
	python3 scripts/c5_quality_gates/refresh_tracked_evidence.py

sovereign: test-sovereign
quality: test-quality



ci-local:
	bash scripts/ci_local.sh

ship:
	bash scripts/c5_git_utils/c5_ship.sh "$(MSG)"

sellar: ship

estado:
	bash scripts/c5_git_utils/c5_ship.sh --status

status: estado
