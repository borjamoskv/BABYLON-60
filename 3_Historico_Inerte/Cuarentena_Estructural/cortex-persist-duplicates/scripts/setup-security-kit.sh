#!/bin/bash
# setup-security-kit.sh — Ejecutar en la raíz del repo

set -euo pipefail

echo "🔒 Instalando Kit P0 de Seguridad..."

# 1. Instalar pre-commit
pip install pre-commit gitleaks git-filter-repo 2>/dev/null || true
pre-commit install
pre-commit install --hook-type pre-push

# 2. Generar baseline de detect-secrets
detect-secrets scan > .secrets.baseline 2>/dev/null || true

# 3. Primer escaneo completo
echo ""
echo "🔍 Ejecutando escaneo inicial..."
echo "================================"
gitleaks detect --source . --verbose || true
echo ""
pre-commit run --all-files || true

echo ""
echo "✅ Kit P0 instalado."
echo "📌 Recuerda:"
echo "   1. Commitear los archivos de config (.pre-commit-config.yaml, .gitleaks.toml, .gitignore)"
echo "   2. Revisar los findings del escaneo inicial"
echo "   3. Compartir SECURITY_CLEANUP_PLAN.md con el equipo"
echo "   4. Configurar los secrets de GitHub Actions"
