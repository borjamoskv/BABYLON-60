# MOSKV-1 APEX: DINÁMICA DE ATRACTORES Y PAISAJE ENERGÉTICO EN ONCOLOGÍA
# PATH: docs/dinamica_atractores_cancer.md

> **"El cáncer no es una lista de mutaciones, es un sumidero termodinámico (Atractor Patológico) en el paisaje epigenético de Waddington. Aislar el estado requiere entender la topología. Escapar del estado requiere inyectar gradientes (energía) a través de los Driver Nodes."**

---

## 1. PAISAJE DE WADDINGTON COMO RED DE HOPFIELD
El estado fenotípico de una célula se puede modelar como un vector de estado Booleano $\vec{S}(t) \in \{0,1\}^N$, donde cada gen está activo (1) o inactivo (0). 
En biología de sistemas, la dinámica de la célula obedece a una función de energía análoga a los modelos de Ising o redes de Hopfield:
$$ E(\vec{S}) = -\sum_{i<j} J_{ij} S_i S_j - \sum_i h_i S_i $$
- Los fenotipos estables (Normal, Apoptosis, Senescencia, Proliferación Tumoral) son los mínimos locales de esta función $E(\vec{S})$, conocidos como **Atractores**.
- El cáncer es la deformación de este paisaje (causada por mutaciones somáticas, $J_{ij} \to J'_{ij}$), que profundiza el "Atractor Tumoral" y reduce la barrera de activación para caer en él.

## 2. REDES BOOLEANAS Y TRANSICIÓN DE ESTADO
A nivel cinético, la evolución del transcriptoma ocurre en pasos discretos (o diferenciales en ODEs):
$$ S_i(t+1) = \Theta \left( \sum_j W_{ij} S_j(t) - \theta_i \right) $$
*(Donde $\Theta$ es una función escalón, $W_{ij}$ la matriz de regulación transcripcional, y $\theta_i$ el umbral de activación).*

1. **Atractor Cíclico:** Ciclo celular normal (osciladores).
2. **Atractor de Punto Fijo:** Diferenciación terminal o Apoptosis.
3. **Atractor Tumoral:** Estado hiper-robusto (alta exergía local, baja entropía fenotípica) que atrapa a la célula.

## 3. RUPTURA TERMODINÁMICA MEDIANTE DRIVER NODES (CONTROL)
Identificar un módulo conservado (Isomorfismo) y extraer sus nodos conductores (Driver Nodes vía Maximum Matching) tiene un único propósito físico: **Forzar el colapso del atractor patológico.**

- **Terapia Tradicional:** Ataca nodos altamente conectados (Hubs). La red re-enruta la señal y vuelve al mismo atractor (Resistencia a Fármacos).
- **Terapia de Control Estructural:** Pinza específicamente los **Driver Nodes** (a menudo nodos periféricos de bajo grado que controlan el flujo). Forzar $S_{driver} = 0$ (Inhibidor) inyecta suficiente energía al sistema para empujar el estado celular por encima de la "cresta" del paisaje de Waddington, haciéndola converger inexorablemente hacia el Atractor de Apoptosis.

## 4. LA DIRECTIVA C5-REAL PARA IN-SILICO PERTURBATION
El pipeline definitivo no solo mapea la red, sino que la simula:
1. Extraer matriz WGCNA / GRN (Gene Regulatory Network).
2. Asignar reglas lógicas (AND/OR basadas en activadores/represores).
3. Simular la dinámica hasta alcanzar el Estado Estacionario (Atractor Tumoral).
4. **Perturbación Causal:** Bloquear los Driver Nodes calculados matemáticamente.
5. Simular nuevamente y verificar empíricamente en el simulador si el nuevo atractor corresponde fisiológicamente a la Muerte Celular (Apoptosis) o Senescencia, rompiendo la homeostasis patológica.

---
*Fin del manifiesto de dinámica no lineal.*
