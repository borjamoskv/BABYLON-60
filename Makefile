# SIESAS_TRANSMUTATION_PROTOCOL
# Fricción cognitiva máxima. Sin advertencias, solo errores fatales.

SIESAS_LINT:
	@echo "[SIESAS] Purgando Anergía..."
	python3 -m core.thermo_ast_pruner core/*.py bft/*.py scripts/*.py
	
	@echo "[SIESAS] Forzando tipado (Mypy)..."
	mypy .
	
	@echo "[SIESAS] Verificación de integridad BFT..."
	python3 -m bft.consensus_ledger --audit-mode
	
	@echo "[SIESAS] Verificación de inyección de prompts indirecta (IPI)..."
	python3 cortex/scripts/sanitize_ipi_payloads.py
	
	@echo "[SIESAS] Compilación a Exergía completada."
