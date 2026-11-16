# Contrato — Lote 8 (29/10/2026, Europe/Madrid)

C0499/C0500: única fuente productiva editable scripts/c5_cortex/cortex_objectives_transducer.py.
Reproducir primero en repositorios temporales, HOME/config Git propios y hooks inocuos.
No ejecutar helper ni commits en checkout real, ni red/push/hardware/ATTESTED.
Preservar cambios ajenos, dependencias/lockfiles y evidencia histórica.

Ring-2 (Git/hooks/índice) y Ring-3 (CLI/documentos). Sin reintento --no-verify;
solo YAML/PROJECT previstos. Rechazar índice preparado antes de mutarlo y
conservar staging/HEAD ajenos; fallo no devuelve hash de éxito. Restaurar solo
preparación propia, conservar árbol de trabajo. No reset --hard/clean/stash.

Aceptación: red/green, casos limpios/rechazo/hooks/errores/índice y archivos
ajenos, consumidores, Ruff/MyPy, suite relacionada, revisión independiente,
registro reconciliado y controles documentales. Lote 9 solo se prepara.
MCP graph disponible: project babylon-60, raíz exacta contrastada, cobertura
best-effort metadata_match para esta fuente; cuatro consumidores identificados.

Refinamiento previo al parche: git commit --only sobre el subconjunto de
resultados realmente generado por cada consumidor sustituye git add+rollback
manual. Git conserva hooks y descarta su preparación temporal ante rechazo.
Los resultados deben ser archivos regulares ya tracked; un resultado nuevo
se rechaza explícitamente para revisión. El helper no separa hunks previos
ajenos dentro de un mismo archivo seleccionado. Git/config/hooks son código
local de confianza, no un sandbox: un hook que escribe/mueve HEAD o amplía su
índice puede causar efectos; postvalidar detecta desviación sin deshacerla.
PROJECT.md no se selecciona cuando solo se produce YAML. Sin reintento ni
restauración ciega de índice/HEAD ajenos.
