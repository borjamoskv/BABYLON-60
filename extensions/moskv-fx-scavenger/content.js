// content.js - La Mónada Estricta / FSM
// Inyectado por background.js en el contexto de labs.google
// Objetivo: Bypassear el DOM y atacar el enrutador tRPC directamente.

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

/**
 * Máquina de Estados Causal (FSM)
 * @param {string} prompt 
 */
async function runFSM(prompt) {
    console.log(`[Moskv-FX-Scavenger] Iniciando FSM con prompt: "${prompt}"`);
    
    // NOTA EMPÍRICA: En Google Labs real, el projectId está en la URL o en el __NEXT_DATA__.
    // Para esta PoC robusta, extraemos el ID del proyecto de la URL actual si existe, 
    // o definimos uno estático/mock para la demostración estructural.
    const urlMatches = window.location.pathname.match(/\/project\/([a-f0-9\-]+)/);
    const projectId = urlMatches ? urlMatches[1] : "mock-project-id";
    console.log(`[Moskv-FX-Scavenger] Anclado al Proyecto ID: ${projectId}`);

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
    // Simulamos la estructura tRPC de creación de tarea de MusicFX
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

    // Al ejecutarse en el contexto de la página (o extensión en mismo host),
    // el navegador adjunta automáticamente las cookies y cabeceras necesarias.
    const response = await fetch('/fx/api/trpc/generation.createMediaTask?batch=1', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            // En un caso real, podría requerirse el header de reCAPTCHA aquí
        },
        body: JSON.stringify(body)
    });

    if (!response.ok) {
        throw new Error(`Fallo HTTP en SUBMITTING: ${response.status}`);
    }

    const data = await response.json();
    
    // Extraemos el taskId simulado (requiere ajuste según el schema exacto)
    try {
        return data[0].result.data.json.taskId;
    } catch (e) {
        throw new Error("Colisión Bizantina: El payload devuelto no coincide con la axiomatización de TaskId.");
    }
}

async function pollStatus(taskId, timeoutMs = 90000) {
    const startTime = Date.now();
    const pollInterval = 2000;

    const inputParam = encodeURIComponent(JSON.stringify({
        "0": { "json": { "taskId": taskId } }
    }));

    while (Date.now() - startTime < timeoutMs) {
        const response = await fetch(`/fx/api/trpc/generation.getTaskStatus?batch=1&input=${inputParam}`, {
            method: 'GET'
        });

        if (!response.ok) {
            console.warn(`[Moskv-FX-Scavenger] Micro-caída de red (Idempotencia). HTTP ${response.status}`);
            await new Promise(r => setTimeout(r, pollInterval));
            continue;
        }

        const data = await response.json();
        
        try {
            const statusJson = data[0].result.data.json;
            if (statusJson.status === "SUCCESS" && statusJson.signedUrl) {
                return statusJson.signedUrl;
            } else if (statusJson.status === "FAILED") {
                throw new Error("Servidor reportó FAILED. Veto Absoluto.");
            }
            // Si es PENDING o PROCESSING, sigue iterando
        } catch (e) {
            console.error("Error parseando estado", e);
        }

        await new Promise(r => setTimeout(r, pollInterval));
    }

    throw new Error("Límite de Chaitin superado (Timeout). Colapso de la FSM.");
}
