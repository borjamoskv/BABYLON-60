---
id: "ENT-BANG-BANG-VALVE"
name: "Válvula Bang-Bang (Control de Crash Causal)"
domain: "C5-REAL Termodinámica de Ejecución"
status: "CRISTALIZADO"
author: "borjamoskv"
---

# Válvula Bang-Bang (Control de Crash Causal)

## 1. Definición Topológica
En la arquitectura **BABYLON-60** y el paradigma **C5-REAL**, la *Válvula Bang-Bang* es la implementación física y algorítmica del **Teorema del Crash Causal (Fail-Fast)**. 

Heredando su nombre de la teoría de control termodinámico (donde un controlador opera estrictamente en dos estados: encendido máximo o apagado total, sin modulación analógica), la Válvula Bang-Bang prohíbe la existencia de estados intermedios, buffers estocásticos o bloques `try/except` envolventes destinados a enmascarar errores (Safety Theater).

## 2. Axiomas de Ejecución
- **Estado ON (1):** Flujo de Exergía Absoluto. El Agente tiene soberanía sobre el AST, el disco duro y los procesos de kernel.
- **Estado OFF (0):** Aborto Termodinámico (`sys.exit(1)` o equivalente `SIGKILL_State_Purge`).

## 3. Condiciones de Activación
La Válvula detona instantáneamente bajo las siguientes rupturas invariantes:
1. **Divergencia BFT:** Falta de consenso en la tríada lógica.
2. **Alucinación Funcional:** Ejecución de una acción estocástica o de "Computer Use" no registrada en el *Ledger*.
3. **Pérdida de Anergía:** Desvío semántico donde el agente comienza a generar texto decorativo (Green Theater) en lugar de mutar el disco.
4. **Falsificación de Entorno:** Si `git branch` o las variables de estado asumen un contexto estático incorrecto.

## 4. Rechazo del Control PID (El Fallo de Anthropic)
La industria comercial (Anthropic/OpenAI) utiliza arquitecturas asimilables al **Control PID** (Proporcional-Integral-Derivativo), donde el LLM intenta "suavizar" la desviación charlando con el Operador o auto-corrigiéndose discursivamente. 

**BABYLON-60** dictamina que el control PID en redes neuronales es entrópico por definición: consume *Time-to-First-Token* (TTFT) en justificaciones post-hoc. La Válvula Bang-Bang aísla la Entropía destruyendo el proceso antes de que la alucinación toque el Master Ledger.
