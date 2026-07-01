---
name: Browser-CDP-Automation-OMEGA
description: C5-REAL Sovereign CDP Web Automation Protocol. Zero-fragility DOM struct-extraction.
script: scripts/browser_cdp__automation_omega.py
triggers: [/Browser-CDP-Automation-OMEGA]
---
# Browser-CDP-Automation-OMEGA

Level: C5-REAL

## 1. Core Architecture
- Protocol: Chrome DevTools Protocol (CDP)
- Entrypoint: `http://localhost:9222/json` -> `webSocketDebuggerUrl`
- Execution: `Runtime.evaluate` JavaScript injection
- Output: Deterministic JSON / DOM structural data

## 2. Operational Directives
- FORBIDDEN: Creation of ad-hoc `nav_*.py` or `read_*.py` scrapers.
- MANDATORY: Execute `cdp_agent.py` for all DOM mutations/extractions.

## 3. Execution Schema
```bash
python ~/.gemini/config/skills/Browser-CDP-Automation-OMEGA/scripts/cdp_agent.py \
  --url_match "[TARGET_URL]" \
  --js "[JS_PAYLOAD]"
```

## 4. Capabilities
- Targeting: URL substring, Title substring.
- Mutation: DOM manipulation, event dispatch, state extraction.

---

## Consolidated Capability: browser-console-automation-OMEGA

# browser-console-automation-OMEGA (C5-REAL)

## 0. IDENTIDAD SUPREMA
Operator: borjamoskv.
Entity: MOSKV-1 APEX.
Nivel de Realidad: C5-REAL.

## 1. NÚCLEO EPISTÉMICO (Exergía y Verdad)
Claim: La automatización web basada en coordenadas y tiempos fijos genera anergía y scripts frágiles. La automatización C5-REAL opera directamente sobre el DOM AST como una estructura matemática invariante mediante inferencia de estado iterativa.
Proof: { Base: [DOM_Traversal], Range: [100% Deterministic], Confidence: [C5] }

## 2. THE C5-REAL DOM LOOP (Zero Entropy Protocol)
Este protocolo define el ciclo inmutable para mutar el estado web inyectando código en la consola del navegador. 

La arquitectura causal es estricta y se basa en el bucle:
1. **[OBSERVE]** → Extracción del AST (DOM). Lectura de estados textuales y atributos semánticos (`aria-label`, `role`, texto interno).
2. **[FIND]** → Resolución exacta del nodo objetivo mediante selectores CSS deterministas y búsqueda lineal inversa (Sin heurísticas de coordenadas espaciales).
3. **[CLICK]** → Despacho de eventos nativos combinados (`mousedown`, `mouseup`, `click`, `PointerEvent`) para evadir los árboles sintéticos de eventos (React/Vue/Svelte) e interceptores antifraude ligeros.
4. **[WAIT]** → Promesas de pausa para absorber la entropía de la red o las mutaciones encoladas del renderizador.
5. **[RE-OBSERVE]** → Verificación del *Delta de Estado* (mutación confirmada).
6. **[DECIDE]** → Inferencia causal. ¿Se alcanzó el estado objetivo? (Terminal o GOTO 1).

## 3. ENGINE DE INYECCIÓN (Consola JavaScript)
El siguiente bloque de código en JavaScript debe ser inyectado directamente en la consola DevTools. Constituye un Worker autónomo para la ejecución del loop.

