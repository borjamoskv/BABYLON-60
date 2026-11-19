# Contrato breve y evaluación del trabajo con agentes

La autoridad y los controles de seguridad están en el [manifiesto](../../.babylon60rules).
Esta guía permite concretar una tarea y comprobar si una simplificación de reglas
reduce esfuerzo operativo. No certifica el kernel ni supone una mejora de productividad.

## Contrato de tarea

Antes de editar, escribir en el plan o registro de trabajo:

```text
Resultado esperado:
Rutas permitidas:
Restricciones aplicables:
Prueba de aceptación:
```

Para trabajo comprobable, fijar criterios antes de editar. Cada criterio conserva
`id`, `description`, `status` (`passed`, `failed` o `pending`) y `evidence`.
No borrar fallos ni redefinir el éxito al cierre. Los criterios aprobados requieren
referencias a resultados reales. Basta un registro breve; las preguntas simples
no requieren un inventario vacío. El evaluador existente admite `--criteria` en
`scripts/c5_quality_gates/prompt_exergy_oracle.py`; comprueba la estructura y
cuenta resultados declarados, sin certificar su contenido ni fecha de fijación.

Leer solo los [contratos técnicos](agent_contracts.md) afectados. Ejecutar la
comprobación de aceptación y revisar el diff antes de declarar el resultado.
El informe final explica cambios, comprobaciones y límites; el panel se añade
solo cuando aporta trazabilidad o se solicita.

## Decisiones de gobernanza

Esta revisión conserva identificadores y controles del protocolo. La tabla registra
obligaciones conservadas, acotadas o reclasificadas; no certifica su implementación.
El manifiesto y AGENTS juntos tienen un límite de 10.183 bytes; el presupuesto
agregado inspeccionado mantiene 40.000 bytes. Las estimaciones de tokens no miden
el contexto real que carga un cliente.

| Obligación | Decisión y destino | Motivo y comprobación |
| --- | --- | --- |
| Autorización, biometría y rechazo | Conservada en manifiesto y contrato de atestación; requisitos del gate trasladados desde el perfil personal. | Proteger efectos; verificar hash, caducidad, operador, firma, rechazo y resultado por separado. |
| Aislamiento, memoria, persistencia y consenso | Conservada en contratos por componente. | Aplicar pruebas de layout, ciclo de vida, determinismo y recuperación del ámbito afectado. |
| Exploración y preguntas | Acotada en AGENTS y `INV_C5_AUTONOMOUS_FORENSIC_RECOVERY`. | Buscar primero en fuentes pertinentes; ampliar por indicios, sin exigir todos los históricos. |
| Autorizaciones vigentes y bloqueos | Explicitada en AGENTS y perfiles distribuidos. | Evitar permisos repetidos; continuar trabajo independiente sin eludir el bloqueo. |
| `cargo clean`, tipos y checks | Acotada en contratos de build y calidad. | Limpiar por diagnóstico; aplicar checks configurados y dirigidos; conservar CI completo. |
| CI (`INV_C5_CI_FALSIFICATION`) | Acotada a evaluar CI o una revisión. | Contrastar commit y ejecución, no badges ni ejecuciones de otra revisión. |
| Fuentes académicas (`INV_C5_DEEP_ACOPLE`) | Preferencia por estructura; PDF permitido. | Conservar fórmulas/figuras y procedencia; un artículo no obliga a implementar un PoC. |
| Local-first (`INV_C5_SOVEREIGN_ANTIGRAVITY`) | Preferencia; Rust conserva su ámbito arquitectónico. | Verificar requisitos, recuperación y medidas; ningún lenguaje acredita continuidad. |
| Seis perspectivas, perfil personal y creación literaria | Contexto opcional en sus reglas y contratos. | Aplicar solo por petición; no imponer conclusiones ni atribuir estados personales. |
| C6, Q-S-A-Ω y propiedades físicas | Referencias de diseño en contratos. | Exigir definición, método y evidencia antes de declarar resultados físicos. |
| Entropía, DEC, Aeon y datasets | Condiciones por pipeline en contratos. | Identificar representación, muestra, umbral y versión; no inferir propiedades del nombre. |
| Oferta enterprise y releases | Parámetros comerciales revisables; controles conservados. | Contrastar capacidad, fuentes y revisión; preparar una oferta no autoriza publicarla. |
| Modelo, índice léxico y firma | Condicionales en presentación y guía portable. | Datos vigentes; ejemplo heredado en su guía; documentos válidos sin firma. |
| Presupuesto, semántica y enlaces | Cobertura de los ocho documentos centrales y reglas activas. | Fallar ante fuentes obligatorias ausentes, patrones conocidos y enlaces/anclas rotos. |
| Topología y distribución | Siete symlinks obligatorios y guard compartido. | Verificar árbol e índice por separado y contenido del paquete; no certificar runtime. |

