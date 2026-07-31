// C5-REAL EXERGY CERTIFIED
import React, { useState } from 'react';
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

