# BABYLON-60: Especificación Formal (v2.5.1-Causal-Determinist)

<div align="center">

[![C5-REAL Verified](https://img.shields.io/badge/C5--REAL-Verified-00F0FF?style=for-the-badge&logo=shield)](https://github.com/borjamoskv/BABYLON-60)
[![Régimen](https://img.shields.io/badge/Régimen-Causal--Determinist-7B1FA2?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)

</div>

> **Axioma Causal-Determinist:** El lenguaje no comunica; compila. Esta especificación formal define la semántica operacional, la máquina abstracta, los invariantes y el modelo de fallos de BABYLON-60, permitiendo a un asistente de pruebas (Lean 4 / Coq) razonar sobre los artefactos exportados sin ambigüedad.

---

## 1. Máquina Abstracta y Modelo Temporal

El motor BABYLON-60 se define formalmente como el autómata determinista de 6 tuplas:

$$\Gamma = \langle \mathcal{R}, \mathcal{H}, \mathcal{L}, \mathcal{Q}, C_{\text{log}}, \mathcal{T} \rangle$$

```
   ┌───────────────────────────────────────────────────────────────────┐
   │                  Máquina Abstracta Γ                              │
   ├───────────┬───────────┬───────────┬───────────┬───────────┬───────┤
   │ Registros │   Heap    │  Ledger   │   Reloj   │ Cola Q    │ Proof │
   │   R[0..N] │  (Lineal) │ (Solo     │ (Planck)  │           │Harness│
   │   (COW)   │           │ Adición)  │  C.tick   │           │   T   │
   └───────────┴───────────┴───────────┴───────────┴───────────┴───────┘
```

Donde:
- $\mathcal{R}$ (**Registros**): Entorno local por corrutina $\rho : \text{Reg} \to v$. Son puramente inmutables y sujetos a *Copy-on-Write* (COW).
- $\mathcal{H}$ (**Heap**): Memoria compartida estructurada con **Tipos Lineales**.
- $\mathcal{L}$ (**Ledger**): Grafo Acíclico Dirigido (DAG) de eventos, ordenado causalmente vía sellos criptográficos.
- $\mathcal{Q}$ (**Cola**): Cola del planificador particionada en $Q_{\text{ready}}$ y $Q_{\text{suspended}}$.
- $C_{\text{log}}$ (**Reloj Lógico**): Tick del planificador ($\mathbb{N}$).
- $\mathcal{T}$ (**Traza**): Acumulador que captura snapshots deterministas tras transiciones observables.

### 1.1 Dominios Temporales
BABYLON-60 desacopla completamente el tiempo físico de la ejecución causal:
- **$C_{\text{phys}}$ (Reloj Físico)**: Entropía externa ($\mathbb{N}$ en ns). **Estrictamente prohibido** de influenciar transiciones de estado.
- **$C_{\text{log}}$ (Reloj Lógico)**: Tick de planificador. Avanza en $+1$ por cada iteración del bucle o instrucción.
- **$C_{\text{sim}}$ (Época de Simulación)**: Tiempo matemático ($\mathbb{N}$), avanzado por eventos explícitos.

---

## 2. Dominio de Tipos y Modelo de Memoria

### 2.1 Dominio de Tipos
El dominio de tipos $\mathbb{T}$ se define estrictamente como:
$$\tau \in \{I64, TIME, F60, UNALLOCATED\}$$

Los valores $v$ son pares de tipo y datos: $v : \tau \times \mathbb{D}_\tau$, donde:
- $\mathbb{D}_{I64} = \mathbb{Z}$
- $\mathbb{D}_{TIME} = \mathbb{N}$ (nanosegundos o ticks)
- $\mathbb{D}_{F60} = \mathbb{Z} \times \mathbb{N}$ (racionales exactos $N / 60^S$)

### 2.2 Exactitud y Reducción Determinista Sexagesimal (`F60`)
El tipo `F60` previene la acumulación de errores y el *Blowup del Numerador* utilizando enteros escalados. La formulación matemática exacta y las cuotas de memoria se rigen por el **Axioma 1: Aritmética Base-60** detallado en la [Especificación Técnica](spec_technical.md).

---

## 3. Semántica Operacional (Small-Step Semantics)

Un frame de corrutina es $q = \langle \text{id}, \text{PC}, \rho \rangle$.
Las transiciones ($\Gamma \vdash op \to \Gamma'$) son atómicas y estrictamente deterministas.

| Opcode | Transición Small-Step |
| :--- | :--- |
| `FORK target` | $\frac{\text{target} \in \text{Labels}}{\Gamma, q \vdash \text{FORK}(\text{target}) \to \Gamma[Q_{\text{ready}} \leftarrow Q_{\text{ready}} \cup \{q_{\text{new}}\}], \mathcal{L} \leftarrow \mathcal{L} \cup \{E_{\text{fork}}\}}$ |
| `AWAIT E` | Si $E \in \mathcal{L}$: $\Gamma, q \vdash \text{AWAIT}(E) \to q[\text{PC} \leftarrow \text{PC}+1]$<br>Si $E \notin \mathcal{L}$: $\Gamma, q \vdash \text{AWAIT}(E) \to \Gamma[Q_{\text{susp}} \leftarrow Q_{\text{susp}} \cup \{q[\text{state} \leftarrow \text{Waiting}(E)]\}]$ |
| `AFTER ticks` | $\frac{\text{target\_time} = C_{\text{log}} + \text{ticks}}{\Gamma, q \vdash \text{AFTER}(\text{ticks}) \to \Gamma[Q_{\text{susp}} \leftarrow Q_{\text{susp}} \cup \{q[\text{state} \leftarrow \text{WaitingTimer}(\text{target\_time})]\}]$ |
| `EXECUTE act` | $\frac{E_{\text{exec}} = \text{Event}(\text{act}, \text{parents}=\text{latest}(\mathcal{L}), C_{\text{log}})}{\Gamma, q \vdash \text{EXECUTE}(\text{act}) \to \Gamma[\mathcal{L} \leftarrow \mathcal{L} \cup \{E_{\text{exec}}\}], q[\text{PC} \leftarrow \text{PC}+1]}$ |
| `HALT` | Inmediatamente detiene la corrutina y exporta su traza a $\mathcal{T}$. |

---

## 4. Invariantes del Sistema y Teorema de BABYLON

Estos invariantes son verificados formalmente por el kernel. Cualquier violación dispara un `CRITICAL_HALT`.

- **I1 (Unicidad Operacional):** Ninguna corrutina ejecuta más de una instrucción por escalar `UNIT.TICK`.
- **I2 (Causalidad Única):** Cada evento $e \in \mathcal{L}$ posee una firma criptográfica única.
- **I3 (Inmutabilidad del Pasado):** $\mathcal{L}$ es estrictamente *append-only*.
- **I4 (Monotonicidad Temporal):** $C.\text{now}() \le C.\text{next}()$.
- **I5 (Ausencia de Anergía):** Toda mutación se refleja transparentemente en $\mathcal{R}$, $\mathcal{H}$ o $\mathcal{L}$.
- *Nota: Para los invariantes arquitectónicos (`INV_BFT_04`, `INV_C5_28`, etc.) y sus mecánicas de validación cruzada, referirse a la especificación central de [Invariantes del Sistema BABYLON-60](spec_invariants.md).*

### 4.1 Teorema de BABYLON (Isomorfismo Semántico-Operacional)

> **Teorema:** $\forall P \in \mathbb{AST}, \text{Canonical}(\mathcal{L}_{\text{Runtime}(P)}) \equiv \text{ProofIR}(P).\mathcal{L}$

Lemas Auxiliares:
1. **Determinismo:** $\Gamma \vdash op \to \Gamma'$ y $\Gamma \vdash op \to \Gamma'' \implies \Gamma' = \Gamma''$.
2. **Independencia Física:** $\forall C_{\text{phys}}, C'_{\text{phys}}, \text{Runtime}(P, C_{\text{phys}}) \equiv \text{Runtime}(P, C'_{\text{phys}})$.

---

## 5. Modelo Formal de Fallos

Ante cualquier fallo causal o violación de invariante:

```
[ CRITICAL HALT ] ──► [ CAUSAL SNAPSHOT ] ──► [ ARTIFACT EXPORT ] ──► [ ABORT PROCESS ]
```