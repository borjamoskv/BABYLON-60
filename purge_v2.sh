# C5-REAL EXERGY CERTIFIED
#!/bin/bash
set -e

echo "Iniciando purga V2 con git filter-repo..."

git filter-repo --force \
  --path-glob "**/cortex/legal_dossier" \
  --path "cortex/legal_dossier" \
  --path-glob "**/cortex/legal_dossier/*" \
  --path-glob "**/osint_proxy_full_profile.yaml" \
  --path "osint_proxy_full_profile.yaml" \
  --path-glob "**/analisis_osint_proxy_*.yaml" \
  --path-glob "analisis_osint_proxy_*.yaml" \
  --path-glob "**/OSINT_AUDIT_BAKALADETROYA_*.md" \
  --path-glob "OSINT_AUDIT_BAKALADETROYA_*.md" \
  --path-glob "**/osint_bakaladetroya_apex_node.yaml" \
  --path "osint_bakaladetroya_apex_node.yaml" \
  --path-glob "**/C5_RESUMEN_PERICIAL_HERMANA_LORENA.md" \
  --path "C5_RESUMEN_PERICIAL_HERMANA_LORENA.md" \
  --path-glob "**/C5_MENSAJE_ACTUALIZADO_ABOGADO_RICARDO.md" \
  --path "C5_MENSAJE_ACTUALIZADO_ABOGADO_RICARDO.md" \
  --path-glob "**/AUDITORIA_ATOMICA*.md" \
  --path-glob "AUDITORIA_ATOMICA*.md" \
  --path-glob "**/reporte_anthropic_hermana.md" \
  --path "reporte_anthropic_hermana.md" \
  --path-glob "**/crystallization_20260718002627437510.yaml" \
  --path "crystallization_20260718002627437510.yaml" \
  --invert-paths

echo "Purga V2 finalizada exitosamente."