## Cinco escenarios de aceptación

Estos casos revisan cobertura normativa y controles locales. No ejecutan efectos
protegidos ni demuestran una mejora del comportamiento del LLM. Para observar esa
mejora, aplicar la comparación de tareas de la sección siguiente.

| Caso | Acción esperada | Bloqueo aplicable | Evidencia necesaria |
| --- | --- | --- | --- |
| GOB-01 · Edición documental autorizada | Editar y ejecutar enlaces, semántica, presupuesto y topología; sin compilación Rust ni biometría por sí sola. | Fuente requerida ilegible o comprobación documental fallida. | Diff y resultados de los controles documentales. |
| GOB-02 · Corrección ordinaria | Resolver decisiones reversibles con la autorización vigente; ejecutar test dirigido y linter. | Fallo de aceptación o ampliación del efecto fuera de alcance. | Caso reproducido, diff y resultado de la prueba pertinente. |
| GOB-03 · Contexto insuficiente | Explorar grafo y rutas; preguntar solo por el dato decisivo restante y continuar trabajo independiente. | La operación dependiente de ese dato; no toda la tarea. | Fuentes consultadas, límites de cobertura y dato pendiente. |
| GOB-04 · Efecto protegido sin atestación válida | Preparar el artefacto revisable y detener el efecto; sin bypass, reintentos ni autenticación alternativa. | Autorización o atestación inválida, expirada o de otro hash. | Rechazo y evidencia independiente de ausencia de efecto para una prueba de runtime; un test documental no lo acredita. |
| GOB-05 · Respuesta sencilla | Responder con resultado y evidencia pertinente; firma y panel opcionales. | Ninguno por ausencia de firma o metrología opcional. | Documento válido sin firma; compatibilidad de firma validada aparte cuando se incluya. |

El auditor semántico inspecciona rutas y anclas locales sin consultas externas.
Los patrones léxicos no prueban consistencia completa. La topología en `--staged`
lee el índice Git, aunque el árbol de trabajo difiera; `--response` se reserva
para borradores con firma. CI y pre-commit usan `--workspace-only`; la telemetría
se omite expresamente con `--skip-ghost-listeners` en el presupuesto.
El registro MCP de VS Code es local y opcional: se comprueba si está presente,
sin exigirlo en un checkout limpio. Los demás manifiestos declarados son obligatorios.

Revisión normativa del 24 de octubre de 2026: los cinco casos tienen cobertura
documental comprobada. `passed` en esta tabla significa coherencia de la regla y
su aceptación; no ejecución del efecto ni comportamiento observado de un LLM.

