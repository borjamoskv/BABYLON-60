// C5-REAL EXERGY CERTIFIED
import { useState, useEffect } from 'react';
import init, { WasmScoreEngine } from 'cortex-wasm';

export function useWasmEngine() {
  const [wasmBenchmark, setWasmBenchmark] = useState(null);

  useEffect(() => {
    init().catch(err => console.error("WASM Init Error:", err));
  }, []);

  const runWasmHyperEval = () => {
    try {
      const t0 = performance.now();
      const LIMIT = 120000; // 120k (Escala Exergética)
      const engine = new WasmScoreEngine(LIMIT);
      const results = engine.evaluate_batch(1, LIMIT, 144);
      const t1 = performance.now();

      const opsPerSec = (LIMIT / ((t1 - t0) / 1000)).toFixed(0);

      setWasmBenchmark({
        timeMs: (t1 - t0).toFixed(2),
        sampleScore: results[41].toFixed(2), // Score of 42
        total: LIMIT,
        opsPerSec
      });
    } catch (err) {
      console.error("WASM Eval Error:", err);
    }
  };

  return { wasmBenchmark, runWasmHyperEval };
}
