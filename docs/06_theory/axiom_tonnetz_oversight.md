---
title: Monitor Tonnetz: sonificación propuesta y evidencia pendiente
status: Revisado-sin-certificacion-cientifica
version: 2.0.0
---

# Monitor Tonnetz: sonificación propuesta y evidencia pendiente

Revisión: 2026-10-24. La declaración histórica de «VERIFICADO» queda retirada. Véase el [informe de auditoría](AUDIT_AXIOMS_2026.md) para evidencia, criterios y límites.

## 1. Alcance

Propuesta de sonificar telemetría con acordes y desplazamientos de afinación. «Homeostasis» y «anergía» son nombres de estados de software, no mediciones físicas o clínicas. Para usar entropía hay que identificar una distribución; para usar energía, medir julios con un protocolo. No se demuestra que ambas magnitudes describan la seguridad del sistema.

## 2. Rectificación de AX-TZ-1 y AX-TZ-2

- **AX-TZ-1:** asociar una entrada baja a una tríada mayor es una elección de interfaz. La ecuación en el origen no demuestra un límite; se requerirían una topología, una función definida y continuidad. «Mayor» no demuestra afinación pura, ausencia de riesgo ni estado óptimo.
- **AX-TZ-2:** aumentar una entrada puede aumentar una métrica escalar de alerta si así se programa. La expresión ∂Φ/∂ΔEx > 0 no está definida para un codominio Tonnetz sin coordenadas, cálculo y orden. Las operaciones L, P y R no implican por sí mismas disonancia microtonal ni una respuesta humana uniforme.
- **Percepción y carga:** reducción de fatiga, detección «irreprimible» y mejora del tiempo de intervención son hipótesis de usabilidad, sin ensayo aportado. Se necesitan medidas de detección, falsas alarmas, accesibilidad y efecto sobre tareas bajo cargas representativas.

## 3. Evidencia de código y límites

Existe [tonnetz_monitor.py](../../01_KISH_ENGINE/babylon60/primitives/tonnetz_monitor.py). La inspección estática muestra un mapeo por umbrales: ambas entradas < 0,1 producen `HOMEOSTATIC_PURE` con C–E–G; otras entradas cambian etiquetas, acordes y números. La función devuelve telemetría: ese recorrido no reproduce audio ni detiene un sistema.

Los [dos tests existentes](../../tests/babylon60/primitives/test_tonnetz_monitor.py) comprueban ejemplos del mapeo. Su contenido no es un estudio de percepción ni una evaluación jurídica. No se ejecutaron en esta revisión documental ni se atribuye a ellos un resultado nuevo. El ejemplo (0,05; 0,05) cae en estado estable aunque ambas entradas sean positivas: contradice la lectura literal del campo Lean que imponía disonancia ante cualquier incremento positivo, si las entradas se interpretan como coordenadas absolutas de Φ.

Existe también [verify_tonnetz_falsification.py](../../scripts/c5_verifiers/verify_tonnetz_falsification.py): por inspección calcula una KL de vectores de ejemplo y la multiplica por una constante de Landauer. No mide calor, potencia ni percepción; sus asserts numéricos no validan una disipación física del runtime. No se ejecuta ni se certifica ese script aquí.

## 4. Supervisión humana y estatus jurídico

Se retira la afirmación de «estricto cumplimiento» o cumplimiento «de facto» del artículo 14. La [fuente oficial de la Comisión Europea, artículo 14](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-14), exige supervisión humana efectiva y medidas proporcionales: comprender límites, vigilar anomalías, interpretar resultados y poder intervenir o detener el funcionamiento, entre otras condiciones aplicables.

Un canal sonoro podría ser una medida de apoyo. Un acorde, una etiqueta `eu_ai_act_status` o un bloque Lean no acreditan esas capacidades ni la conformidad del sistema. **Cumplimiento: NO_EVALUADO**, pendiente de propósito, clasificación, contexto de uso, medidas completas y evidencias de eficacia. Esta corrección no emite un dictamen de incumplimiento.

## 5. Estado formal

La estructura histórica `TonnetzOversight` pedía `triadic_homeostasis_limit`, `thermodynamic_degradation_dissonance` y `dissonance_exclusion` como campos. Definir esas obligaciones no construye una instancia ni prueba percepción o cumplimiento. El primer campo describía un valor puntual, no un límite asintótico.

La extracción original falla con Lean 4.35.0 por ausencia de tipos/clases numéricas resueltos para `Real`. Se retira el bloque como prueba. **Correspondencia Lean–implementación y eficacia perceptiva: NO_VERIFICADAS.** Una futura formalización deberá especificar entradas, umbrales y función de salida reales; su alcance seguirá limitado al modelo.
