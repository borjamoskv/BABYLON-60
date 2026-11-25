---
title: Arquitectura propuesta: de requisitos a evidencia
status: Diseno-sin-certificacion-de-runtime
version: 2.0.0
---

# Arquitectura propuesta: de requisitos a evidencia

Revisión científica: 2026-10-24. Estatus: **Diseno-sin-certificacion-de-runtime**. El sello histórico de verificación y el axioma genérico de validez documental no acreditaban el contenido. [Alcance y evidencia de la revisión](AUDIT_SCIENTIFIC_STATUS_2026.md).

## 1. Naturaleza del mapeo

Los módulos matemáticos 01–07 pueden inspirar decisiones, pero no dictan por sí solos una implementación. Los nombres de invariantes históricos no prueban que un control exista o se aplique a toda ruta. Este documento formula requisitos y corrige sus justificaciones; no evalúa el estado actual del código concurrentemente modificado.

| Propuesta | Justificación y límite |
| --- | --- |
| Comprobar igualdad de payload en colisiones | Integridad e idempotencia requieren política explícita; no se deduce de Σ₁-completitud ni se certifica por prohibir una sentencia SQL. |
| Usar compromisos criptográficos canónicos | Un hash de 256 bits compromete datos bajo supuestos de seguridad, no preserva reversiblemente toda su información. La codificación hexadecimal duplica longitud textual, sin destruir por sí misma información. |
| Pre-filtrar grafos antes del cotejo exacto | 1-WL puede descartar pares no isomorfos; igualdad de colores no demuestra isomorfismo. Coste depende de rondas e implementación, no siempre O(V+E). |
| Limitar concurrencia y almacenamiento | Requiere carga, presupuestos y medición. «Disco se agota a diez agentes» no es un umbral universal ni prueba que todo trabajo deba ser en memoria. |
| Limitar profundidad de AST | Es una política de mantenibilidad; profundidad ≤ 4 no acota por sí sola número de caminos, bucles ni coste de verificación. |

Fuente primaria sobre límites de refinamiento: [Arvind et al., *Graph Isomorphism, Color Refinement, and Compactness*](https://arxiv.org/abs/1502.01255). Un ciclo de seis vértices y dos triángulos, con coloreado inicial uniforme, son un contraejemplo sencillo a usar 1-WL como prueba completa de isomorfismo.

## 2. Estado científico y de implementación

Se retiran las afirmaciones «soberanía absoluta», O(1) para todo rechazo, complejidad factorial inevitable del problema de isomorfismo y verificación universal lineal. Comparar dos resúmenes de tamaño fijo puede ser constante después de computarlos; no hace constante el procesamiento del grafo completo.

Una matriz de requisitos no es una demostración de BFT, de persistencia ni de aislamiento. Cada control requiere prueba dirigida y vínculo con la versión del código evaluada. Ni un diagrama ni el axioma genérico de validez documental constituyen esa evidencia; se retiran como certificados.

## 3. Autoridad y licencia

Los requisitos vigentes se consultan en el [manifiesto canónico](../../.babylon60rules) y los [contratos de agente](../03_guides/agent_contracts.md). Este texto no autoriza efectos de runtime. La licencia aplicable se consulta en [LICENSE](../../LICENSE); se retira la caracterización general de «100% open-source» como conclusión metamatemática o garantía jurídica.
