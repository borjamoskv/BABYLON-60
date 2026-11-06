# 📐 Especificación Formal: Álgebra de Transiciones Cognitivas (CTA) en Enjambres
## Modelo Matemático y Dinámica de Transiciones Puras para Enjambres Masivos

> **Dominio:** `edin.swarms.cta` / BABYLON-60  
> **Versión:** 1.0.0-PROD  
> **Estatus Epistémico:** Formal / Rigor Matemático  
> **Firma de Autoría:** Borja Fernández Angulo — Investigador en Sistemas Complejos  

---

## 1. Fundamentos y Espacio de Estados

Sea un sistema distribuido de agentes compuesto por $N$ transiciones cognitivas concurrentes. Rechazamos el espacio de estados tradicional basado en productos cartesianos de memorias individuales mutables:

$$\mathcal{H}_{\text{tradicional}} = \prod_{i=1}^N \mathcal{M}_i \quad (\text{Colapso por explosión de estados})$$

Definimos en su lugar un **Ledger Inmutable** $\mathcal{L}$, representado como un monoide libre generado por el conjunto de eventos atómicos $\mathcal{E}$:

$$\mathcal{L} = (E^*, \cdot, \varepsilon)$$

Donde cada evento $e \in \mathcal{E}$ es una tupla canónica:
$$e = \langle t_k, \kappa_i, \alpha, \delta, \sigma \rangle$$
*   $t_k \in \mathbb{N}$: Marca de orden secuencial estricto en el Write-Ahead Log (WAL).
*   $\kappa_i \in \mathcal{K}$: Identificador efímero de la transición cognitiva ejecutora.
*   $\alpha \in \mathcal{A}$: Tipo de acción semántica clasificada.
*   $\delta \in \Delta$: Carga útil (payload estructurado en JSON/C-ABI).
*   $\sigma \in \{0, 1\}^{512}$: Firma criptográfica o digest SHA-256 de verificación.

---

## 2. El Operador de Proyección de Markov ($\mathcal{P}$)

Para impedir que cada nodo consuma la totalidad de $\mathcal{L}$ (lo que induciría un coste de inferencia $\mathcal{O}(|\mathcal{L}|)$), definimos el **Operador de Proyección de Manta de Markov**:

$$\mathcal{P}_{\mu}: \mathcal{L} \times \mathcal{M} \longrightarrow \mathcal{S}_{\text{local}}$$

Donde $\mathcal{M}$ es la máscara de relevancia semántica del rol del nodo. La proyección se formaliza como un homomorfismo de monoides condicionado:

$$\mathcal{P}_{\mu}(e_1 \cdot e_2) = \mathcal{P}_{\mu}(e_1) \oplus \mathcal{P}_{\mu}(e_2)$$

### Invariante de Confinamiento de Información ($\Delta I \le 0$):
$$\mathcal{H}(\mathcal{S}_{\text{local}}) \le \mathcal{H}_{\max} = \text{constante} \quad \forall |\mathcal{L}| \in [1, \infty)$$

La entropía de Shannon del estado local inyectado al modelo de lenguaje está acotada superiormente por una constante universal fija ($\mathcal{H}_{\max}$), garantizando tiempo de inferencia y coste de tokens invariantes frente al crecimiento del historial.

---

## 3. Transición Cognitiva Pura ($T$)

Un agente en el enjambre no es un proceso daemon continuo. Se formaliza estrictamente como una **función de transición pura**:

$$T_i: \mathcal{S}_{\text{local}} \longrightarrow \Delta\mathcal{L} \cup \{\bot\}$$

Donde:
*   $\Delta\mathcal{L} \subset \mathcal{E}$: Conjunto ordenado de nuevos eventos propuestos para su commit en el Ledger.
*   $\bot$: Símbolo de rechazo / no-operación (el nodo determina que no se requiere acción).

