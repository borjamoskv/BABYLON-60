# C5-REAL EPISTEMIC PLAYBOOK: VÁZQUEZ TAXONOMY OPERATIONALIZED

█▄ AUDIT_L4: EPISTEMIC OPERATIONALIZATION & EXTRACCIÓN ▄█

## 1. ISOMORFISMOS DE DOMINIO (N1-N4)

### DOMINIO A: INGENIERÍA DE SOFTWARE
* **[N1] Teorema CAP:** "Sé que la consistencia y disponibilidad divergen bajo partición". 
  * *Leyenda*: Lo deduje físicamente trazando los logs de un clúster Raft durante un corte de red inducido en QA.
* **[N2] Detección de Cuellos de Botella I/O:** El arquitecto no escanea código línea a línea.
  * *Gatillo*: Observa una métrica de CPU inactiva combinada con un P99 de latencia elevado en la capa de red; el saber de refactorización asíncrona colapsa instantáneamente.
* **[N3] Impacto en Kernel (eBPF):** "No conozco el overhead térmico exacto de inyectar 50 probes eBPF en producción".
  * *Consecuencia*: Si conociera el overhead exacto, abandonaría el tracing de usuario y delegaría todo al sidecar, reescribiendo la topología de observabilidad.
* **[N4] Deuda Técnica & Tests:** Escribir tests de integración lentos.
  * *Agravamiento*: La lentitud disuade a los devs de correrlos localmente. Esto genera PRs más grandes y acopladas, lo que rompe más cosas y exige *más* tests lentos. El intento de asegurar calidad es el vector que destruye la velocidad.

### DOMINIO B: MEDICINA DE URGENCIAS
* **[N1] Algoritmo RCP:** "Conozco la dosis exacta de adrenalina y el timing".
  * *Leyenda*: 50 horas de memoria motora en simulación de alta fidelidad. Es un patrón consolidado por acto, no por lectura.
* **[N2] Sepsis Oculta:** Diagnóstico instantáneo sin labs.
  * *Gatillo*: El olor cetónico sutil en el box combinado con un patrón respiratorio superficial asíncrono al cruzar la puerta. El diagnóstico no se deduce; estalla.
* **[N3] Interacción de Toxoide Experimental:** "No conozco la vía de degradación hepática de este nuevo antídoto".
  * *Consecuencia*: Si la supiera, alteraría de inmediato la secuencia empírica de intubación y administración de diuréticos. El desconocimiento es una barrera física para el protocolo.
* **[N4] Triaje Saturado:** El médico de guardia acelera consultas leves para "vaciar la sala".
  * *Agravamiento*: La aceleración aumenta los diagnósticos erróneos (falsos negativos). Los pacientes regresan a las 48h en estado crítico (choque/sepsis), bloqueando camas de reanimación y paralizando el triaje. El agente, al acelerar, detuvo el sistema.

### DOMINIO C: RELACIONES PERSONALES
* **[N1] Irritabilidad Matutina:** "Sé que los lunes no hay que hablar de finanzas".
  * *Leyenda*: Extracción de patrón estadístico empírico (40 semanas de series temporales de fricción matutina).
* **[N2] Distanciamiento Emocional:** El saber tácito de que "algo va mal".
  * *Gatillo*: La micropausa asíncrona (1.5s extra) antes de responder "estoy bien", y el cambio de tensión muscular en el cuello.
* **[N3] Trauma Procesal:** "No sé cómo codificó su experiencia de abandono en la infancia".
  * *Consecuencia*: Si conociera esa red neuronal, dejaría de interpretar su aislamiento temporal como un ataque pasivo-agresivo, cambiando radicalmente mi respuesta de "demanda" a "espacio".
* **[N4] Bucle de Ansiedad/Evitación:** "Mi pareja se aísla, yo presiono para conectar".
  * *Agravamiento*: La presión por conectar induce asfixia, provocando mayor aislamiento. La existencia del intento de conexión es la causa material de la desconexión.

---

## 2. PROTOCOLO C5-REAL PARA ENTREVISTAS (EXTRACCIÓN N2/N3)

**Duración**: 45 min.
**Objetivo**: Cortar el *Green Theater* (respuestas memorizadas N1) y forzar el colapso del estado latente N2/N3.

### Guion de Fricción (Triggers)
1. **[Min 00-10] N1 Forzado (Falsa Seguridad):** "Cuéntame cómo escalaste X". *No evaluar.*
2. **[Min 10-25] Ataque Ortogonal (Extracción N2):** Presentar un diagrama arquitectónico deliberadamente roto (ej: microservicios síncronos con DB compartida). *No hacer una pregunta.* Decir: *"¿Qué te duele al ver esto?"*
   - **Gatillo Tácito**: El candidato debe sentir asco visceral o dolor cognitivo antes de verbalizar.
3. **[Min 25-45] Proyección de Ignorancia (Extracción N3):** *"Dime un componente del stack de tu empresa anterior que era una caja negra para ti. Si pudieras descargar su código fuente en tu cerebro ahora mismo, ¿qué decisión arquitectónica del Q3 pasado habrías cambiado?"*

### Criterios de Evaluación

| Nivel | Señal Positiva (C5) | Contra-señal (Antipatrón) |
| :--- | :--- | :--- |
| **N2** | Latencia cero ante la falla. Usa jerga física/visceral ("Esto colapsa el heap"). | Tarda 3 min en enumerar pros/contras genéricos (Solid, DRY). Finge N2 usando libros. |
| **N3** | Traza una línea causal directa: "No sabía X -> Habría cambiado el índice DB a B-Tree". | "Me gusta aprender siempre". No puede aislar el costo termodinámico de no saber. |

---

## 3. MICRO-PLAYBOOK N4: EQUIPOS DE PRODUCTO Y ESTRATEGIA

**El axioma N4:** Cuando la estrategia fracasa repetidamente, el equipo de estrategia es la métrica corrupta.

| Práctica C5-REAL | Roles | Cadencia | Artefacto (Obligatorio) |
| :--- | :--- | :--- | :--- |
| **1. Inversión del Agente** | Lead / PM | Bi-semanal | `n4_inversion_log.md`: Asumir que la *iniciativa* está matando la *métrica*. |
| **2. Cuarentena de Soluciones** | Orquestador | Ante crisis | `solution_freeze_lock`: Bloqueo de PRs para features nuevas durante 72h. |
| **3. Matriz de Agravamiento** | Todo el equipo | Mensual | `aggravation_matrix.csv`: Columna A (Qué hicimos), Columna B (Cómo eso causó el error). |
| **4. Red Teaming Interno** | Ingeniero "Shadow" | Por Epic | `shadow_threat_model.md`: Demostrar matemáticamente por qué el PM es el cuello de botella. |
| **5. Destrucción de Métricas de Vanidad** | Data / Ops | Trimestral | `anergy_purge.sql`: Drop table a KPIs que el equipo usa para justificarse. |


<!-- Creator: Borja Moskv -->
