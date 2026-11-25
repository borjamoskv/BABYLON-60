// content.js - La Mónada Estricta / FSM
// Inyectado por manifest.json en el contexto de labs.google
// Objetivo: Bypassear el DOM y atacar el enrutador tRPC directamente.

if (!window.moskvFsmInjected) {
    window.moskvFsmInjected = true;
    console.log("[Moskv-FX-Scavenger] Content Script Injected in labs.google");

    // Escucha comandos del background.js
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        if (request.action === "START_FSM") {
            runFSM(request.prompt)
                .then(result => sendResponse(result))
                .catch(error => sendResponse({ status: "FATAL_ENTROPY", error: error.message }));
            return true; // Keep the message channel open for async response
        }
    });
}

/**
 * Extrae de forma determinista el Project ID del entorno de Google Labs.
 */
function resolveProjectId() {
    // 1. Pathname extraction
    const urlMatches = window.location.pathname.match(/\/project\/([a-f0-9\-]+)/i);
    if (urlMatches && urlMatches[1]) {
        return urlMatches[1];
    }

    // 2. Query param extraction
    const searchParams = new URLSearchParams(window.location.search);
    const paramId = searchParams.get("project") || searchParams.get("projectId") || searchParams.get("id");
    if (paramId) {
        return paramId;
    }

    // 3. Next.js hydration payload inspection (__NEXT_DATA__)
    try {
        const nextDataEl = document.getElementById("__NEXT_DATA__");
        if (nextDataEl && nextDataEl.textContent) {
            const parsed = JSON.parse(nextDataEl.textContent);
            const nextProjectId = parsed?.props?.pageProps?.projectId || parsed?.query?.projectId;
            if (nextProjectId) {
                return nextProjectId;
            }
        }
    } catch (e) {
        console.warn("[Moskv-FX-Scavenger] Fallo en parsing de __NEXT_DATA__:", e);
    }

    // Si no se encuentra en territorio real, aborto estricto
    throw new Error("No se pudo resolver el Project ID en la página de labs.google. Navega a un proyecto activo.");
}

/**
 * Máquina de Estados Causal (FSM)
 * @param {string} prompt 
 */
async function runFSM(prompt) {
    console.log(`[Moskv-FX-Scavenger] Iniciando FSM con prompt: "${prompt}"`);
    
    const projectId = resolveProjectId();
    console.log(`[Moskv-FX-Scavenger] Anclado al Proyecto ID real: ${projectId}`);

    // --- ESTADO: SUBMITTING ---
    const taskId = await submitTask(projectId, prompt);
    console.log(`[Moskv-FX-Scavenger] Transición: QUEUED. Task ID: ${taskId}`);

    // --- ESTADO: POLLING / GENERATING ---
    const resultUrl = await pollStatus(taskId);
    
    // --- ESTADO: CRYSTALLIZED ---
    console.log(`[Moskv-FX-Scavenger] Transición: CRYSTALLIZED. URL: ${resultUrl}`);
    return { status: "CRYSTALLIZED", url: resultUrl };
}

async function submitTask(projectId, prompt) {
    const body = {
        "0": {
            "json": {
                "projectId": projectId,
                "tool": "MUSIC_FX",
                "prompt": prompt,
                "parameters": {
                    "duration": 30,
                    "loop": false
                }
            }
        }
    };

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);

    try {
        const response = await fetch('/fx/api/trpc/generation.createMediaTask?batch=1', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
            signal: controller.signal
        });

        if (!response.ok) {
            throw new Error(`Fallo HTTP en SUBMITTING: ${response.status}`);
        }

        const data = await response.json();
        
        try {
            return data[0].result.data.json.taskId;
        } catch (e) {
            throw new Error("Colisión Bizantina: El payload devuelto no coincide con la axiomatización de TaskId.");
        }
    } finally {
        clearTimeout(timeout);
    }
}

async function pollStatus(taskId, timeoutMs = 90000) {
    const startTime = Date.now();
    let currentInterval = 1500;
    const maxInterval = 6000;

    const inputParam = encodeURIComponent(JSON.stringify({
        "0": { "json": { "taskId": taskId } }
    }));

    while (Date.now() - startTime < timeoutMs) {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 10000);

        try {
            const response = await fetch(`/fx/api/trpc/generation.getTaskStatus?batch=1&input=${inputParam}`, {
                method: 'GET',
                signal: controller.signal
            });

            if (!response.ok) {
                console.warn(`[Moskv-FX-Scavenger] Micro-caída de red (Idempotencia). HTTP ${response.status}`);
            } else {
                const data = await response.json();
                const statusJson = data?.[0]?.result?.data?.json;
                
                if (statusJson?.status === "SUCCESS" && statusJson?.signedUrl) {
                    return statusJson.signedUrl;
                } else if (statusJson?.status === "FAILED") {
                    throw new Error("Servidor reportó FAILED. Veto Absoluto.");
                }
            }
        } catch (e) {
            if (e.name === "AbortError") {
                console.warn("[Moskv-FX-Scavenger] Polling timeout local, reintentando...");
            } else {
                console.error("[Moskv-FX-Scavenger] Error en sondeo:", e.message);
            }
        } finally {
            clearTimeout(timeout);
        }

        // Backoff exponencial con jitter determinista para no saturar tRPC
        currentInterval = Math.min(currentInterval * 1.35 + Math.random() * 300, maxInterval);
        await new Promise(r => setTimeout(r, currentInterval));
    }

    throw new Error("Límite de Chaitin superado (Timeout). Colapso de la FSM.");
}