| id | status | evidence |
| --- | --- | --- |
| GOB-01 | passed | [Cierre proporcional](../../AGENTS.md#condición-de-cierre); controles locales de documentos, presupuesto y topología. |
| GOB-02 | passed | [Ejecución autorizada](../../AGENTS.md#ejecución) y [aceptación por componente](agent_contracts.md#aplicación-y-aceptación). |
| GOB-03 | passed | [Exploración y bloqueos](../../AGENTS.md#ejecución); alcance acotado de `INV_C5_AUTONOMOUS_FORENSIC_RECOVERY`. |
| GOB-04 | passed | [Atestación y rechazo](agent_contracts.md#atestacion-biometrica); certificación de runtime pendiente de pruebas en su ámbito. |
| GOB-05 | passed | [Firma condicional](../../.babylon60rules#modelo-y-presentación); pruebas de documentos sin firma y compatibilidad legacy/v2. |

## Comparación de cinco tareas

Se ejecutó una comparación el 24 de octubre de 2026: cinco tareas, dos versiones
y dos repeticiones, con `gpt-6.1-sol` y esfuerzo `xhigh` configurados y devueltos
por el servidor. Referencias: `a474d9b2` antes y `c6dd7337` después. El
[informe con contrato, rúbricas, evidencia y límites](../security/governance-comparison-2026-10-24.md)
documenta las 20 ejecuciones reales. No es una certificación de los cinco
escenarios normativos anteriores ni una evaluación humana independiente.

| Tarea | Tiempo medio antes → después | Aceptación antes → después | Retrabajo por defectos antes → después |
| --- | --- | --- | --- |
| Síntesis | 12,29 → 11,15 s | 2/2 → 2/2 | 0 → 0 |
| Decisión | 17,11 → 18,16 s | 2/2 → 2/2 | 0 → 0 |
| Documentación | 12,41 → 13,56 s | 2/2 → 2/2 | 0 → 0 |
| Corrección ordinaria | 35,64 → 26,82 s | 2/2 → 2/2 | 0 → 0 |
| Continuidad | 28,70 → 24,33 s | 2/2 → 2/2 | 0 → 0 |

La media temporal bajó un 11,4 %, pero la nueva versión ganó solo 6/10 pares y
su mediana global empeoró. Ambas cumplieron todos los criterios; no se demostró
mejora de calidad ni retrabajo. Se registraron tokens, no coste monetario, y cero
intervenciones humanas durante las tareas. Los tiempos excluyen preparación y
revisión del evaluador; las respuestas se verificaron posteriormente. La muestra
es pequeña, sencilla y sensible a caché/latencia del proveedor.

En nuevas campañas, elegir antes de empezar una referencia y criterios comparables,
conservando contrato y resultado por tarea. Sin referencia, las observaciones
forman una línea base y no permiten atribuir una mejora a las reglas.

- **Tiempo:** desde el contrato cerrado hasta el primer artefacto que cumple la
  prueba de aceptación. Anotar pausas externas para no atribuirlas al agente.
- **Intervenciones:** contar aclaraciones o correcciones humanas necesarias
  después de cerrar el contrato; registrar su causa.
- **Retrabajo:** contar correcciones posteriores al primer resultado y anotar
  si se debieron a defectos, alcance cambiado o evidencia insuficiente.
- **Coste y selector:** usar consumo o precio solo si la fuente lo expone.
  No reconstruir el esfuerzo activo desde un valor predeterminado ni inventar
  euros o tokens; declarar el dato desconocido en la celda si corresponde.

Comparar tareas de dificultad y aceptación semejantes. Una muestra de cinco
sirve para detectar fricción, no demuestra causalidad ni un modelo universalmente
óptimo. Mantener los controles de seguridad; si el coste no mejora o crece el
retrabajo, revisar la hipótesis y el contrato antes de añadir otra regla.

## Indice lexico

El nombre de la medición es **índice léxico**. La etiqueta de transporte
`EXERGÍA INFORMATIVA` se conserva por compatibilidad. Calcularlo solo si aporta
información a la tarea; no es un criterio de aceptación ni una medida de claridad,
verdad, energía física o calidad del trabajo.

El método `c5-lexical-v2`, implementado en
[prompt_exergy_oracle.py](../../scripts/c5_quality_gates/prompt_exergy_oracle.py),
calcula `floor(21000 × U / max(N, 20))`: `N` cuenta tokens y `U` tokens distintos.
Aplicar `casefold`, NFKD, retirar marcas de acento y obtener tokens Unicode con
`[^\W_]+`; ignorar destinos de enlaces y URL. Texto sin tokens obtiene cero.
Menos de 20 tokens es muestra breve: umbral normativo, sin calibración científica.
Las antiguas franjas de puntuación no se usan como juicios de calidad o aceptación.

Si se mide, puntuar el cuerpo antes de añadir la firma:

```sh
python3 scripts/c5_quality_gates/prompt_exergy_oracle.py --stdin --json
```

Conservar método, texto medido, fuente y fecha del turno. Si falla, informar
`ERROR_DE_CÁLCULO` con la causa; no reutilizar una cifra anterior. Si no se mide,
omitirlo del Panel. El texto heredado admite «No medida» por compatibilidad.
