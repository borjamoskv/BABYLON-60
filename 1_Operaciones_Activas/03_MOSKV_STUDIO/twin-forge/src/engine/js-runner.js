// === JS Runner — Web Worker based execution ===

let _worker = null;

function createWorkerCode() {
  return `
    let _logs = [];
    let _animFrameId = null;

    const _console = {
      log: (...args) => _logs.push({ type: 'log', text: args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ') }),
      warn: (...args) => _logs.push({ type: 'warn', text: args.map(a => String(a)).join(' ') }),
      error: (...args) => _logs.push({ type: 'error', text: args.map(a => String(a)).join(' ') }),
      info: (...args) => _logs.push({ type: 'info', text: args.map(a => String(a)).join(' ') }),
    };

    self.onmessage = function(e) {
      const { code, id } = e.data;
      _logs = [];
      try {
        const fn = new Function('console', code);
        fn(_console);
        self.postMessage({ id, success: true, logs: _logs });
      } catch (err) {
        _logs.push({ type: 'error', text: err.message });
        self.postMessage({ id, success: false, logs: _logs, error: err.message });
      }
    };
  `;
}

export function runJS(code) {
  return new Promise((resolve) => {
    // Terminate old worker
    if (_worker) { try { _worker.terminate(); } catch {} }

    const blob = new Blob([createWorkerCode()], { type: 'application/javascript' });
    const url = URL.createObjectURL(blob);
    _worker = new Worker(url);

    const id = Date.now();
    const timeout = setTimeout(() => {
      _worker.terminate();
      _worker = null;
      resolve({
        success: false,
        logs: [{ type: 'error', text: '⏰ Tiempo agotado (5s). ¿Tienes un bucle infinito?' }],
        error: 'timeout'
      });
    }, 5000);

    _worker.onmessage = (e) => {
      if (e.data.id === id) {
        clearTimeout(timeout);
        resolve(e.data);
      }
    };

    _worker.onerror = (err) => {
      clearTimeout(timeout);
      resolve({
        success: false,
        logs: [{ type: 'error', text: err.message || 'Error desconocido' }],
        error: err.message
      });
    };

    _worker.postMessage({ code, id });
    URL.revokeObjectURL(url);
  });
}

// Canvas runner — runs JS with canvas context on main thread
export function runCanvasJS(code, canvas) {
  const ctx = canvas.getContext('2d');
  const logs = [];

  const _console = {
    log: (...args) => logs.push({ type: 'log', text: args.map(a => typeof a === 'object' ? JSON.stringify(a) : String(a)).join(' ') }),
    warn: (...args) => logs.push({ type: 'warn', text: args.map(a => String(a)).join(' ') }),
    error: (...args) => logs.push({ type: 'error', text: args.map(a => String(a)).join(' ') }),
    info: (...args) => logs.push({ type: 'info', text: args.map(a => String(a)).join(' ') }),
  };

  try {
    // Cancel previous animation frames
    if (window._twinForgeAnimFrame) {
      cancelAnimationFrame(window._twinForgeAnimFrame);
    }

    // Wrap requestAnimationFrame to track it
    const origRAF = window.requestAnimationFrame.bind(window);
    const wrappedRAF = (cb) => {
      window._twinForgeAnimFrame = origRAF(cb);
      return window._twinForgeAnimFrame;
    };

    const fn = new Function('console', 'ctx', 'canvas', 'requestAnimationFrame', 'document', code);
    fn(_console, ctx, canvas, wrappedRAF, document);
    return { success: true, logs };
  } catch (err) {
    logs.push({ type: 'error', text: err.message });
    return { success: false, logs, error: err.message };
  }
}

// Detect if code uses canvas
export function usesCanvas(code) {
  return /\bctx\b/.test(code) || /\bcanvas\b/.test(code) || /\brequestAnimationFrame\b/.test(code);
}