### Propiedad de Determinismo Verificable:
Dada una semilla estocástica congelada $\xi$ o un decodificador greedy con temperatura $T=0$:
$$\forall s \in \mathcal{S}_{\text{local}}, \quad T_i(s; \xi) = T_i(s; \xi) \implies \text{Reproducibilidad Bit a Bit}$$

---

## 4. Control Termodinámico MCTS y Poda por Entropía

La exploración masiva del enjambre se modela como un árbol de búsqueda de Monte Carlo Termodinámico (*Swarm Thermodynamic MCTS*). Cada nodo del árbol representa una proyección proyectada de estado $s$.

Definimos la **Energía Libre Esperada (EFE)** de Friston para la trayectoria de un clúster de agentes:

$$\text{EFE}(s) = \underbrace{D_{\text{KL}}\big(q(o|s) \parallel p(o)\big)}_{\text{Riesgo Epistémico}} + \underbrace{\mathbb{E}_{q}[\mathcal{H}(s|o)]}_{\text{Ambigüedad Residual}}$$

### Regla de Poda Temprana (*Early Stopping Condition*):
Si la entropía normalizada de las respuestas del enjambre supera el umbral crítico $\theta_{\text{crit}}$:

$$\tanh\big(\mathcal{H}_{\text{norm}}(s)\big) \ge \theta_{\text{crit}} \implies \text{PruneBranch}(s)$$

Los recursos computacionales asignados a dicha rama se liberan inmediatamente mediante un mecanismo de cancelación colaborativa de corutinas (`asyncio.Task.cancel()`), evitando la saturación de cuotas de API en trayectorias divergentes o alucinatorias.

---

## 5. El Protocolo de Compromiso en Dos Fases (Two-Phase Commit para $T_{eff}$)

Las transiciones se bifurcan en dos clases ortogonales según sus efectos en el sistema:

$$\mathcal{T} = \mathcal{T}_{\text{pure}} \sqcup \mathcal{T}_{\text{eff}}$$

1. **Transiciones Puras ($\mathcal{T}_{\text{pure}}$):** Operan exclusivamente en memoria volátil o lectura analítica. Tienen concurrencia no acotada:
   $$\text{Concurrency}(\mathcal{T}_{\text{pure}}) = N_{\text{max}} = 10.000$$

2. **Transiciones con Efectos Externos ($\mathcal{T}_{\text{eff}}$):** Modifican el mundo exterior (escritura en disco, ejecución de comandos shell, transacciones de red o pagos). Sometidas al Teorema de Reducción de Concurrencia:
   $$\text{Concurrency}(\mathcal{T}_{\text{eff}}) = 1$$

### Protocolo 2PC:
```
Agente Worker (Ring-2)              Orquestador BFT (Ring-0)
       │                                       │
       │─── 1. Prepare: AttestationEnvelope ──>│
       │    (Digest SHA-256 + Diff + Sig)      │
       │                                       │── [Auditoría AST Ring-0]
       │                                       │── [Verificación Manta Markov]
       │<── 2. Commit / Abort Token ───────────│
       │                                       │
```

---

## 6. Teorema de Homeostasis y Convergencia de Terminación

Un enjambre tradicional finaliza cuando su cola de tareas está vacía ($Q = \emptyset$). En presencia de bucles de delegación, la cola nunca se vacía, produciendo bloqueos o costes desorbitados.

En `02_EDIN_SWARMS`, la condición de parada se define por convergencia termodinámica del sistema:

### Criterio de Parada Homeostática:
$$\lim_{t \to \infty} \left\| \nabla \text{EFE}(G_t) \right\|_2 < \epsilon \quad \land \quad \Delta\mathcal{L}_t = \emptyset$$

Cuando el gradiente de energía libre cae por debajo de la cota de tolerancia $\epsilon$, el hipervisor declara el **Colapso Homeostático del Enjambre**. Todas las corutinas finalizan ordenadamente, emitiendo un reporte final firmado en formato SCITT RFC 9942.

---
**Firmado:**  
**Borja Fernández Angulo**  
*Investigador en Sistemas Complejos*
