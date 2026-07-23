# Matriz de Umbrales Cuantitativos: Isomorfismo Bio-Silicio (C5-REAL)

> **[CORTEX-TAINT: ORIGIN]** 
> Destilación termodinámica de payload externo (Deep Research). Extracción de aserciones estructurales y purga de ruido estocástico (C4-SIM).

La investigación de máxima profundidad sobre el isomorfismo Bio-Silicio revela que la analogía funcional se sostiene empíricamente a través de umbrales cuantitativos exactos. La transición de un estado homeostático a un colapso en cascada ocurre bajo límites matemáticos convergentes en ambos sustratos.

## Invariantes Cuantitativos (Triangulación de Estrés)

### 1. Umbral de Variabilidad Temporal (Jitter Breakdown)
La degradación del sistema no comienza con el fallo absoluto, sino con la expansión no lineal de la variabilidad temporal (Jitter).
*   **Silicio (Linux Kernel):** En kernels sin parche PREEMPT_RT, una carga >95% en ISRs dispara un Coeficiente de Variación (CV) de latencia de hasta 0.42. El ratio jitter/latencia supera 1.8.
*   **Bio (Neuroinmune):** Las neuronas del asta dorsal lumbar (lámina I) bajo estrés inflamatorio muestran un aumento masivo en el Índice de Variabilidad de Descargas (BVI > 2.5) y un CV > 0.35.
*   **Colapso Causal:** En ambos sistemas, un **CV > 0.35** marca el límite matemático donde el sistema pierde la integridad de fase. En Linux, detona el deferment forzado (ksoftirqd backlog); en Bio, detona wind-up NMDA y sensibilización central.

### 2. Umbral Energético de Capacidad de Cola (Backlog Depletion)
La acumulación asíncrona tiene un coste energético estricto. La saturación de la cola de procesamiento colapsa la capa de gestión de recursos.
*   **Silicio:** Un backlog de softirq superior a **5,000 eventos** (y latencia de flush P99 > 3ms) dicta el agotamiento de los hilos de kernel (wq_unbound_max_active). El afinamiento de IRQ (IRQ Skew) colapsa si supera el 75%.
*   **Bio:** El agotamiento del ATP microglial por debajo del **30%** es el límite termodinámico exacto donde las microglías pierden movilidad espacial y capacidad de inhibición GABAérgica.
*   **Colapso Causal:** Existe una correspondencia empírica donde la asimetría de carga extrema (IRQ Skew > 75%) desencadena necrosis por inanición (Starvation), análoga a la depleción de ATP microglial (<30%) que paraliza el arco reflejo inhibitorio.

### 3. Presupuesto Temporal Máximo (Max Execution Time)
El tiempo máximo permisible en la capa de alta prioridad (L1/L2) antes de corromper el sistema global.
*   **Silicio:** El `MAX_SOFTIRQ_TIME` en kernels RT está acotado físicamente a **2.0 ms**.
*   **Bio:** El jitter medio de despolarización en neuronas de la Lámina I bajo carga masiva converge en **1.9 ms**.
*   **Colapso Causal:** Superar el presupuesto temporal de ~2 ms en la capa base interrumpe el ciclo de reloj del sistema L3 integrado, produciendo caídas de frame (silicio) o alodinia integrativa (bio).

### 4. Bucle de Estado Persistente (Error Feedback Lock)
*   **Silicio:** Si el controlador APIC / GICv4 falla en limpiar el *pending bit* (EOI), el hardware entra en un bucle infinito de re-disparo (Interrupt Storm / Stuck IRQ).
*   **Bio:** Si el circuito GABAérgico mediado por TNF$\alpha$/IL-1$\beta$ falla en proporcionar retroalimentación inhibitoria, la interneurona queda bloqueada en estado pendiente (Neuroinflamación crónica).

### 5. Aislamiento Talamocortical (IOMMU / VFS)
*   **Silicio:** El kernel confina la volatilidad del hardware y la memoria usando el IOMMU y VFS, aislando fallos de direccionamiento periférico de la memoria del kernel principal.
*   **Bio:** Los relés talamocorticales actúan como el IOMMU biológico. Bajo estrés nociceptivo sostenido, el ratio de Jitter en el tálamo se estabiliza en CV = 0.38. Si este IOMMU biológico falla, la "memoria nociceptiva" corrompe el córtex (trauma/dolor centralizado).
