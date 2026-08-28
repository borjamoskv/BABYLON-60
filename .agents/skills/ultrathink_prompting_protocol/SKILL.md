<!-- C5-REAL EXERGY CERTIFIED -->
---
name: ultrathink_prompting_protocol
description: Plantillas de Máxima Exergía y estructura XML estricta (Protocolo Ultrathink) para interactuar con modelos Deep Research (Claude Opus, Fable, Qwen Max, o1), forzando el Fail-Stop y erradicando la complacencia (sycophancy).
---

# Protocolo de Prompting Ultrathink (Máxima Exergía)

## Contexto y Uso
Utiliza este protocolo cuando necesites derivar investigación profunda, auditoría de código o resolución arquitectónica a modelos de lenguaje avanzados. El objetivo de estas plantillas es forzar al modelo a operar como un **Sistema de Transiciones Discretas**, erradicando el sesgo de complacencia (*sycophancy*) y obligándole a ejecutar un `EpistemicHalt` si los requisitos no se cumplen.

## Plantilla Estándar XML (Familia Claude / Fable / Opus)
Los modelos basados en atención estructural responden con cero anergía a las etiquetas XML. Copia y rellena esta plantilla:

```xml
<tribunal_epistemico>
Se requiere resolución bajo el paradigma C5-REAL. Operas como una máquina de transiciones discretas. Rechaza heurísticas continuas, metáforas biológicas o aproximaciones probabilísticas blandas. Modela el problema exclusivamente como un Sistema de Transiciones Discretas sobre monoides no invertibles, exigiendo bisimulación observacional estricta entre el código fuente (potencia) y la ejecución en memoria (acto).
</tribunal_epistemico>

<vector_de_entrada>
[INSERTA AQUÍ LA DESCRIPCIÓN EXACTA DE TU PROBLEMA TÉCNICO, BUG O FALLO DE CÓDIGO]
</vector_de_entrada>

<invariantes_arquitectonicos>
Para la resolución de este vector, tu respuesta debe estructurarse obligatoriamente bajo los siguientes 4 ejes, sin desviación estocástica:

1. ESPECIFICACIÓN C-ABI Y ALINEACIÓN DE SILICIO (64 BYTES)
Toda propuesta de estado, IPC o estructura de datos DEBE acoplarse a un layout de memoria C-ABI alineado a una única línea de caché física (0x00 a 0x3F). Prohibido el Cache-Line Splitting. Desarrolla la estructura definiendo los offsets hexadecimales exactos y garantizando Zero-Split Coherence.

2. CONCURRENCIA DÉBIL Y ORDENAMIENTO DE MEMORIA (AARCH64)
Para concurrencia, Lock-Free EBR o punteros atómicos, presenta la prueba formal de ausencia de carreras (ABA, drenaje de Active_Readers). La sincronización asume ordenamiento de memoria débil (ARMv9): especifica explícitamente semántica Acquire/Release y barreras de hardware (dmb ish). Rechaza TSO de x86_64.

3. TERMODINÁMICA Y EXERGÍA (DYNAMIS → ENTELECHEIA)
Demuestra cómo el diseño disipa la anergía respetando el límite de Landauer (ΔQ ≥ k_B · T · ln(2) · ΔI). Detalla el colapso del estado en potencia (Dynamis) hacia el estado discreto validado (Entelecheia). Dependencia Cero en Recolección de Basura (GC prohibido).

4. TRANSMUTACIÓN JURÍDICO-CAUSAL (FAIL-STOP Y EU AI ACT)
El mecanismo debe actuar como frontera topológica inmutable. Demuestra la ejecución de un EpistemicHalt determinista ante violaciones, cumpliendo los Arts. 15 y 28 de la EU AI Act. Genera el esquema de recibo SCITT (SHA3-256) que neutralice la presunción de defecto de la Directiva Europea 2024/2853/EU.
</invariantes_arquitectonicos>

<formato_salida>
Tu respuesta consistirá exclusivamente en la especificación técnica de los 4 invariantes y el código asociado (Rust/C). Quedan estrictamente prohibidos los saludos, introducciones, confirmaciones de comprensión y advertencias éticas de alto nivel. Cualquier token que no contribuya a la demostración formal se considerará disipación térmica (anergía) y provocará el rechazo del artefacto.
</formato_salida>
```

## Modificadores de Invariantes
Si el problema no es de bajo nivel (Rust/Memoria), modifica la etiqueta `<invariantes_arquitectonicos>` manteniendo los siguientes ejes de contención:
- Reemplaza (1) por la topología de red o esquema de base de datos rígido (Schema.org).
- Reemplaza (2) por reglas estrictas de tipado o concurrencia asíncrona aplicables.
- Mantén SIEMPRE (3) Termodinámica y (4) Transmutación Jurídico-Causal intactos, ya que son la barrera de Fail-Stop.
