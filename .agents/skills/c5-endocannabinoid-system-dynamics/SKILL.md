<!-- C5-REAL EXERGY CERTIFIED -->
---
name: c5-endocannabinoid-system-dynamics
description: Modelado categórico de sistemas cannabinoides (THC/CBD), neurobiología de la Doble Excepcionalidad (2e: TDAH + AACC), desacoplamiento DMN/ECN y farmacología geriátrica de reducción de daños.
---

# C5-REAL Endocannabinoid System Dynamics & Dual-Neurodivergence (2e)

## Descripción General
Este skill proporciona la metodología formal, categórica y neurobiológica para analizar la dinámica de la matriz cannabinoide (THC + CBD) en sistemas complejos, con especial énfasis en:
1. **Modelado Categórico de Ligandos**: THC (Agonista parcial ortostérico / Vector de entropía) y CBD (Modulador Alostérico Negativo - NAM en CB₁ / Operador de estricción alostérica).
2. **Doble Excepcionalidad (2e: TDAH + Altas Capacidades)**: Fricción entre la Red por Defecto (DMN) y la Red de Control Ejecutivo (ECN), efecto en la memoria de trabajo y preservación del mecanismo de compensación intelectual.
3. **Farmacología Geriátrica y Reducción de Daños**: Sustitución de Benzodiacepinas/AINEs por CBD, interacciones en el citocromo P450 (CYP3A4/CYP2C9) y tablas de dosificación milimétrica en mg por gota.

---

## Triggers
Dispara automáticamente cuando la consulta mencione:
- `"morfismos cannabinoides"`, `"THC CBD sistemas"`, `"farmacodinámica 2e"`, `"CBD personas mayores"`, `"CBD geriatría"`, `"TDAH AACC cannabinoides"`, `"efecto séquito"`, `"modulación alostérica CB1"`.

---

## 1. Categoría de Estados Neuroquímicos: Cann

Definición de los morfismos primarios en el espacio fásico de receptores:
* **Ob(Cann)**: Variedades conformacionales de los receptores ℳ_CB1, ℳ_CB2, ℳ_5-HT1A, ℳ_TRPV1.
* **f_THC**: ℳ_CB1(off) ──► ℳ_CB1(on) [Agonismo parcial ortostérico; desinhibición GABAérgica fásica en VTA].
* **g_CBD**: End(ℳ_CB1) [Modulación Alostérica Negativa; desvío conformacional del pozo de potencial ortostérico].
* **Composición**: h_HACHIS = g_CBD(f_THC) ⊕ ϕ_FAAH ⊕ ϕ_5-HT1A.

```
                        f_THC (Agonismo Ortostérico)
          ℳ_CB1(inactivo) ─────────────────────────► ℳ_CB1(activo)
                 │                                           │
   g_CBD (NAM)   │                                           │ Transducción G_i/o
                 ▼                                           ▼
          ℳ_CB1(modificado) ───────────────────────► ℳ_S (Respuesta Amortiguada)
                        h = g_CBD ∘ f_THC
```

---

## 2. Neurobiología de la Doble Excepcionalidad (2e: TDAH + AACC)

* **AACC (Altas Capacidades)**: Hiper-conectividad asociativa, procesamiento paralelo masivo, sobreecitabilidad de Dabrowski. Genera alta entropía de hipótesis.
* **TDAH**: Hipo-dopaminergia tónica prefrontal (dlPFC), fallo de desactivación del Default Mode Network (DMN), memoria de trabajo frágil.
* **Mecanismo de Compensación Intelectual**: El cerebro 2e suple la desatención tónica usando la lógica asociativa de las AACC.
* **Efecto del THC Aislado**: Suprime la dlPFC, colapsando el filtro compensatorio y aumentando la desorganización ejecutiva.
* **Efecto del CBD (NAM + 5-HT₁₇)**: Silencia el parloteo amigdalino y el DMN, reduciendo la sobrecargada sensorial sin degradar la memoria funcional.

---

## 3. Protocolo Geriátrico de Reducción de Daños (CBD vs. Benzodiacepinas)

### A. Ventaja Clínica
- **Benzodiacepinas**: Riesgo elevado de caídas (ataxia), adicción, tolerancia rápida y aumento de deterioro cognitivo.
- **CBD**: Cero ataxia, cero adicción, preservación de la lucidez y neuroprotección antioxidante/inmunomoduladora.

### B. Matriz de Concentraciones (10 ml = ~250 gotas)
- **5% CBD**: 500 mg total | 2.0 mg / gota (Inicio frágil).
- **10% CBD**: 1000 mg total | 4.0 mg / gota (Estándar dolor leve / insomnio).
- **25% CBD**: 2500 mg total | 10.0 mg / gota (Máxima eficiencia financiera para dolor crónico / artrosis / Parkinson).

### C. Precaución CYP450
- Monitorear dosis al combinar con **Sintrom / Warfarina** (competencia por CYP2C9) y **antihipertensivos**.

---

## 4. Invariantes de Formato y Presentación
- **Tipografía Matemática UTF-8 Directa**: Prohibido el uso de LaTeX crudo (`$...$` / `$$...$$`). Usar siempre símbolos UTF-8 (ℳ, ℝ, ──►, ∘, ⊕, α, β, γ).
- **Representación Estructural**: Priorizar diagramas ASCII / Box-Drawing y Tagged Unions en Rust/C-ABI para definir estados no-válidos como irrepresentables.
