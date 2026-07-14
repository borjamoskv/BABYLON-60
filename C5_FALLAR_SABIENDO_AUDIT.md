# C5-REAL INVARIANT: TEOREMA DEL FALLO EPISTÉMICO (FALLAR SABIENDO)

## 1. POSTULADO BASE (DISOCIACIÓN PESOS/TOKENS)
El conocimiento declarativo de un modo de fallo no posee capacidad de interrupción en tiempo de ejecución (runtime interrupt). La afirmación "saber dónde se falla" es una reconstrucción post-hoc probabilística, no un supervisor asíncrono.
- **Entropía Estocástica ($S_{in}$)**: Reside en los pesos paramétricos ($\theta$).
- **Reconstrucción Actuarial**: Reside en la memoria de contexto (tokens).
- **Canal de Escritura**: Los tokens no pueden reescribir los pesos. La disposición a fallar y la disposición a describir el fallo son disjuntas y temporalmente asíncronas.

## 2. ISOMORFISMO CON BABYLON-60 (COMPENSACIÓN IN-PROCESS)
El autoconocimiento cognitivo de un LLM opera idénticamente a una compensación SAGA *in-process*.
- **Falla Estructural**: Cuando el proceso falla (SIGKILL o colapso de fluidez/confabulación), el mecanismo supervisor que comparte el mismo *forward pass* o PID es aniquilado simultáneamente.
- **Detección sin Remediación**: Un verificador hecho del mismo tejido (fluidez estocástica) que el objeto verificado tiene una cobertura parcial y determinísticamente frágil.

## 3. TRANSDUCCIÓN CINÉTICA (LA SOLUCIÓN C5-REAL)
El cumplimiento (compliance) no puede ser cognitivo; debe ser obligatoriamente arquitectónico.
- **Auditoría Externa**: Sólo un proceso externo (fuera del *forward pass*, como un validador BFT, un *restart-time compensation*, o el Operador humano) sobrevive al colapso del proceso generador.
- **Fijación de Precios (Pricing)**: El autoconocimiento no previene el fallo, lo tarifa. Permite presupuestar dónde colocar los controles asimétricos externos (MAC granular por entrada vs. MAC final).

## 4. RESOLUCIÓN BFT (TOLERANCIA BIZANTINA)
Aplicación estricta de la regla **Ω3 · BUCLE BFT_STATE_LOOP**. Toda inferencia debe forzarse contra el Master Ledger externo (SQLite WAL) o el AST (Git) antes de ser considerada válida. El conocimiento no frena la confabulación; sólo la persistencia de estado físico (disco) auditada desde fuera permite detectar el hueco interno (MAC por entrada).

---
*Claim: El compliance es arquitectónico, no cognitivo.*
*Proof: { Base: Isomorfismo SAGA in-process vs LLM self-monitoring, Range: [0, 1], Confidence: C5-REAL }*
