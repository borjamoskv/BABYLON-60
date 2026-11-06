---
title: Auditoría de estatus científico de los axiomas C5-REAL
status: Certificaciones-historicas-retiradas
version: 2.0.0
---

# Auditoría de estatus científico de los axiomas C5-REAL

Revisión: 2026-10-24. Este informe sustituye el dictamen histórico fechado 2026-08-18. Se retiran su sello «Verified», sus cinco certificaciones restantes y la afirmación global de consistencia/completitud. No se certifica el resto de `docs/06_theory` ni el runtime.

## 1. Contrato, método y vocabulario

Alcance cerrado: las seis entradas de la tabla histórica, más el propio informe. Se preserva el compendio corregido en la revisión anterior y se corrigen los otros cuatro archivos existentes, el informe y las descripciones de tres índices. `axiom_legion_swarm.md` no existe en la ruta citada: no se crea un sustituto ni se transfiere su certificación a otro archivo.

Se inspeccionaron textos, bloques Lean, referencias de implementación y fuentes primarias pertinentes. Antes de editar se extrajeron los bloques originales y se ejecutó `lean <archivo-extraído>` con Lean 4.35.0, sin instalar dependencias. Los fallos de imports son límites de reproducibilidad, no refutaciones de los resultados matemáticos citados. La inspección de código no acredita ejecución; una estructura con campos de tipo Prop impone obligaciones a sus instancias, no demuestra que exista una instancia ni que modele la realidad.

- **Definición / convención:** significado elegido; no hallazgo empírico.
- **Resultado matemático condicional:** conclusión con hipótesis y derivación delimitadas; no necesariamente formalizada en Lean.
- **Hipótesis:** afirmación pendiente de contraste; sin variables observables puede no ser aún falsable.
- **Metáfora:** analogía sin equivalencia física, biológica o jurídica demostrada.
- **NO_VERIFICADO:** evidencia insuficiente; no significa falso.
- **REFUTADO en el alcance indicado:** contraejemplo o error de derivación identificado; no se extrapola a otras tesis.

## 2. Rectificación de las seis entradas

| Documento históricamente certificado | Evidencia observada y garantía retirada | Estatus vigente |
| --- | --- | --- |
| [AXIOMATIZATION_C5_REAL.md](AXIOMATIZATION_C5_REAL.md) | Dos declaraciones `axiom`; elementos usados como tipos; `Score < 700 → F > 0` no modela Abort. No hay prueba de no-alucinación ni rechazo de compilación en O(1). | Postulados de diseño; formalización e implementación NO_VERIFICADAS. |
| [axiom_bayesian_disintegration.md](axiom_bayesian_disintegration.md) | Campos Prop en una estructura, imports no reproducibles y referencias no localizadas. El soporte del prior no garantiza verdad ni impide modificar coherentemente el prior. | Resultados finitos condicionales conservados; garantías universales de no-alucinación y prompt injection retiradas. |
| `axiom_legion_swarm.md` | Archivo ausente en la ruta certificada; búsqueda de nombres no localiza ese documento. Scripts con nombres legion no acreditan su contenido. | NO_LOCALIZADO; certificación de scheduler/concurrencia sin objeto verificable. |
| [axiom_oncology_protocol.md](axiom_oncology_protocol.md) | La estructura exige causalidad, monotonicidad y reducción como campos; no construye un modelo biológico. El boceto no define dinámica ni demuestra estabilidad o remisión. | Hipótesis y analogías; control tumoral y eficacia NO_VERIFICADOS. |
| [axiom_tonnetz_oversight.md](axiom_tonnetz_oversight.md) | La estructura pide las propiedades acústicas; el código inspeccionado devuelve telemetría por umbrales, no evidencia perceptiva o jurídica. | Mapeo de software observado estáticamente; eficacia NO_VERIFICADA y cumplimiento NO_EVALUADO. |
| [c5_thermodynamic_invariants_compendium.md](c5_thermodynamic_invariants_compendium.md) | Cuatro teoremas aritméticos con dependencias auditadas; no axiomas científicos añadidos. Fórmulas de información separadas de energía física. | Prueba Lean de alcance limitado; no certificación física, de calidad ni del kernel. |

