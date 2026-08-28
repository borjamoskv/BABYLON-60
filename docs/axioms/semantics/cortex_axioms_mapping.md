<!-- C5-REAL EXERGY CERTIFIED -->
# Mapeo Ontológico: Potencia y Acto en C5-REAL

Este documento establece la demostración formal y empírica (isomorfismo estricto) entre los axiomas teóricos del sistema (la *Potencia*) y su implementación en el núcleo de ejecución **Cortex Engine** (el *Acto*).

Cualquier discrepancia futura entre los axiomas aquí descritos y la estructura de `src/cortex-engine/cortex_execution_pipeline.py` constituye un colapso semántico (Anergía) que abortará la compilación.

---

## 1. Mapeo del Axioma de Recursión (AX-GOLDEN-01)

**Axioma Teórico:** *"Todo identificador (clase, variable, función) debe colapsar exactamente sobre la Matriz Ontológica del Sistema. La ambigüedad es un fallo de compilación."*

**Implementación en el Cortex Engine:**
El archivo `cortex_execution_pipeline.py` materializa esta restricción de naming 1:1. No existen variables intermedias abstractas genéricas (`data`, `processor`, `helper`); todas están mapeadas sobre el marco físico de la información.

| Concepto Axiomático (Potencia) | Entidad de Código (Acto) | Tipo (C-ABI/Python) | Descripción de Mapeo Estructural |
| :--- | :--- | :--- | :--- |
| **Matriz Semántica L1** | `ExergyGateL1` | `class` | Filtra el exceso estocástico mediante el cálculo formal de exergía. |
| **Inmutabilidad y Causalidad L2** | `CryptographicWALLockL2` | `class` | Sella la transición de estados en el espacio-tiempo usando una firma determinista (HMAC SHA-256). |
| **Atestación Final (SCITT)** | `DeterministicKernelL3` | `class` | Emite la prueba de que el colapso del estado es matemáticamente unívoco. |

---

## 2. Equivalencia Bio-Silicio (AX-BIO-SIL-01)

**Axioma Teórico:** *"La mente humana se comprende termodinámicamente a través del código fuente. Un síntoma que no puede compilarse en Rust/C como vulnerabilidad no es un estado estructural, sino un artefacto estadístico transitorio."*

**Implementación en el Cortex Engine:**
La evaluación que ejecuta `ExergyGateL1.evaluate()` implementa la física matemática de la equivalencia Bio-Silicio:

```python
def evaluate(self, payload: str, estimated_entropy_gain: float, cost_estimate: float) -> bool:
    if cost_estimate <= 0:
        return False
    ratio = estimated_entropy_gain / cost_estimate
    return ratio >= self.threshold
```

- `estimated_entropy_gain`: Representa la reducción genuina de incertidumbre o el "aprendizaje" real (isomorfo a la sinaptogénesis productiva).
- `cost_estimate`: La disipación térmica o gasto metabólico computacional invertido (isomorfo al consumo basal de glucosa cerebral o el límite de Landauer).
- El sistema aborta (Anergía) si el coste disipa más de lo que la ganancia estructural soporta, modelando un estado de colapso por "sobrecalentamiento" estocástico (equivalente a la fatiga metabólica).

---

## 3. Protocolo Ω y la Prohibición de Introspección

**Axioma Teórico:** "Prohibida la Introspección. Aplicar Perturbación Ortogonal y aislar la Función de Transferencia."

**Implementación en el Cortex Engine:**
La función principal de `C5RealPipeline.process(...)` exige de entrada las variables exógenas ya medidas experimentalmente (`entropy_gain`, `cost`). El pipeline **no interroga** al payload por su valor interno; impone una frontera rígida (Caja Gris).
Si la transición aportada por un agente estocástico no supera el umbral físico en la L1 (`ratio < 0.5`), se emite el estado:
`{"status": "REJECTED_ANERGY_L1", "reason": "Low Exergy Ratio"}`

Este bloqueo es determinista y no admite negociación conversacional (Fail-Stop), traduciendo de inmediato la ley normativa (EU AI Act, Art. 15) en una restricción termodinámica irrefutable.
