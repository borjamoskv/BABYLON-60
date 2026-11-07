.PHONY: setup start-agent

setup:
	@echo "[+] Verificando e instalando dependencias agénticas de coste marginal cero..."
	@pip install -q ollama mcp || echo "[!] Advertencia: No se pudo instalar el paquete Python."
	@npm install -g @modelcontextprotocol/server-sqlite @modelcontextprotocol/server-filesystem
	@echo "[+] Setup de Fricción Cero completado."

start-agent:
	@echo "[+] Iniciando Spark Soberano (Sistema 1 Local)..."
	@python3 sovereign_spark.py