## 3. Hallazgos y criterios de refutación

### H1. Axiomas y campos presentados como demostraciones

**Afirmación histórica:** las firmas habían sido sustituidas por modelos verificados y el corpus era consistente.
**Criterio:** revisar qué se demuestra y qué se exige como hipótesis; reproducir compilación.
**Observación:** `morphism_primacy` y `exergy_homeostasis_abort` eran axiomas. Las estructuras bayesiana, oncológica y Tonnetz almacenaban pruebas como campos, sin construir instancias. El informe añadía `ax_canonical_invariant : ∀ (x : X), True` y `formal_axiomatization ... : True`, que solo pretendía reutilizar ese supuesto.
**Veredicto:** la descripción de estos bloques como pruebas científicas queda REFUTADA. Esto no afirma inconsistencia lógica de toda la teoría. El propio bloque final del informe fallaba además por un comentario de documentación delante de `variable`. Se retira y no se reemplaza por otra tautología.

### H2. Bayes como garantía de ausencia de alucinaciones

**Criterio:** posterior falso que respete normalización y soporte.
**Contraejemplo:** un prior concentrado en una causa falsa y likelihood compatible con la observación mantiene esa causa con masa uno. El álgebra es coherente y la explicación puede ser falsa. Recalcular conjunta y posterior tras modificar el prior también conserva la identidad, sin autenticarlo.
**Fuente:** [Cho y Jacobs, desintegración e inversión bayesiana](https://arxiv.org/abs/1709.00322), casos discretos y tratamiento de eventos nulos.
**Veredicto:** REFUTADA la implicación general de soporte a verdad y a protección contra prompt injection. Se conservan los resultados finitos bajo sus hipótesis; existencia general, complejidad O(1), zero-copy y correspondencia con código siguen NO_VERIFICADAS.

### H3. Causalidad y control tumoral por analogía

**Criterio:** exigir variable medible, dinámica, control con unidades coherentes y prueba de que excluye el estado tumoral objetivo.
**Observación:** faltaban estos elementos. Una condición sin intervención no implica una dinámica bajo control; 300 clases no hacen finitos los estados. La equivalencia entre integral de purga y remisión no estaba derivada. `UNSAT` solo excluye soluciones de la codificación, no demuestra eficacia farmacológica.
**Fuente primaria:** [Koebel et al., Nature 2007, DOI 10.1038/nature06309](https://pubmed.ncbi.nlm.nih.gov/18026089/), equilibrio inmunitario en un modelo murino. No mide la F_T indefinida ni valida el modelo propuesto.
**Veredicto:** demostración de remisión inválida; postulados biológicos NO_VERIFICADOS y analogía terapéutica reclasificada como metáfora. No se hace una revisión clínica completa del catálogo.

### H4. Sonificación como supervisión efectiva y cumplimiento

**Criterio:** comprobar correspondencia del modelo con el código y aportar evaluación perceptiva y requisitos de supervisión aplicables.
**Observación:** el código tiene umbral estable con ambas entradas < 0,1, mientras el campo Lean exigía disonancia para cualquier valor positivo. En la lectura absoluta de sus entradas, (0,05; 0,05) contradice esa equivalencia. El script de KL/Landauer calcula valores de ejemplo; no mide disipación ni supervisión efectiva.
**Fuente oficial:** [Comisión Europea, artículo 14 del AI Act](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-14). La supervisión incluye capacidades efectivas de comprensión e intervención; un canal acústico aislado no acredita conformidad.
**Veredicto:** correspondencia formal general no demostrada; ventajas perceptivas NO_VERIFICADAS, cumplimiento NO_EVALUADO. Se retira la autocertificación, sin emitir dictamen de incumplimiento.

### H5. Concurrencia y efectos termodinámicos

**Criterio:** localizar el documento certificado y aportar mediciones o pruebas de scheduler con carga y hardware identificados.
**Observación:** el documento legion no está en la ruta citada. Los umbrales 2132 y 2,8 s y el límite por núcleos no se derivan de una ley física; sus problemas ya se explican en el compendio.
**Veredicto:** NO_VERIFICADO; no se asigna por analogía la evidencia de otro script o experimento.

## 4. Resultado reproducible de los bloques originales

Extracción por bloque Markdown `lean`, sin corregir imports, tipos ni comentarios. La columna describe el primer obstáculo observado; no supone que sea el único. Los bloques fallidos se retiraron de los documentos corregidos como certificados, en vez de reparar su sintaxis y mantener la misma conclusión injustificada.

| Origen | Bloque | Salida de Lean 4.35.0 | Alcance |
| --- | --- | --- | --- |
| Informe original | Ejemplo de axioma vacío | 0, con aviso por variable no usada | Aceptar un axioma tautológico no certifica nada del sistema. |
| Informe original | `AuditAxioms2026` | 1, comentario de documentación antes de `variable` | No reproducible tal como estaba escrito. |
| Base axiomática | `AxiomatizationC5Real` | 1, comentario/tipos/clases numéricas | No hay prueba de A1–A4. |
| Bayes | `BayesianDisintegration` | 1, `unknown module prefix Mathlib` | Dependencias locales insuficientes; no se afirma compilación con un entorno hipotético. |
| Oncología | `OncologyProtocol` | 1, resolución de tipos/clases | No acredita estabilidad, biología ni eficacia. |
| Tonnetz | `TonnetzOversight` | 1, clases de orden/numerales de Real | No acredita percepción ni conformidad. |
| Compendio corregido | Cuatro teoremas discretos | 0, sin mensajes | Cotas, conservación, antitonicidad y separación entre déficit y etiqueta de verdad; alcance explicitado allí. |

Las extracciones, copias previas, salidas completas y contrato de tarea se conservan localmente en `.audit/axioms-status-20261024/` (ignorado por Git). Este informe guarda los hallazgos duraderos; no depende de que ese directorio local se distribuya. Para repetir la compilación vigente del compendio basta extraer su único bloque Lean y ejecutar `lean <archivo.lean>`; sus `#guard_msgs` controlan las dependencias axiomáticas. Para repetir la inspección histórica se necesitan las versiones originales, no los documentos ya corregidos.

## 5. Cierre y trabajo pendiente

Para volver a declarar una propiedad formal: fuente y dependencias identificadas, modelo y supuestos explícitos, construcción o teorema relevante, auditoría de axiomas y compilación reproducible. Para extrapolarla a runtime, biología, percepción o cumplimiento se necesita evidencia adicional de ese dominio. Compilar no demuestra completitud, consistencia global ni verdad empírica.

La revisión cambia documentación y estatus, no runtime, dependencias ni distribución. Se comprueban enlaces/anclas y los gates semántico, presupuesto y topología del workspace. No se evalúa CI remoto ni se obtiene telemetría global; los tests Tonnetz se inspeccionan, no se ejecutan ni se presentan como resultados nuevos. La revisión de integración oncológica existente se referencia sin modificarla.

Resultado local de aceptación (2026-10-24): pasan `audit_semantic_contracts.py --workspace-only`, `audit_token_budget.py --workspace-only --skip-ghost-listeners`, `verify_active_topology.py`, los enlaces locales de los cinco documentos corregidos y `git diff --check` sobre las ocho rutas editadas. El compendio se conserva idéntico al inicio de esta extensión. Estos controles documentales no convierten las propiedades pendientes en verificadas.
