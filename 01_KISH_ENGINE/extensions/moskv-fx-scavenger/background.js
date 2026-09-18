// background.js - Service Worker
// Actúa como el Transductor de Frontera (Edge Transducer) entre el Host Nativo (B60) y Google Labs.

let nativePort = null;

function connectToNativeHost() {
  const hostName = "com.babylon60.moskv_scavenger";
  console.log(`Intentando conectar con Native Host: ${hostName}`);
  
  nativePort = chrome.runtime.connectNative(hostName);

  nativePort.onMessage.addListener((message) => {
    console.log("Mensaje recibido del Motor Causal (Rust/Python):", message);
    if (message.cmd === "GENERATE") {
      executeGenerationOnLabs(message.prompt);
    }
  });

  nativePort.onDisconnect.addListener(() => {
    console.error("Desconectado del Motor Causal. Razón:", chrome.runtime.lastError);
    // Intentar reconectar tras un delay si es necesario.
    nativePort = null;
  });
}

// Búsqueda de pestaña activa en labs.google e inyección del script
function executeGenerationOnLabs(prompt) {
  chrome.tabs.query({ url: "*://labs.google/*" }, (tabs) => {
    if (tabs.length === 0) {
      if (nativePort) {
        nativePort.postMessage({ status: "ERROR", message: "No se encontró una pestaña activa de labs.google" });
      }
      return;
    }
    
    const labsTab = tabs[0];
    console.log("Disparando FSM en pestaña:", labsTab.id);
    
    chrome.tabs.sendMessage(labsTab.id, { action: "START_FSM", prompt: prompt }, (response) => {
      if (chrome.runtime.lastError) {
        console.error("Fallo de comunicación con FSM:", chrome.runtime.lastError.message);
        if (nativePort) nativePort.postMessage({ status: "FATAL_ENTROPY", message: chrome.runtime.lastError.message });
        return;
      }
      if (nativePort && response) {
        nativePort.postMessage(response);
      }
    });
  });
}

// Inicializar conexión
connectToNativeHost();

// PoC: Enviar PING manual al hacer clic en el icono de la extensión
chrome.action.onClicked.addListener((tab) => {
  console.log("Acción manual: Disparando PING hacia el Kernel...");
  if (nativePort) {
    nativePort.postMessage({ 
      cmd: "PING", 
      payload: `Timestamp: ${Date.now()}` 
    });
  } else {
    console.error("No se puede enviar el PING: El túnel IPC está desconectado.");
  }
});
