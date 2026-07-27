import React, { useState, useRef } from 'react';
import { useCTREGuardian } from '../utils/useCTREGuardian';

// C5-REAL: Byzantine Auth Gateway Visualizer with CTRE Optimistic Concurrency
// This component is the visual projection of the Phase 5 Lossy Projection.
export default function ByzantineGateway() {
  const [log, setLog] = useState<string[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);
  const { captureState, atomicCommit } = useCTREGuardian(containerRef);
  
  const addLog = (msg: string) => {
    setLog(prev => [...prev, msg].slice(-15)); // Keep last 15 entries
  };

  const simulateInjection = (quorumSize: number, validSigs: boolean) => {
    addLog(`> [INIT] Payload injected. Quorum Evidence: ${quorumSize}/3. Sigs: ${validSigs ? "VALID" : "FORGED"}`);
    
    // Capture structural DOM hash before latency
    captureState();
    
    // Phase 5 Formal Constants (f=1 -> 2f+1=3)
    const requiredQuorum = 3;
    
    setTimeout(() => {
      // Attempt Atomic Commit
      const success = atomicCommit(() => {
        if (!validSigs) {
          addLog(`❌ [FAIL-STOP] Epistemic Forgery. Adversarial payload rejected.`);
          return;
        }
        
        if (quorumSize < requiredQuorum) {
          addLog(`❌ [FAIL-STOP] Insufficient Quorum (${quorumSize} < ${requiredQuorum}). Epistemic gap detected.`);
          return;
        }
        
        addLog(`✅ [COMMIT] Quorum Truth established. Local state mutated.`);
      });

      if (!success) {
        // C5-REAL: Safe Abort executed without React rendering collision
        console.warn('CTRE Rollback Triggered in Byzantine Gateway');
        setLog(prev => [...prev, `⚠️ [CTRE-ABORT] DOM Mutation detected during latency. Payload dumped.`].slice(-15));
      }
    }, 400);
  };

  return (
    <div ref={containerRef} className="p-5 border border-cortex-accent bg-[#0A0A0A] text-blue-300 font-mono text-sm shadow-[0_0_15px_rgba(0,229,59,0.2)]">
      <h3 className="text-xl font-bold text-cortex-accent mb-2 border-b border-cortex-accent/30 pb-2 uppercase tracking-widest">
        Auth Gateway: Epistemic Boundary
      </h3>
      <p className="mb-6 text-xs text-cortex-muted leading-relaxed">
        <strong>Fase 5 (Lossy Projection):</strong> Este nodo no asume omnisciencia. Sólo muta su estado local si la carga útil está respaldada por firmas criptográficas válidas de un Quórum Bizantino (<code className="bg-[#0A0A0A]/50 px-1">N &ge; 2f + 1</code>).
      </p>
      
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <button 
          onClick={() => simulateInjection(3, true)} 
          className="px-4 py-2 bg-green-900/20 hover:bg-green-900/50 border border-green-500/50 text-green-400 transition-colors uppercase text-xs"
        >
          Inyectar: Quórum Válido (3/3)
        </button>
        <button 
          onClick={() => simulateInjection(2, true)} 
          className="px-4 py-2 bg-yellow-900/20 hover:bg-yellow-900/50 border border-yellow-500/50 text-yellow-400 transition-colors uppercase text-xs"
        >
          Inyectar: Sub-Quórum (2/3)
        </button>
        <button 
          onClick={() => simulateInjection(4, false)} 
          className="px-4 py-2 bg-red-900/20 hover:bg-red-900/50 border border-red-500/50 text-red-400 transition-colors uppercase text-xs"
        >
          Inyectar: Firma Falsificada
        </button>
      </div>
      
      <div className="bg-[#0A0A0A] border border-white/[0.06] p-4 h-48 overflow-y-auto custom-scrollbar font-mono text-xs">
        {log.length === 0 && (
          <span className="text-white/30 animate-pulse">A la espera de telemetría de red...</span>
        )}
        {log.map((entry, i) => (
          <div key={i} className={`mb-1 ${entry.includes('❌') ? 'text-red-400' : entry.includes('✅') ? 'text-green-400' : 'text-blue-300/70'}`}>
            {entry}
          </div>
        ))}
      </div>
    </div>
  );
}
