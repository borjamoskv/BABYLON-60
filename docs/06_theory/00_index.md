---
title: Índice de teoría y estatus científico
status: Indice-sin-certificacion-global
version: 2.0.0
---

# Índice de teoría y estatus científico

Revisión: 2026-10-26. Este índice describe los 31 documentos Markdown actuales, incluido él mismo. No certifica consistencia, completitud, implementación ni verdad empírica del corpus. Los resultados matemáticos expuestos se distinguen de las pruebas de un modelo, requisitos de diseño, hipótesis, metáforas e historia no revalidada.

[Auditoría completa de esta ampliación](AUDIT_SCIENTIFIC_STATUS_2026.md) · [Rectificación de las seis entradas anteriores](AUDIT_AXIOMS_2026.md)

Seguimiento externo a este corpus: [garantías de las especificaciones técnicas](../01_spec/AUDIT_SCIENTIFIC_GUARANTEES_2026.md). Su alcance no añade una certificación global de teoría o runtime.

## Inventario

| Documento | Tema | Estatus científico |
| --- | --- | --- |
| [00_index.md](00_index.md) | Índice de teoría y estatus científico | Índice; sin certificación global |
| [01_robinson_arithmetic.md](01_robinson_arithmetic.md) | Aritmética de Robinson | Exposición matemática; no formalizada |
| [02_goedel_incompleteness.md](02_goedel_incompleteness.md) | Gödel, Rosser y Löb | Exposición matemática; no formalizada |
| [03_computability_turing.md](03_computability_turing.md) | Computabilidad y Turing | Exposición matemática; no formalizada |
| [04_chaitin_kolmogorov.md](04_chaitin_kolmogorov.md) | Complejidad algorítmica | Exposición matemática; no formalizada |
| [05_model_theory.md](05_model_theory.md) | Teoría de modelos | Exposición matemática; no formalizada |
| [06_curry_howard.md](06_curry_howard.md) | Curry–Howard | Exposición matemática; no formalizada |
| [07_cross_domain.md](07_cross_domain.md) | Analogías entre lógica y cognición | Ensayo; analogías no demostradas |
| [08_babylon60_architecture.md](08_babylon60_architecture.md) | Arquitectura propuesta | Diseño; runtime no certificado |
| [09_formal_ontology_lean.md](09_formal_ontology_lean.md) | Modelos Lean y correspondencia | Fuentes formales acotadas |
| [10_physical_realization.md](10_physical_realization.md) | B60: ejemplos y límites | Ejemplos; garantías no verificadas |
| [AUDIT_AXIOMS_2026.md](AUDIT_AXIOMS_2026.md) | Rectificación de certificaciones | Revisión previa: seis entradas |
| [AUDIT_TAUTOLOGIA_VACIA_2026.md](AUDIT_TAUTOLOGIA_VACIA_2026.md) | Tautologías y evidencia | Auditoría documental limitada |
| [AUDIT_VERDICT_C5_REAL.md](AUDIT_VERDICT_C5_REAL.md) | Dictamen histórico C4-SIM | Historia no revalidada; filtro acotado |
| [AXIOMATIZATION_C5_REAL.md](AXIOMATIZATION_C5_REAL.md) | Postulados C5-REAL | Revisión previa: no certificados |
| [BABYLON60_PROOF_CARRYING_EXECUTION.md](BABYLON60_PROOF_CARRYING_EXECUTION.md) | Proof-carrying execution | Diseño; fuentes y métricas separadas |
| [CONTINUIDAD_SIN_OBEDIENCIA_TEORIA_ARQUITECTONICA.md](CONTINUIDAD_SIN_OBEDIENCIA_TEORIA_ARQUITECTONICA.md) | Continuidad sin obediencia | Requisitos normativos propuestos |
| [MOSKV_1_APEX_BLUEPRINT.md](MOSKV_1_APEX_BLUEPRINT.md) | MOSKV-1 APEX: blueprint | Propuesta de producto |
| [STATUS_THEORY.md](STATUS_THEORY.md) | Registro histórico de estado | Historia no revalidada; filtro acotado |
| [TETRADA_CAUSAL_BABYLON60.md](TETRADA_CAUSAL_BABYLON60.md) | Tétrada C5-REAL | Marco metafórico |
| [TOPOLOGIA_MAESTRA.md](TOPOLOGIA_MAESTRA.md) | Topología conceptual | Mapa; integraciones no certificadas |
| [VECTOR_A_MASTER_LEDGER_DESIGN.md](VECTOR_A_MASTER_LEDGER_DESIGN.md) | Diseño de ledger y ATMS | Diseño; resultados no revalidados |
| [axiom_bayesian_disintegration.md](axiom_bayesian_disintegration.md) | Bayes finito y soporte | Revisión previa: alcance matemático |
| [axiom_cyclic_conformal_aeon.md](axiom_cyclic_conformal_aeon.md) | Ciclos Aeon | Modelo discreto; sin prueba térmica |
| [axiom_moloch_landauer_balance.md](axiom_moloch_landauer_balance.md) | Moloch y balance de Landauer | Modelo contable Nat; sin garantía física o de incentivos |
| [axiom_oncology_protocol.md](axiom_oncology_protocol.md) | Modelo oncológico propuesto | Revisión previa: hipótesis |
| [axiom_sharur_swarm.md](axiom_sharur_swarm.md) | Sharur: concurrencia y reducción | Especificación condicional |
| [axiom_tonnetz_oversight.md](axiom_tonnetz_oversight.md) | Monitor Tonnetz | Revisión previa: propuesta |
| [c5_thermodynamic_invariants_compendium.md](c5_thermodynamic_invariants_compendium.md) | Compendio C5-REAL corregido | Revisión previa: Lean discreto acotado |
| [AUDIT_SCIENTIFIC_STATUS_2026.md](AUDIT_SCIENTIFIC_STATUS_2026.md) | Cobertura, hallazgos, fuentes y controles | Auditoría documental; no certificación de runtime |
| [AUDIT_LEAN_SCOPE_2026.md](AUDIT_LEAN_SCOPE_2026.md) | Auditoría de alcance Lean: revisión histórica de 23 fuentes y reconciliación posterior de 26 módulos | Hipótesis, fixtures y verificación bajo demanda; sin certificación del runtime |
| [LEAN_CENSUS_SCOPE_2026.md](LEAN_CENSUS_SCOPE_2026.md) | 144 declaraciones de teoremas y 275 construcciones, clasificadas 1:1 | Inventario documental del modelo; no garantiza propiedades físicas, PDE ni Rust |

## Lectura y autoridad

01–06 exponen conceptos matemáticos; 07 compara dominios como ensayo; 08–10 separan modelos y ejemplos de garantías de implementación. Los demás documentos especifican propuestas, registran historia o describen revisiones con sus límites. El índice no convierte ninguno de ellos en dependencia formal de otro.

Las reglas vigentes son el [manifiesto](../../.babylon60rules) y los [contratos de agente](../03_guides/agent_contracts.md). La licencia se consulta en [LICENSE](../../LICENSE); este índice no crea excepciones ni declara condiciones comerciales. Las referencias de diseño no autorizan efectos de runtime ni acreditan integraciones activas.
