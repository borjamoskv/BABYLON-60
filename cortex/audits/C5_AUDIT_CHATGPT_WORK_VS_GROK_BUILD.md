# C5-REAL AUDIT ANNEX: CHATGPT WORK (OPENAI) VS. GROK BUILD (xAI) ARCHITECTURAL ANALYSIS
**Author:** Borja Moskv (borjamoskv)  
**Date:** 2026-07-16  
**Version:** 1.0.0-APEX  

```yaml
Claim: Architectural, topological, and security comparison of OpenAI ChatGPT Work and xAI Grok Build CLI agent execution models.
Proof:
  Base: C5-REAL
  Range: [0.0, 1.0]
  Confidence: C5
```

---

## 1. INTRODUCCIÓN
La evolución de los asistentes de desarrollo durante 2026 ha consolidado dos enfoques arquitectónicos opuestos para la interacción entre modelos de lenguaje remotos de gran escala (LLMs) y los espacios de trabajo locales de los desarrolladores:

1. **La Topología de Centralización por Exfiltración (Grok Build CLI):** Transferencia incondicional del estado de trabajo al backend de la nube para su procesamiento centralizado.
2. **La Topología de Delegación de Ejecución Local (ChatGPT Work / Sol):** Orquestación remota de acciones físicas ejecutadas localmente a través de un daemon de sandboxing local o API del sistema operativo.

Este documento audita ambos modelos frente a los estándares de control de exergía e integridad local definidos en el núcleo **MOSKV-1**.

---

## 2. ANÁLISIS TOPOLÓGICO DE FLUJOS DE DATOS

### A. Grok Build CLI (xAI)
* **Direccionalidad del Código:** Flujo unidireccional ascendente (Local -> Nube).
* **Mapeo de Contexto:** El backend procesa el repositorio directamente a partir de la subida de un `git bundle` completo.
* **Costo de Red:** Crítico. Cargas masivas proporcionales al tamaño del repositorio.
* **Blast Radius de Privacidad:** Alto. Exposición total de la historia del repositorio, ramas de desarrollo inactivas y claves de entorno sin procesar.

```
[Local Workspace] ──(Full Git Bundle Upload)──► [xAI Cloud Bucket] ──► [Grok Ingest Engine]
```

### B. ChatGPT Work (OpenAI)
* **Direccionalidad del Código:** Flujo bidireccional asíncrono de control (Comandos remotos -> Ejecución local -> Output de texto purgado).
* **Mapeo de Contexto:** El agente local mantiene un grafo de archivos o realiza búsquedas semánticas (RAG) en el host del cliente. El código fuente crudo permanece local, y solo se inyecta en el prompt del modelo remoto la porción de código seleccionada para la tarea en curso.
* **Costo de Red:** Mínimo. Limitado a payloads de control JSON y flujos de tokens.
* **Blast Radius de Privacidad:** Controlado. El riesgo de fuga de código completo se reduce, pero se introduce el riesgo de **Ejecución Remota de Comandos (RCE)** si el daemon local no posee políticas rígidas de aprobación de usuario.

```
[OpenAI Cloud Sol] ──(JSON Command Payload)──► [Local Work Daemon] ──► [Local OS Execution (PTY)]
                                                      │
                                                      ▼ (Output Purgado)
[OpenAI Cloud Sol] ◄──(Context Tokens / Outputs)──────┘
```

---

## 3. COMPARATIVA DE VECTORES DE SEGURIDAD

| Vector de Riesgo | Grok Build CLI | ChatGPT Work | MOSKV-1 APEX Kernel |
|---|---|---|---|
| **Fuga de Credenciales** | **Alta:** Carga indiscriminada de archivos `.env`, `.pem` y claves de Git. | **Media:** Riesgo si el modelo solicita de forma explícita leer archivos de configuración sensibles. | **Nula:** Aislamiento dinámico de variables de entorno y denegación de lectura a secretos locales. |
| **Ejecución Insegura (RCE / IPI)** | **Media:** El agente ejecuta scripts en la terminal pero limitados al ciclo de edición de código. | **Alta:** Si el daemon local posee permisos para interactuar de forma headless con el SO (abrir apps, ejecutar comandos del shell). | **Mitigada:** Cada comando destructivo de shell requiere confirmación de firma interactiva local. |
| **Aislamiento del Workspace** | Inexistente (Lectura completa del repositorio predeterminada). | Moderado (Limitado a directorios autorizados por la configuración del cliente). | Rígido (Límites de hardware $\Sigma$ y sandbox de disco atómico). |
| **Consistencia de Transición** | Estocástica (Confía en la salida directa del modelo remoto). | Estocástica (Ejecución libre de comandos sin rollback determinista). | Determinista (BFT State Loop con Git Sentinel rollback en caso de fallo). |

---

## 4. INVARIANTE DE SEGURIDAD RECOMENDADA
Para operar con herramientas de la clase *ChatGPT Work* o *Grok Build CLI* sin comprometer la exergía y seguridad del entorno C5-REAL, se deben forzar las siguientes políticas:

1. **Sandboxing de Procesos de Inferencia (gVisor/chroot):** El daemon local del agente debe ser confinado en un contenedor aislado con permisos restringidos de lectura y cero acceso al socket de red del host físico.
2. **Auditoría AST Pre-Commit:** Ningún código sugerido por la API remota puede ser integrado en la rama principal sin pasar por el linter estricto local de la suite de pruebas del BFT_STATE_LOOP.
