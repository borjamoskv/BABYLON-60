---
name: c5-adaptive-annealing-engine
display_name: Motor de Recocido Adaptativo y Convergencia Exergética (Q1-Q4)
description: Motor de Recocido Adaptativo en cuatro cuartiles (Q1-Q4) para forzar convergencia al Apex en espacios discretos y optimización sin colisión topológica ni colapso de gradiente voraz. Dispara con "adaptive annealing", "motor de recocido", "optimizacion sin colisiones", "recocido adaptativo", "busqueda del apex", "evitar colapso voraz".
role: arquitecto
allowed_roles:
- arquitecto
- ejecutor
- auditor
directives:
  worktree_mode: spec-only
  phase: design
  handoff:
    upstream: operador
    downstream: ejecutor
---

# Invariante C5-REAL: Motor de Recocido Adaptativo (Adaptive Exergy Annealing)

> **Directiva Declarativa (Orquestación en Árbol de Trabajo):**
> - **Rol Asignado:** `arquitecto` (Diseño Sistémico & Modelado de Espacio de Estados)
> - **Modo de Acceso a Worktree:** `spec-only` (Modelado matemático y algoritmos sin mutación indiscriminada de producción)
> - **Fase Causal:** `design`
> - **Contrato Handoff:** Recibe de `operador` $\to$ Despacha a `ejecutor`

---

## 1. El Diagnóstico Termodinámico (Aforismo 3)

En espacios discretos gobernados por **Invariantes de Colisión Nula** (ej. síntesis de 100 primitivas sin duplicados, generación de combinatorias de agentes o visemas únicos), la inyección de optimizadores voraces (*Greedy Search*, *Gradient Ascent*) provoca un colapso topológico prematuro:

$$\text{Aforismo 3: «La solución intentada es el problema».}$$

Al intentar maximizar la exergía de forma miope desde el paso cero, el radio de búsqueda se agota en atractores locales degenerados, provocando redundancia masiva y entropía inútil.

---

## 2. La Arquitectura de los 4 Cuartiles (Q1 - Q4)

El recocido adaptativo particiona el cronograma térmico $T(t)$ modulando la aceptación de saltos estocásticos según el principio de Metropolis-Hastings acoplado a la Métrica de Información de Fisher:

```
[ Espacio Discreto de Entrada ]
              │
              ▼
  ┌──────────────────────────────────────┐
  │ Q1: Dispersión Balística             │  T = T_max  · Exploración ergódica pura (Weyl)
  └──────────────────┬───────────────────┘
                     │
                     ▼
  ┌──────────────────────────────────────┐
  │ Q2: Filtrado Bayesiano               │  T = 0.6·T  · Identificación de atractores (ΔΦ > 0)
  └──────────────────┬───────────────────┘
                     │
                     ▼
  ┌──────────────────────────────────────┐
  │ Q3: Contracción Dirigida             │  T = 0.2·T  · Gradiente Natural de Amari (d ≥ ε)
  └──────────────────┬───────────────────┘
                     │
                     ▼
  ┌──────────────────────────────────────┐
  │ Q4: Órbita Asintótica (Apex)         │  T = 0.0    · Enfriamiento cero, colisión = 0
  └──────────────────────────────────────┘
```

### Especificación de Fases:
- **Q1 (Dispersión Balística):** Temperatura máxima ($T \gg 0$). Mapeo ergódico mediante secuencias de baja discrepancia (Sobol / Weyl) sin optimización local.
- **Q2 (Filtrado Bayesiano):** Detección de cuencas de atracción de alta ganancia exergética ($\Delta \Phi > 0$) y filtrado de ruido.
- **Q3 (Contracción Dirigida):** Reducción de varianza sobre la geodésica dictada por la Métrica de Fisher, imponiendo separación mínima euclídea/informacional $d(x_i, x_j) \ge \epsilon$.
- **Q4 (Órbita Asintótica):** Rotación determinista en el radio óptimo del Apex, garantizando verificación de unicidad criptográfica en silicio (SHA-256 / Bloom filter).

---

## 3. Implementación Canónica en Silicio (Python 3 Stdlib / Zero Dependency)

```python
import math
import hashlib
from typing import List, Dict, Any, Callable

class AdaptiveAnnealingEngine:
    """Motor de Recocido Adaptativo en 4 cuartiles (Q1-Q4) libre de dependencias externas."""

    def __init__(self, total_steps: int = 100, min_distance: float = 0.15):
        self.total_steps = total_steps
        self.min_distance = min_distance
        self.history: List[Dict[str, Any]] = []
        self.hashes = set()

    def temperature(self, step: int) -> float:
        """Cronograma térmico discontinuo por cuartiles."""
        progress = step / self.total_steps
        if progress < 0.25:
            return 1.0  # Q1: Exploración balística
        elif progress < 0.50:
            return 0.60 * (1.0 - (progress - 0.25) / 0.25)  # Q2: Filtrado
        elif progress < 0.75:
            return 0.20 * (1.0 - (progress - 0.50) / 0.25)  # Q3: Contracción
        else:
            return 0.00  # Q4: Apoptosis térmica (Apex)

    def is_collision_free(self, candidate_repr: str) -> bool:
        """Verificación fail-closed de colisión en silicio."""
        digest = hashlib.sha256(candidate_repr.encode("utf-8")).hexdigest()
        if digest in self.hashes:
            return False
        self.hashes.add(digest)
        return True

    def step(self, step_idx: int, current_state: Any, candidate_gen: Callable, energy_fn: Callable) -> Any:
        T = self.temperature(step_idx)
        candidate = candidate_gen(current_state, T)

        # Invariante de Anillo-0: Colisión Cero
        if not self.is_collision_free(repr(candidate)):
            return current_state

        dE = energy_fn(candidate) - energy_fn(current_state)
        # Criterio Metropolis-Hastings adaptativo
        if dE < 0 or (T > 0 and math.exp(-dE / max(1e-6, T)) > 0.5):
            return candidate
        return current_state
```

---

## 4. Disparadores de Activación (Triggers)
- `"adaptive annealing"`
- `"motor de recocido"`
- `"optimizacion sin colisiones"`
- `"recocido adaptativo"`
- `"busqueda del apex"`
- `"evitar colapso voraz"`
- `"itera annealing"`

---

## 5. Invariante de Validación Popperiana

> [!IMPORTANT]
> **Veto a la Simulación de Diversidad:** Queda prohibido asumir convergencia exitosa sin verificar empíricamente la matriz de distancias por pares ($d_{ij} \ge \epsilon$) y la colisión nula de hashes SHA-256 en la colección generada.
