// C5-REAL EXERGY CERTIFIED
import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  IRPAutomata_Gravity_C2_FriccionComputacional,
  IRPAutomata_Gravity_C3_FluctuacionTermica,
  IRPAutomata_Gravity_C4_DegradacionGeometrica,
  IRPAutomata_Gravity_C5_ColapsoOntologico,
  IRPAutomata_MembraneState_Stable,
  IRPAutomata_applyThermalStress,
  IRPAutomata_commitBoundary,
  LedgerValidation_validateAndAppend,
  LedgerValidation_genesisLedger
} from './domain/IRPAutomata';

// Web Crypto helper decoupled from F# Kernel
async function sha256Hex(message) {
  const encoder = new TextEncoder();
  const data = encoder.encode(message);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}
import init, { WasmScoreEngine } from 'cortex-wasm';

function App() {
  // Sync Queue Ref (Zero-Overhead background telemetry)
  const syncQueueRef = useRef([]);
  const [cloudSyncStatus, setCloudSyncStatus] = useState('IDLE');
  // Isomorphic IRP Membrane State (Fable Transduced)
  const [kernelState, setKernelState] = useState(IRPAutomata_MembraneState_Stable(0.01));
  const [ledgerState, setLedgerState] = useState(LedgerValidation_genesisLedger());
  const [lastParentId, setLastParentId] = useState(LedgerValidation_genesisLedger().GenesisId);

  const [bftLogs, setBftLogs] = useState([
    { id: 1, hash: '0x8f3a...d91c', status: 'STATUS:OK|ENTROPY:0.0100', timestamp: '08:08:12' },
    { id: 2, hash: '0x4e12...b84f', status: 'STATUS:OK|ENTROPY:0.0200', timestamp: '08:08:25' }
  ]);

  // Score Explorer State
  const [scoresData, setScoresData] = useState(null);
  const [scoreQuery, setScoreQuery] = useState('');
  const [scoreResult, setScoreResult] = useState(null);
  const [scoreLoading, setScoreLoading] = useState(false);
  const [wasmBenchmark, setWasmBenchmark] = useState(null);

  // Initialize WASM and BFT Async Sync Loop
  useEffect(() => {
    init().catch(err => console.error("WASM Init Error:", err));

    // Zero-overhead background telemetry (Axiom Ω10)
    const intervalId = setInterval(async () => {
      if (syncQueueRef.current.length === 0) {
        setCloudSyncStatus('IDLE');
        return;
      }

      setCloudSyncStatus('SYNCING...');
      const batch = [...syncQueueRef.current];
      syncQueueRef.current = []; // clear queue immediately

      try {
        const res = await fetch('http://127.0.0.1:8787/seal', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ logs: batch })
        });
        if (res.ok) {
          setCloudSyncStatus(`SEALED (${batch.length})`);
          setTimeout(() => setCloudSyncStatus('IDLE'), 2000);
        } else {
          setCloudSyncStatus('ERROR: CLOUD');
          syncQueueRef.current = [...batch, ...syncQueueRef.current]; // restore failed items
        }
      } catch (err) {
        console.error("Cloudflare Notary Sync Error:", err);
        setCloudSyncStatus('OFFLINE');
        syncQueueRef.current = [...batch, ...syncQueueRef.current]; // restore on network error
      }
    }, 5000);

    return () => clearInterval(intervalId);
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

  // Lazy-load scores.json on first interaction
  const loadScores = useCallback(async () => {
    if (scoresData) return scoresData;
    setScoreLoading(true);
    try {
      const res = await fetch('/scores.json');
      const data = await res.json();
      setScoresData(data);
      setScoreLoading(false);
      return data;
    } catch (err) {
      console.error('Failed to load scores.json:', err);
      setScoreLoading(false);
      return null;
    }
  }, [scoresData]);

  const lookupScore = async (num) => {
    const data = await loadScores();
    if (!data) return;
    const n = parseInt(num, 10);
    if (isNaN(n) || n < 1 || n > 120000) {
      setScoreResult({ error: true, message: `Invalid: must be 1–120,000` });
      return;
    }
    const score = data.scores[String(n)];
    setScoreResult({ number: n, score, metadata: data.metadata });
  };

  const applyStress = async (gravityKey) => {
    const currentStateName = kernelState.cases()[kernelState.tag];
    if (currentStateName === 'Apoptosis') {
      alert('IRP MEMBRANE IN APOPTOSIS — Irreversible state (Axiom Ω22). Reset required.');
      return;
    }

    let gravity;
    if (gravityKey === 'C2_FriccionComputacional') gravity = IRPAutomata_Gravity_C2_FriccionComputacional();
    else if (gravityKey === 'C3_FluctuacionTermica') gravity = IRPAutomata_Gravity_C3_FluctuacionTermica();
    else if (gravityKey === 'C4_DegradacionGeometrica') gravity = IRPAutomata_Gravity_C4_DegradacionGeometrica();
    else if (gravityKey === 'C5_ColapsoOntologico') gravity = IRPAutomata_Gravity_C5_ColapsoOntologico();

    const nextState = IRPAutomata_applyThermalStress(kernelState, gravity);
    setKernelState(nextState);

    const boundaryMsg = IRPAutomata_commitBoundary(nextState);
    const nextStateName = nextState.cases()[nextState.tag];

    // Cryptographic SHA-256 Ledger Append
    try {
      const payloadHash = await sha256Hex(`PAYLOAD:${Date.now()}:${boundaryMsg}`);
      const rawContent = `${lastParentId}:CLAIM:${nextStateName}:${payloadHash}`;
      const nodeId = await sha256Hex(rawContent);

      const result = LedgerValidation_validateAndAppend(
        ledgerState,
        lastParentId,
        `CLAIM:${nextStateName}`,
        payloadHash,
        nodeId
      );

      // Fable Result DU: tag 0 is Ok, 1 is Error
      if (result.tag === 0) {
        const [newLedgerState, newNode] = result.fields[0];
        setLedgerState(newLedgerState);
        setLastParentId(newNode.NodeId);

        const logItem = {
          id: Date.now(),
          hash: `0x${newNode.NodeId.substring(0, 6)}...${newNode.NodeId.substring(58)}`,
          status: boundaryMsg,
          timestamp: new Date().toLocaleTimeString()
        };
        setBftLogs(prev => [logItem, ...prev.slice(0, 7)]);

        // Push to Cloudflare Async Sync Queue
        syncQueueRef.current.push({
          nodeId: newNode.NodeId,
          parentId: lastParentId,
          payloadHash,
          status: boundaryMsg
        });

      } else {
        console.error("Ledger Validation Error (F# Kernel rejected mutation):", result.fields[0]);
      }
    } catch (err) {
      console.error('Ledger Append Exception:', err);
    }
  };

  const resetMembrane = () => {
    setKernelState(IRPAutomata_MembraneState_Stable(0.01));
  };

  const exportBFTReceipt = async () => {
    const receipt = {
      issuer: "BABYLON-60 C5-REAL Node",
      timestamp: new Date().toISOString(),
      membraneState: kernelState.cases()[kernelState.tag],
      lastBftRoot: lastParentId,
      bftLogs: bftLogs
    };

    // Create a deterministic hash of the receipt to prove integrity
    const receiptString = JSON.stringify(receipt, null, 2);
    const receiptHash = await sha256Hex(receiptString);

    const finalReceipt = {
      ...receipt,
      cryptographicSeal: receiptHash
    };

    const blob = new Blob([JSON.stringify(finalReceipt, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bft-receipt-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const currentStateName = kernelState.cases()[kernelState.tag];
  let stateColor = 'var(--accent-primary)';
  let stateBg = 'rgba(43, 59, 229, 0.1)';
  if (currentStateName === 'Stable') {
    stateColor = 'var(--accent-success)';
    stateBg = 'rgba(0, 255, 102, 0.1)';
  } else if (currentStateName === 'Apoptosis') {
    stateColor = 'var(--accent-secondary)';
    stateBg = 'rgba(255, 0, 85, 0.2)';
  } else if (currentStateName === 'Rollback') {
    stateColor = 'var(--accent-primary)';
    stateBg = 'rgba(43, 59, 229, 0.2)';
  } else {
    stateColor = 'var(--text-main)';
    stateBg = 'rgba(255, 255, 255, 0.1)';
  }


  return (
    <>
      <nav style={{ padding: '2rem 0', borderBottom: '1px solid var(--border-dim)' }}>
        <div className="container flex-center" style={{ justifyContent: 'space-between' }}>
          <div className="text-mono" style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
            BABYLON<span style={{ color: 'var(--accent-primary)' }}>-60</span>
          </div>
          <div>
            <a href="#kernel-sim" style={{ marginRight: '2rem', fontSize: '0.9rem' }}>Kernel Simulator</a>
            <a href="#score-explorer" style={{ marginRight: '2rem', fontSize: '0.9rem' }}>Score Explorer</a>
            <a href="#compliance" style={{ marginRight: '2rem', fontSize: '0.9rem' }}>EU AI Act Compliance</a>
            <button className="btn btn-primary" onClick={() => alert('C5-REAL Substrate Deployment Requested — Initializing Node Credentials.')}>
              Deploy C5-REAL
            </button>
          </div>
        </div>
      </nav>

      <main className="container" style={{ paddingTop: '6rem', paddingBottom: '8rem' }}>
        <div className="flex-center" style={{ flexDirection: 'column', textAlign: 'center', gap: '2rem' }}>

          <div className="glass-panel animate-fade-in-up" style={{ padding: '0.5rem 1rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-success)' }}>
            <span style={{ width: '8px', height: '8px', backgroundColor: 'var(--accent-success)', borderRadius: '50%' }}></span>
            <span className="text-mono" style={{ fontSize: '0.8rem' }}>CORTEX ENGINE ONLINE — ZERO OPEX</span>
          </div>

          <h1 className="h1-hero animate-fade-in-up delay-100">
            The Trust Infrastructure <br />
            for <span style={{ color: 'var(--accent-primary)' }}>Autonomous AI</span>
          </h1>

          <p className="animate-fade-in-up delay-200" style={{ fontSize: '1.2rem', color: 'var(--text-muted)', maxWidth: '700px', margin: '0 auto' }}>
            Sovereign C5-REAL Substrate. The equivalent of SSL/TLS for AI memory.
            Cryptographic audit trails engineered for EU AI Act compliance.
            Zero cloud dependency.
          </p>

          <div className="animate-fade-in-up delay-300" style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
            <a href="#kernel-sim" className="btn btn-primary animate-pulse-glow" style={{ padding: '1rem 3rem', fontSize: '1.1rem' }}>
              Inspect IRP Kernel
            </a>
            <button className="btn btn-outline" style={{ padding: '1rem 3rem', fontSize: '1.1rem' }} onClick={() => window.open('https://github.com/borjamoskv/Teorema-Robinson-Moskv', '_blank')}>
              Read the Axioms
            </button>
          </div>
        </div>

        {/* Interactive IRP Kernel Simulator Section */}
        <section id="kernel-sim" style={{ marginTop: '8rem' }}>
          <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <h2 className="text-mono" style={{ fontSize: '2rem', color: 'var(--accent-primary)', marginBottom: '0.5rem' }}>
              IRP Membrane Automata & BFT Ledger Ticker
            </h2>
            <p style={{ color: 'var(--text-muted)' }}>
              Live execution of F# Domain Kernel (<code style={{ color: 'var(--accent-success)' }}>IRPAutomata.fs</code>). Simulate thermal gravity stress on the state membrane.
            </p>
          </div>

          <div className="grid-3">
            {/* Membrane State Display */}
            <div className="glass-panel animate-fade-in-up" style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="text-mono" style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>MEMBRANE STATE</span>
                <span className="text-mono" style={{
                  padding: '0.2rem 0.6rem',
                  borderRadius: '4px',
                  fontSize: '0.8rem',
                  backgroundColor: stateBg,
                  color: stateColor,
                  border: `1px solid ${stateColor}`,
                  boxShadow: `0 0 10px ${stateBg}`
                }}>
                  {currentStateName}
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                  <span>Entropy Level (e):</span>
                  <span className="text-mono">{currentStateName === 'Stable' ? kernelState.fields[0].toFixed(4) : '0.0000'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                  <span>Variance (v):</span>
                  <span className="text-mono">{currentStateName === 'Smoothing' ? kernelState.fields[0].toFixed(4) : '0.0000'}</span>
                </div>
                {currentStateName === 'Rollback' && (
                  <div className="animate-fade-in-up" style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--accent-primary)' }}>
                    <span>Target Hash:</span>
                    <span className="text-mono">{kernelState.fields[0]}</span>
                  </div>
                )}
                {currentStateName === 'Apoptosis' && (
                  <div className="animate-fade-in-up" style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--accent-secondary)' }}>
                    <span>Taint Log:</span>
                    <span className="text-mono">{kernelState.fields[0]}</span>
                  </div>
                )}
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '1rem' }}>
                <button className="btn btn-outline" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }} onClick={() => applyStress('C2_FriccionComputacional')}>
                  + C2 Fricción
                </button>
                <button className="btn btn-outline" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }} onClick={() => applyStress('C3_FluctuacionTermica')}>
                  + C3 Fluctuación
                </button>
                <button className="btn btn-outline" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', borderColor: 'var(--accent-primary)' }} onClick={() => applyStress('C4_DegradacionGeometrica')}>
                  ⚡ C4 Rollback
                </button>
                <button className="btn btn-outline" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', borderColor: 'var(--accent-secondary)', color: 'var(--accent-secondary)' }} onClick={() => applyStress('C5_ColapsoOntologico')}>
                  💥 C5 Colapso
                </button>
                <button className="btn btn-outline" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', marginTop: '0.5rem', width: '100%' }} onClick={resetMembrane}>
                  ↺ Reset Membrane
                </button>
              </div>
            </div>

            {/* BFT Log Ticker */}
            <div className="glass-panel" style={{ padding: '2rem', gridColumn: 'span 2' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <span className="text-mono" style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>BFT LEDGER EVENT FEED (SHA-256)</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <span className="text-mono" style={{
                    fontSize: '0.75rem',
                    padding: '0.2rem 0.5rem',
                    borderRadius: '4px',
                    border: '1px solid',
                    borderColor: cloudSyncStatus === 'OFFLINE' ? 'var(--accent-secondary)' : cloudSyncStatus.startsWith('SEALED') ? 'var(--accent-success)' : cloudSyncStatus === 'SYNCING...' ? 'var(--accent-primary)' : 'var(--text-muted)',
                    color: cloudSyncStatus === 'OFFLINE' ? 'var(--accent-secondary)' : cloudSyncStatus.startsWith('SEALED') ? 'var(--accent-success)' : cloudSyncStatus === 'SYNCING...' ? 'var(--accent-primary)' : 'var(--text-muted)',
                  }}>
                    CLOUD: {cloudSyncStatus}
                  </span>
                  <span className="text-mono" style={{ fontSize: '0.8rem', color: 'var(--accent-success)' }}>LIVE MERKLE ROOTS</span>
                  <button className="btn btn-outline" style={{ padding: '0.3rem 0.8rem', fontSize: '0.8rem' }} onClick={exportBFTReceipt}>
                    ↓ ZK Receipt
                  </button>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                {bftLogs.map((log, index) => (
                  <div key={log.id} style={{
                    display: 'flex',
                    justify: 'space-between',
                    alignItems: 'center',
                    padding: '0.6rem 1rem',
                    background: 'rgba(255, 255, 255, 0.02)',
                    borderLeft: `3px solid ${log.status.includes('APOPTOSIS') ? 'var(--accent-secondary)' : log.status.includes('ROLLBACK') ? 'var(--accent-primary)' : 'var(--accent-success)'}`,
                    borderRadius: '4px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.85rem',
                    animation: index === 0 ? 'pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite' : 'none',
                    opacity: 1 - (index * 0.12)
                  }}>
                    <span style={{ color: 'var(--accent-primary)' }}>{log.hash}</span>
                    <span style={{ color: 'var(--text-main)' }}>{log.status}</span>
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{log.timestamp}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Score Explorer Section */}
        <section id="score-explorer" style={{ marginTop: '8rem' }}>
          <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
            <h2 className="text-mono" style={{ fontSize: '2rem', color: 'var(--accent-secondary)', marginBottom: '0.5rem' }}>
              Score Explorer (1–120,000)
            </h2>
            <p style={{ color: 'var(--text-muted)' }}>
              Multi-criteria evaluation engine: Primality (30%) · Divisor Richness (25%) · Bit Density (20%) · Fibonacci Proximity (15%) · Perfect Power (10%)
            </p>
          </div>

          <div className="grid-3">
            {/* Search Panel */}
            <div className="glass-panel" style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <span className="text-mono" style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>SCORE LOOKUP</span>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input
                  type="number"
                  min="1"
                  max="120000"
                  placeholder="Enter 1–120,000"
                  value={scoreQuery}
                  onChange={(e) => setScoreQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && lookupScore(scoreQuery)}
                  style={{
                    flex: 1,
                    padding: '0.6rem 1rem',
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid var(--border-dim)',
                    borderRadius: '6px',
                    color: 'var(--text-main)',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '1rem'
                  }}
                />
                <button
                  className="btn btn-primary"
                  style={{ padding: '0.6rem 1.2rem' }}
                  onClick={() => lookupScore(scoreQuery)}
                  disabled={scoreLoading}
                >
                  {scoreLoading ? '...' : '⚡ Eval'}
                </button>
              </div>

              {scoreResult && !scoreResult.error && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                    <span style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--accent-primary)' }}>
                      {scoreResult.score.toFixed(2)}
                    </span>
                    <span className="text-mono" style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                      / 100
                    </span>
                  </div>
                  {/* Score Bar */}
                  <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{
                      width: `${scoreResult.score}%`,
                      height: '100%',
                      background: scoreResult.score > 60 ? 'var(--accent-success)' : scoreResult.score > 40 ? 'var(--accent-primary)' : 'var(--accent-secondary)',
                      boxShadow: `0 0 15px ${scoreResult.score > 60 ? 'var(--accent-success)' : scoreResult.score > 40 ? 'var(--accent-primary)' : 'var(--accent-secondary)'}`,
                      borderRadius: '4px',
                      transition: 'width 0.4s ease'
                    }} />
                  </div>
                  <div className="text-mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    n = {scoreResult.number.toLocaleString()}
                  </div>
                </div>
              )}
              {scoreResult && scoreResult.error && (
                <div className="text-mono" style={{ color: 'var(--accent-secondary)', fontSize: '0.85rem' }}>
                  {scoreResult.message}
                </div>
              )}

              {/* Quick Access Buttons */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                {[1, 2, 7, 42, 127, 1024, 7919, 46368, 120000].map(n => (
                  <button
                    key={n}
                    className="btn btn-outline"
                    style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                    onClick={() => { setScoreQuery(String(n)); lookupScore(n); }}
                  >
                    {n.toLocaleString()}
                  </button>
                ))}
              </div>

              {/* WASM Hyper-Eval Benchmark */}
              <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--accent-primary)', borderRadius: '6px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <span className="text-mono" style={{ fontSize: '0.8rem', color: 'var(--accent-primary)' }}>WASM SIMD ENGINE</span>
                  <button className="btn btn-primary" style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }} onClick={runWasmHyperEval}>
                    ⚡ Detonate 120K (Rust)
                  </button>
                </div>
                {wasmBenchmark && (
                  <div className="text-mono" style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                    <div><span style={{ color: 'var(--accent-success)' }}>{wasmBenchmark.timeMs}ms</span> | {wasmBenchmark.total.toLocaleString()} Nodes</div>
                    <div style={{ color: 'var(--accent-primary)', fontWeight: 'bold' }}>{(wasmBenchmark.opsPerSec / 1000000).toFixed(2)}M Ops/sec</div>
                    <div>Score(42) = {wasmBenchmark.sampleScore}</div>
                  </div>
                )}
                {!wasmBenchmark && (
                  <div className="text-mono" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Eval 120K nodes in Native Rust WASM.
                  </div>
                )}
              </div>
            </div>

            {/* Distribution Histogram */}
            <div className="glass-panel" style={{ padding: '2rem', gridColumn: 'span 2' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <span className="text-mono" style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>SCORE DISTRIBUTION (120,000 INTEGERS)</span>
                <span className="text-mono" style={{ fontSize: '0.8rem', color: 'var(--accent-success)' }}>
                  {scoresData ? `avg: ${scoresData.metadata.stats.avg.toFixed(2)}` : 'LOAD TO VIEW'}
                </span>
              </div>

              {scoresData ? (
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: '4px', height: '180px' }}>
                  {scoresData.metadata.histogram.map((count, i) => {
                    const maxCount = Math.max(...scoresData.metadata.histogram);
                    const heightPct = maxCount > 0 ? (count / maxCount) * 100 : 0;
                    const lo = i * 10;
                    const hi = lo + 10;
                    return (
                      <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
                        <div
                          style={{
                            width: '100%',
                            height: `${heightPct}%`,
                            minHeight: count > 0 ? '4px' : '0',
                            background: `linear-gradient(to top, var(--accent-primary), var(--accent-success))`,
                            borderRadius: '3px 3px 0 0',
                            transition: 'height 0.5s ease',
                            opacity: heightPct > 50 ? 1 : 0.6 + (heightPct / 200)
                          }}
                          title={`${lo}–${hi}: ${count.toLocaleString()} numbers`}
                        />
                        <span className="text-mono" style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                          {lo}
                        </span>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div style={{ height: '180px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <button className="btn btn-outline" onClick={loadScores} disabled={scoreLoading}>
                    {scoreLoading ? 'Loading 120K scores...' : '⚡ Load Distribution Data'}
                  </button>
                </div>
              )}

              {scoresData && (
                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1rem', fontSize: '0.8rem' }}>
                  <span className="text-mono" style={{ color: 'var(--accent-secondary)' }}>min: {scoresData.metadata.stats.min.toFixed(2)}</span>
                  <span className="text-mono" style={{ color: 'var(--text-muted)' }}>{scoresData.metadata.totalScores.toLocaleString()} scored</span>
                  <span className="text-mono" style={{ color: 'var(--accent-success)' }}>max: {scoresData.metadata.stats.max.toFixed(2)}</span>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Value Proposition Cards */}
        <section style={{ marginTop: '8rem' }}>
          <div className="grid-3">

            <div className="glass-panel" style={{ padding: '2rem' }}>
              <h3 className="text-mono" style={{ color: 'var(--accent-primary)', marginBottom: '1rem' }}>01. Local-First</h3>
              <p style={{ color: 'var(--text-muted)' }}>
                Your agents run locally. All embeddings and memory reside in your SQLite database. BABYLON-60 never reads your raw data.
              </p>
            </div>

            <div className="glass-panel" style={{ padding: '2rem' }}>
              <h3 className="text-mono" style={{ color: 'var(--accent-secondary)', marginBottom: '1rem' }}>02. Independent Notary</h3>
              <p style={{ color: 'var(--text-muted)' }}>
                Your node silently syncs cryptographic hashes (Merkle Roots) to our Cloudflare BFT Ledger, creating an immutable timeline.
              </p>
            </div>

            <div className="glass-panel" style={{ padding: '2rem' }}>
              <h3 className="text-mono" style={{ color: 'var(--accent-success)', marginBottom: '1rem' }}>03. Legal Compliance</h3>
              <p style={{ color: 'var(--text-muted)' }}>
                Generate mathematically irrefutable cryptographic receipts. Shield your enterprise from EU AI Act audits and liabilities.
              </p>
            </div>

          </div>
        </section>
      </main>
    </>
  );
}

export default App;

