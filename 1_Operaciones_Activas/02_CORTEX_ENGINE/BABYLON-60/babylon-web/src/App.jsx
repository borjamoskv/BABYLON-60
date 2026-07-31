// C5-REAL EXERGY CERTIFIED
import React, { useState, useEffect, useCallback } from 'react';
import {
  Gravity,
  MembraneState,
  applyThermalStress,
  commitBoundary,
  validateAndAppendNode,
  GENESIS_ID,
  sha256Hex
} from './irpKernel';

function App() {
  // Isomorphic IRP Membrane State (Direct F# Domain Kernel Execution)
  const [kernelState, setKernelState] = useState(MembraneState.Stable(0.01));
  const [ledgerMap, setLedgerMap] = useState(new Map());
  const [lastParentId, setLastParentId] = useState(GENESIS_ID);

  const [bftLogs, setBftLogs] = useState([
    { id: 1, hash: '0x8f3a...d91c', status: 'STATUS:OK|ENTROPY:0.0100', timestamp: '08:08:12' },
    { id: 2, hash: '0x4e12...b84f', status: 'STATUS:OK|ENTROPY:0.0200', timestamp: '08:08:25' }
  ]);

  // Score Explorer State
  const [scoresData, setScoresData] = useState(null);
  const [scoreQuery, setScoreQuery] = useState('');
  const [scoreResult, setScoreResult] = useState(null);
  const [scoreLoading, setScoreLoading] = useState(false);

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
    if (kernelState.type === 'Apoptosis') {
      alert('IRP MEMBRANE IN APOPTOSIS — Irreversible state (Axiom Ω22). Reset required.');
      return;
    }

    const gravity = Gravity[gravityKey];
    const nextState = applyThermalStress(kernelState, gravity);
    setKernelState(nextState);

    const boundaryMsg = commitBoundary(nextState);

    // Cryptographic SHA-256 Ledger Append
    try {
      const payloadHash = await sha256Hex(`PAYLOAD:${Date.now()}:${boundaryMsg}`);
      const { newNodesMap, newNode } = await validateAndAppendNode(
        ledgerMap,
        lastParentId,
        `CLAIM:${nextState.type}`,
        payloadHash
      );

      setLedgerMap(newNodesMap);
      setLastParentId(newNode.nodeId);

      const logItem = {
        id: Date.now(),
        hash: `0x${newNode.nodeId.substring(0, 6)}...${newNode.nodeId.substring(58)}`,
        status: boundaryMsg,
        timestamp: newNode.timestamp
      };
      setBftLogs(prev => [logItem, ...prev.slice(0, 7)]);
    } catch (err) {
      console.error('Ledger Append Exception:', err);
    }
  };

  const resetMembrane = () => {
    setKernelState(MembraneState.Stable(0.01));
  };


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
            <div className="glass-panel" style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="text-mono" style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>MEMBRANE STATE</span>
                <span className="text-mono" style={{
                  padding: '0.2rem 0.6rem',
                  borderRadius: '4px',
                  fontSize: '0.8rem',
                  backgroundColor: kernelState.type === 'Stable' ? 'rgba(0, 255, 102, 0.1)' : kernelState.type === 'Apoptosis' ? 'rgba(255, 0, 85, 0.2)' : 'rgba(43, 59, 229, 0.2)',
                  color: kernelState.type === 'Stable' ? 'var(--accent-success)' : kernelState.type === 'Apoptosis' ? 'var(--accent-secondary)' : 'var(--accent-primary)',
                  border: `1px solid ${kernelState.type === 'Stable' ? 'var(--accent-success)' : kernelState.type === 'Apoptosis' ? 'var(--accent-secondary)' : 'var(--accent-primary)'}`
                }}>
                  {kernelState.type}
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                  <span>Entropy Level (e):</span>
                  <span className="text-mono">{kernelState.entropyLevel !== undefined ? kernelState.entropyLevel.toFixed(4) : '0.0000'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                  <span>Variance (v):</span>
                  <span className="text-mono">{kernelState.variance !== undefined ? kernelState.variance.toFixed(4) : '0.0000'}</span>
                </div>
                {kernelState.targetHash && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--accent-primary)' }}>
                    <span>Target Hash:</span>
                    <span className="text-mono">{kernelState.targetHash}</span>
                  </div>
                )}
                {kernelState.taintLog && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--accent-secondary)' }}>
                    <span>Taint Log:</span>
                    <span className="text-mono">{kernelState.taintLog}</span>
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
                <span className="text-mono" style={{ fontSize: '0.8rem', color: 'var(--accent-success)' }}>LIVE MERKLE ROOTS</span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                {bftLogs.map(log => (
                  <div key={log.id} style={{
                    display: 'flex',
                    justify: 'space-between',
                    alignItems: 'center',
                    padding: '0.6rem 1rem',
                    background: 'rgba(255, 255, 255, 0.02)',
                    borderLeft: `3px solid ${log.status.includes('APOPTOSIS') ? 'var(--accent-secondary)' : log.status.includes('ROLLBACK') ? 'var(--accent-primary)' : 'var(--accent-success)'}`,
                    borderRadius: '4px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.85rem'
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