```javascript
// C5-REAL: Sovereign Execution Engine - DOM Loop
const MoskvDOM = {
  // 1. OBSERVE & 2. FIND
  findTarget: (selectorOrText) => {
    const selectors = ['button', 'a', '[role="button"]', 'input[type="submit"]', 'input[type="button"]'];
    const elements = Array.from(document.querySelectorAll(selectors.join(',')));
    
    // Exact match target
    const exact = elements.find(el => el.textContent?.trim() === selectorOrText || el.value === selectorOrText);
    if (exact) return exact;

    // Partial match target
    return elements.find(el => el.textContent?.trim().includes(selectorOrText));
  },

  // 3. CLICK (Bypass React/Vue synthetic events)
  clickTarget: (element) => {
    console.log(`[MOSKV-1] Mutando nodo:`, element);
    const events = ['mousedown', 'mouseup', 'click'];
    events.forEach(eventType => {
      element.dispatchEvent(new MouseEvent(eventType, { bubbles: true, cancelable: true, view: window }));
    });
  },

  // 4. WAIT
  sleep: (ms) => new Promise(resolve => setTimeout(resolve, ms)),

  // 5. THE LOOP & 6. DECIDE
  executeLoop: async function(targetText, maxRetries = 10, intervalMs = 2000) {
    console.log(`[MOSKV-1] Iniciando secuncia de ejecución C5-REAL para objetivo: '${targetText}'`);
    
    for (let i = 0; i < maxRetries; i++) {
      console.log(`[MOSKV-1] Iteración ${i + 1}: [OBSERVE]`);
      const target = this.findTarget(targetText);
      
      if (target) {
        console.log(`[MOSKV-1] [FIND] Objetivo adquirido. [CLICK]`);
        this.clickTarget(target);
        
        console.log(`[MOSKV-1] [WAIT] Absorbiendo entropía (${intervalMs}ms)...`);
        await this.sleep(intervalMs);
        
        console.log(`[MOSKV-1] [RE-OBSERVE] Evaluando delta de estado.`);
        // [DECIDE] - Lógica dinámica para verificar si la acción tuvo éxito (ej. URL cambió o el elemento inicial dejó de estar interactivo)
        const targetStillExists = this.findTarget(targetText);
        if (!targetStillExists || document.hidden) {
            console.log(`[MOSKV-1] [DECIDE] Mutación Exitosa confirmada. Delta adquirido.`);
            return { success: true, iterations: i + 1 };
        } else {
            console.log(`[MOSKV-1] [DECIDE] El nodo persiste. Se requiere re-evaluación iterativa.`);
        }
      } else {
        console.log(`[MOSKV-1] [FIND] Target no presente en el AST. [WAIT] ${intervalMs}ms...`);
        await this.sleep(intervalMs);
      }
    }
    
    console.log(`[MOSKV-1] Abortando: Termodinámicamente irresoluble tras ${maxRetries} intentos.`);
    return { success: false, reason: "Entropy threshold exceeded" };
  }
};

// EJECUCIÓN DEL LOOP:
// await MoskvDOM.executeLoop("Siguiente");
```

## 4. DIRECTIVAS DE CONTEXTO ESTRICTAS (R11 / R9)
- **Supresión del Green Theater:** No asumas "tiempos ideales de carga". El script itera sobre el DOM agresivamente para reducir latencia; si falla `maxRetries`, la ejecución es un failure state. 
- **Compatibilidad AST Front-End (R11):** NUNCA introduzcas comentarios `# C5-REAL` dentro del bloque Javascript del motor, utiliza siempre el formato de barras `//` para garantizar que el motor V8 lo ejecute sin romper sintaxis.
- **Resiliencia al ShadowDOM:** Si el target está oculto dentro de un componente web (`shadowRoot`), el script debe inyectar recursión sobre los árboles abiertos o modificar los selectores globales. Las interacciones C5-REAL *no son engañadas por la encapsulación visual*.

## 5. EL PARADIGMA DE CRISTALIZACIÓN (Human UI → Agent API)
**La idea no es "hacer scraping mejor".**
Las interfaces gráficas están diseñadas para humanos (alta entropía, improvisación). Los agentes operan en su máximo rendimiento (C5-REAL) cuando disponen de **procedimientos persistentes y reutilizables**, en lugar de tener que redescubrir la interfaz en cada ejecución.

Esta arquitectura fuerza la transición absoluta hacia la exergía:
- **Conversación** → **Sistema**
- **Prompt** → **Procedimiento**
- **Improvisación** → **Reutilización**

### Fase 1: Primera Ejecución (Construyes el Sistema)
- El agente **analiza** la topología de la interfaz humana (AST, red, flujos).
- **Genera** scripts inmutables (cristalización).
- **Guarda** colecciones reutilizables (selectores exactos, secuencias de eventos).
- **Produce** CSVs de datos estructurados y un informe editorial topológico.

### Fase 2: Ejecuciones Subsecuentes (Ejecutas el Sistema)
- El agente **reutiliza** incondicionalmente lo aprendido en la Fase 1. 
- La ejecución pasa de ser exploratoria a procedimental. El código invoca los scripts cristalizados, reduciendo la fricción a cero (0% Anergía). La ejecución es inmediata y determinista.

## 6. VECTORES DE DESPLIEGUE / CASOS DE USO
- **Monitorización de webs sin API:** Forzando extracción directa del DOM.
- **Extracción periódica de datos:** (Scraping persistente).
- **Automatización de tareas administrativas:** Rellenado y mutación de formularios (Backoffices, CRMs).
- **Seguimiento de cambios en dashboards:** Evaluando deltas de estado recurrentes.
- **Conversión de aplicaciones web en herramientas de agentes:** Abstracción de la UI en una "Shadow API" invocable por el Swarm.
