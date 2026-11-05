# Lote 9 propuesto: Git del monitor de estado — 29/10/2026

> Alcance de la distribución pública: las referencias marcadas como material no distribuido identifican evidencia o herramientas excluidas deliberadamente de este checkout. Se conservan sus rutas y los resultados históricos; esos soportes no pueden verificarse desde esta distribución.

Estado: ejecutado por instrucción del operador; véase el
[informe de cierre](REMEDIATION_SWARM100_LOTE9_2026-10-29.md).
La planificación inicial seleccionó un P1 CONFIRMED_STATIC/OPEN:
C0438, en la única fuente productiva prevista
`scripts/c5_thermo/c5_exergy_optimizer_monitor.py`. La
selección con hash (material no distribuido: `evidence/swarm100-lot8-20261029/lot9-selection.json`)
conserva evidencia estática y versión anterior a cualquier futuro parche.
No quedan P1 OPEN previamente reproducidos; este lote continúa la familia de
commits que incluyen trabajo ajeno y omiten controles.

| ID | Fallo que reproducir primero | Resultado exigido |
| --- | --- | --- |
| C0438 | _git ignora códigos de retorno y desactiva firma; add usa una ruta obsoleta, el commit consume el índice entero y el caller hace amend sin verificar. | Fallos propagados, hooks/configuración de firma respetados y commit limitado al resultado que produce el monitor, preservando staging/HEAD ajenos. |

Explorar _git, git_sentinel_commit y c5_real_colapso mediante grafo y fuente.
Reproducir en repositorios temporales: índice ajeno preparado, ruta obsoleta,
hook que rechaza commit/amend, fallo de Git y diagnóstico que nunca puede
convertirse en hash o mensaje COMPLETE. HOME/configuración Git propios,
identidad sintética y firma real desactivada solo en la configuración local
de las fixtures; el código productivo no debe imponer ese override.

No ejecutar el monitor completo sobre el proyecto real: lee bases del operador,
lanza auditorías/tests y escribe STATUS.md. Extraer o sustituir los productores
del censo, linter y tests en fixtures controladas, manteniendo Git real solo en
repositorios temporales. No red, claves reales, biometría, bases reales o push.

Diseño propuesto: _git debe comprobar retorno y usar bytes en diff; retirar
--no-verify y el override commit.gpgsign=false. El monitor genera STATUS.md:
no preparar su propio archivo fuente, ni su ruta obsoleta. Rechazar preparación
previa/estados no soportados y limitar la mutación Git a ese resultado concreto.
Preservar archivo/índice ajenos al rechazar, sin reset --hard/clean/stash.
Aprovechar las comprobaciones del Lote 8 sin duplicar ni importar un script
con efectos; en esta fase no se autoriza ampliar fuentes productivas.

Eliminar el amend automático y el intento de incrustar dentro del documento
el hash del mismo commit que lo contiene. El hash real puede informarse tras
un commit verificado; un fallo no imprime COMPLETE ni reutiliza un HEAD viejo
como prueba de una operación nueva. No alterar por inferencia las métricas del
censo ni cerrar otros defectos del monitor.

Cubrir éxito/no-op y rechazos, índice/HEAD intactos, hooks normales, firma
configurada respetada mediante registradores inocuos, staging intercalado y
consumidor sin éxito tras fallo. Declarar granularidad por archivo y confianza
en Git/config/hooks; una comprobación posterior no contiene efectos de hooks.
Aceptación: red/green, suite relacionada, Ruff/MyPy, revisión independiente,
registro reconciliado y controles documentales. Preparar el Lote 10 sin
aplicarlo. La ejecución posterior y sus límites constan en el informe enlazado;
el Lote 10 queda solo preparado.
