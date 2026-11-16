---
name: cortex-skill-auditor
display_name: Auditor Exergético de Skills CORTEX Engine
description: Diagnóstico y auditoría exergética de las habilidades y skills del ecosistema CORTEX. Dispara con "auditar skills", "auditoría de habilidades", "exergía skills", "solapamiento de triggers", "cortex skill auditor", "matriz de colisión", "salud de skills".
role: auditor
allowed_roles:
- auditor
- arquitecto
directives:
  worktree_mode: audit-only
  phase: verification
  handoff:
    upstream: ejecutor
    downstream: operador
---

# Auditoría de skills

Audita la biblioteca solicitada sin ejecutar sus procedimientos ni modificar sus instalaciones. Conservar el rol auditor y las restricciones del módulo. Una verificación estructural no certifica que las instrucciones sean correctas ni que un servicio externo esté activo.

## Comprobaciones independientes

- Estructura: YAML, identidad, descripción y referencia o procedimiento. Los contratos de roles se validan solo en skills que los declaran.
- Rutas: módulos presentes y confinados, políticas de intención disponibles y recursos relativos a la distribución.
- Enlaces: destinos locales y anclas. Los remotos se identifican como no verificados si no se consulta la red.
- Contratos semánticos: patrones léxicos conocidos, con hallazgos que requieren revisión contextual.
- Distribución: hashes de contenido, modos y referencias simbólicas frente a la salida revisada. No sustituye las comprobaciones anteriores.

Los resultados se reúnen en un informe versionado, conservando el nombre, método, cobertura y estado de cada comprobador. No promediar fallos para convertirlos en éxito. No atribuir FPR, energía, calidad ni seguridad general a estas comprobaciones.

## Comprobador declarativo portable

Desde esta carpeta:

```bash
python3 ../../../../cortex-skill-auditor/scripts/audit_declarative_skills.py --root /ruta/biblioteca --output /ruta/fuera-de-skills/declarative.json
```

El wrapper descubre el comprobador incluido en la distribución. No presupone rutas de usuario, Gemini ni Codex. Para incluir plugins, indicar sus raíces explícitamente con `--plugin-root`.

## Mantenimiento y efectos

La fuente canónica del repositorio es `tools/skill_library/catalog.json`; los índices y launchers son generados. El mantenimiento se prepara con `scripts/c5_skills_ontology/maintain_skill_library.py` desde el repositorio. Este módulo auditor solo revisa resultados; distribuir cambios corresponde al trabajo de implementación autorizado por el usuario. Seleccionar una habilidad o auditarla no inicia agentes, purgas, despliegues ni comunicaciones.
