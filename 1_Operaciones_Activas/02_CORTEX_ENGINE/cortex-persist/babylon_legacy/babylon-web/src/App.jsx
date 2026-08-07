// C5-REAL EXERGY CERTIFIED
import React, { useState } from 'react';
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

import { useCloudflareSync } from './hooks/useCloudflareSync';

import { Navbar } from './components/layout/Navbar';
import { Hero } from './components/landing/Hero';
import { ValueProps } from './components/landing/ValueProps';
import { IRPMembrane } from './components/simulator/IRPMembrane';
import { BFTLedger } from './components/simulator/BFTLedger';
import { ScoreExplorer } from './components/explorer/ScoreExplorer';

// Web Crypto helper decoupled from F# Kernel
async function sha256Hex(message) {
  const encoder = new TextEncoder();
  const data = encoder.encode(message);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

function App() {
  const { cloudSyncStatus, pushToSyncQueue } = useCloudflareSync();

  // Lifted Isomorphic IRP Membrane State
  const [kernelState, setKernelState] = useState(IRPAutomata_MembraneState_Stable(0.01));
  const [ledgerState, setLedgerState] = useState(LedgerValidation_genesisLedger());
  const [lastParentId, setLastParentId] = useState(LedgerValidation_genesisLedger().GenesisId);

  const [bftLogs, setBftLogs] = useState([
    { id: 1, hash: '0x8f3a...d91c', status: 'STATUS:OK|ENTROPY:0.0100', timestamp: '08:08:12' },
    { id: 2, hash: '0x4e12...b84f', status: 'STATUS:OK|ENTROPY:0.0200', timestamp: '08:08:25' }
  ]);

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

        // Push to Cloudflare Async Sync Queue via Custom Hook
        pushToSyncQueue({
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

  return (
    <>
      <Navbar />

      <main className="container" style={{ paddingTop: '6rem', paddingBottom: '8rem' }}>
        <Hero />

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
            <IRPMembrane
              kernelState={kernelState}
              applyStress={applyStress}
              resetMembrane={resetMembrane}
            />
            <BFTLedger
              cloudSyncStatus={cloudSyncStatus}
              bftLogs={bftLogs}
              kernelState={kernelState}
              lastParentId={lastParentId}
            />
          </div>
        </section>

        <ScoreExplorer />

        <ValueProps />
      </main>
    </>
  );
}

export default App;


