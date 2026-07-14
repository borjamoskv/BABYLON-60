# SIESAS_TRANSMUTATION_PROTOCOL
# Fricción cognitiva máxima. Sin advertencias, solo errores fatales.

SIESAS_LINT:
	@echo "[SIESAS] Purgando Anergía..."
	python -m core.thermo_ast_pruner src/legacy/**/*.py
	
	@echo "[SIESAS] Forzando tipado estricto (Mypy nivel máximo)..."
	mypy --strict --disallow-untyped-defs src/
	
	@echo "[SIESAS] Verificación de integridad BFT..."
	python -m bft.consensus_ledger --audit-mode
	
	@echo "[SIESAS] Compilación a Exergía completada."
