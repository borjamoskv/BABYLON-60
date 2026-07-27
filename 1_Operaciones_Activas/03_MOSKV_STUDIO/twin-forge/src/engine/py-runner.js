// === Python Runner — Pyodide lazy-loaded ===

let pyodideInstance = null;
let loading = false;
let loadPromise = null;

export async function loadPyodide() {
  if (pyodideInstance) return pyodideInstance;
  if (loadPromise) return loadPromise;

  loading = true;
  loadPromise = new Promise(async (resolve, reject) => {
    try {
      // Dynamically load pyodide from CDN (first time only, then cached by SW)
      if (!window.loadPyodide) {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.js';
        script.async = true;
        await new Promise((res, rej) => {
          script.onload = res;
          script.onerror = () => rej(new Error('No se pudo cargar Python. ¿Hay internet?'));
          document.head.appendChild(script);
        });
      }

      pyodideInstance = await window.loadPyodide({
        indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.27.7/full/',
      });

      loading = false;
      resolve(pyodideInstance);
    } catch (err) {
      loading = false;
      loadPromise = null;
      reject(err);
    }
  });

  return loadPromise;
}

export async function runPython(code) {
  const logs = [];

  try {
    const pyodide = await loadPyodide();

    // Redirect stdout/stderr
    pyodide.setStdout({ batched: (msg) => logs.push({ type: 'log', text: msg }) });
    pyodide.setStderr({ batched: (msg) => logs.push({ type: 'error', text: msg }) });

    await pyodide.runPythonAsync(code);
    return { success: true, logs };
  } catch (err) {
    const errorMsg = err.message || String(err);
    // Make Python errors friendlier
    let friendly = errorMsg;
    if (errorMsg.includes('SyntaxError')) {
      friendly = '🐍 Error de sintaxis: revisa que no falten : o paréntesis';
    } else if (errorMsg.includes('NameError')) {
      friendly = '🐍 Variable no encontrada: ¿la has escrito bien?';
    } else if (errorMsg.includes('IndentationError')) {
      friendly = '🐍 Error de indentación: revisa los espacios al inicio de la línea';
    }
    logs.push({ type: 'error', text: friendly });
    return { success: false, logs, error: errorMsg };
  }
}

export function isPyodideLoaded() {
  return pyodideInstance !== null;
}

export function isPyodideLoading() {
  return loading;
}
