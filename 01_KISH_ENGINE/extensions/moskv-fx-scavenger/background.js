// background.js - Service Worker (Manifest V3)
// Transductor de Frontera (Edge Transducer) entre el Host Nativo (B60) y Google Labs.

let nativePort = null;

function ensureNativeConnection() {
  if (nativePort) {
    return nativePort;
  }

  const hostName = "com.babylon60.moskv_scavenger";
  console.log(`[Moskv-SW] Conectando con Native Host: ${hostName}`);

  try {
    nativePort = chrome.runtime.connectNative(hostName);

    nativePort.onMessage.addListener((message) => {
      console.log("[Moskv-SW] Mensaje recibido del Motor Causal:", message);
      if (message.cmd === "GENERATE" && message.prompt) {
        executeGenerationOnLabs(message.prompt);
      } else if (message.status === "PONG") {
        console.log("[Moskv-SW] PONG recibido del Motor Causal. Latencia sellada.");
      }
    });

    nativePort.onDisconnect.addListener(() => {
      const err = chrome.runtime.lastError ? chrome.runtime.lastError.message : "Desconexión limpia";
      console.warn("[Moskv-SW] Desconectado del Motor Causal. Razón:", err);
      nativePort = null;
    });

    return nativePort;
  } catch (err) {
    console.error("[Moskv-SW] Error crítico inicializando connectNative:", err);
    nativePort = null;
    return null;
  }
}

// Búsqueda de pestaña activa en labs.google e inyección del script
function executeGenerationOnLabs(prompt) {
  chrome.tabs.query({ url: "*://labs.google/*" }, (tabs) => {
    const port = ensureNativeConnection();
    if (!tabs || tabs.length === 0) {
      if (port) {
        port.postMessage({ status: "ERROR", message: "No se encontró una pestaña activa de labs.google" });
      }
      return;
    }

    const labsTab = tabs[0];
    console.log("[Moskv-SW] Disparando FSM en pestaña:", labsTab.id);

    chrome.tabs.sendMessage(labsTab.id, { action: "START_FSM", prompt: prompt }, (response) => {
      const activePort = ensureNativeConnection();
      if (chrome.runtime.lastError) {
        console.error("[Moskv-SW] Fallo de comunicación con FSM:", chrome.runtime.lastError.message);
        if (activePort) {
          activePort.postMessage({ status: "FATAL_ENTROPY", message: chrome.runtime.lastError.message });
        }
        return;
      }
      if (activePort && response) {
        activePort.postMessage(response);
      }
    });
  });
}

// Inicialización pasiva en arranque
ensureNativeConnection();

// Disparador manual al hacer clic en el icono de la extensión
chrome.action.onClicked.addListener((_tab) => {
  console.log("[Moskv-SW] Acción manual: Disparando PING hacia el Kernel...");
  const port = ensureNativeConnection();
  if (port) {
    port.postMessage({
      cmd: "PING",
      payload: `Timestamp: ${Date.now()}`
    });
  } else {
    console.error("[Moskv-SW] No se puede enviar el PING: El túnel IPC está desconectado.");
  }
});
