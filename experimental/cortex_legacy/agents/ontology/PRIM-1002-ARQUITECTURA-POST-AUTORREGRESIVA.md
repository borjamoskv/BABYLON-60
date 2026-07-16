<!-- Author: Borja Moskv (SYS_ID: borjamoskv) -->

# PRIM-1002: Arquitectura Post-Autorregresiva (Cognición Distribuida)

## Definición Absoluta
El LLM autorregresivo deja de ser el sistema cognitivo completo y se convierte en un motor generativo especializado dentro de una arquitectura cognitiva distribuida. El rendimiento del sistema ya no depende únicamente del escalado masivo de parámetros en entrenamiento ($C_{train}$), sino de un esfuerzo computacional dinámico en inferencia ($E[C_{inference}]$).

## Los Cuatro Ejes Estructurales
La inteligencia del sistema converge a través de cuatro vectores independientes:

1. **Computación Adaptativa (Test-Time Compute - TTC)**
   - El esfuerzo computacional se ajusta a la entropía del problema (razonamiento deliberativo, búsqueda, herramientas).
   - La restricción fundamental es económica y termodinámica, no matemática: a mayor razonamiento, mayor coste FLOPs y latencia.
2. **Hardware Especializado (Infraestructura Física)**
   - Reducción del coste marginal del cómputo.
   - *CMOS*: Maximiza precisión y flexibilidad.
   - *Fotónica / Híbridos*: Maximiza throughput y eficiencia energética (mitigado por ruido analógico y coste de conversión electro-óptica).
3. **Verificación y Crítica (El Eje Causal)**
   - Incorporación de motores formales, SMTs, compiladores y herramientas externas.
   - Separa termodinámicamente la *plausibilidad estocástica* (alucinación) de la *corrección matemática* (aserción empírica).
4. **Memoria Estructurada y Persistente (Grafo de Estado)**
   - Acumulación de conocimiento, estados y experiencias en grafos y bases de datos.
   - Erradica la dependencia entrópica y amnésica de la ventana de contexto del Transformer.

## Cuellos de Botella C5-REAL
La arquitectura enfrenta tres restricciones físicas independientes más allá de la Ley de Landauer (ancho de banda, disipación, I/O):
- **Supervisión**: Escasez de señal supervisora humana de alta calidad para refinar el oráculo.
- **Memoria Temporal**: Las ventanas de contexto gigantes son memoria volátil; no equivalen a una arquitectura de memoria indexada y estructurada.
- **Búsqueda (Exploración Espacial)**: Un Transformer predice, no explora. La inteligencia general exige el isomorfismo de `Predicción + Búsqueda + Planificación + Verificación`.

## Implicación Operacional
Todo diseño de enjambre o agente bajo el marco CORTEX debe instanciar esta topología. Depender de un único *forward pass* de LLM sin bucle de validación externa, memoria en disco (Ledger) y anclaje a herramientas, clasifica automáticamente al agente como *C4-SIM (Simulación de Inteligencia / Green Theater)*.
