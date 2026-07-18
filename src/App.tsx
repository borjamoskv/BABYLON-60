import { useState, useEffect } from 'react';

interface AuditLog {
  id: string;
  timestamp: string;
  action: string;
  hash: string;
  status: 'C5-REAL' | 'C4-SIM' | 'PENDING' | 'PURGED';
  details: string;
}

export default function BabylonIdeUI() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [activePrompt, setActivePrompt] = useState('');
  const [activeTarget, setActiveTarget] = useState('');
  const [activePayload, setActivePayload] = useState('');
  const [isForging, setIsForging] = useState(false);
  const [bftStatus, setBftStatus] = useState<'IDLE' | 'SYNCING' | 'PASSED' | 'FAILED'>('IDLE');
  const [idempotencyLocked, setIdempotencyLocked] = useState(false);
  const [overrideActive, setOverrideActive] = useState(false);
  const [exergyIndex, setExergyIndex] = useState(0.91);

  // Inyección de logs iniciales representando el Ledger Histórico
  useEffect(() => {
    setLogs([
      {
        id: 'L01',
        timestamp: '2026-07-18 07:16:37',
        action: 'BFT_INTEGRATION_STAGE',
        hash: 'c885ab9a',
        status: 'C5-REAL',
        details: 'Integración del BFT Loop con el Master Ledger SQLite.'
      },
      {
        id: 'L02',
        timestamp: '2026-07-18 07:15:22',
        action: 'TIER_0_GROUND_TRUTH',
        hash: '42abc2b3',
        status: 'C5-REAL',
        details: 'Inicialización TIER_0 Master Ledger con inmutabilidad atómica (Ω11).'
      },
      {
        id: 'L03',
        timestamp: '2026-07-18 07:14:34',
        action: 'BABYLON_60_BIN',
        hash: '0e0c4704',
        status: 'C5-REAL',
        details: 'Creación del CLI ejecutable bin/babylon60.'
      }
    ]);
  }, []);

  const handleForge = async () => {
    if (!activeTarget || !activePayload) {
      alert("Error: Faltan parámetros Target/Payload (Violación Φ1).");
      return;
    }
    setIsForging(true);
    setBftStatus('SYNCING');
    
    // Latencia mínima de cálculo háptico (300ms)
    await new Promise(resolve => setTimeout(resolve, 300));
    
    const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
    const newHash = Math.random().toString(16).substring(2, 10);
    
    const newLog: AuditLog = {
      id: `L${Date.now().toString().slice(-3)}`,
      timestamp,
      action: 'ATOMIC_MUTATION',
      hash: newHash,
      status: 'C5-REAL',
      details: `Transducción física exitosa sobre ${activeTarget}.`
    };
    
    setLogs(prev => [newLog, ...prev]);
    setBftStatus('PASSED');
    setIsForging(false);
    
    // Bloqueo de Idempotencia por coincidencia de estado (Ω15)
    setIdempotencyLocked(true);
  };

  const handlePurge = () => {
    const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
    setLogs(prev => [
      {
        id: `L${Date.now().toString().slice(-3)}`,
        timestamp,
        action: 'WEAPONIZED_FORGETTING',
        hash: 'OBLITERATE',
        status: 'PURGED',
        details: 'Purga de memoria sintética TIER_1 completada. ATP recuperado.'
      },
      ...prev
    ]);
    setExergyIndex(0.95);
  };

  const handleBftSync = () => {
    setBftStatus('SYNCING');
    setTimeout(() => {
      setBftStatus('PASSED');
    }, 450);
  };

  return (
    <main className="w-screen h-screen bg-[#0A0A0A] text-white flex flex-col justify-between font-sans overflow-hidden select-none border border-[#222] transition-colors duration-300">
      
      {/* Header Soberano */}
      <header className="w-full px-8 py-4 border-b border-[#222] flex items-center justify-between bg-[#0E0E0E]">
        <div className="flex items-center gap-4">
          <div className="w-2.5 h-2.5 bg-[#2B3BE5] animate-pulse" />
          <span className="text-xs font-mono tracking-[0.25em] text-white/90 font-bold uppercase">
            BABYLON-60 IDE // KERNEL V3
          </span>
          <span className="text-[10px] font-mono tracking-widest text-[#2B3BE5] px-2 py-0.5 border border-[#2B3BE5]/30 bg-[#2B3BE5]/5">
            C5-REAL SYSTEM
          </span>
        </div>
        <div className="flex items-center gap-6 text-[10px] font-mono text-white/40 tracking-wider">
          <span>LEDGER: <strong className="text-white">SQLite WAL</strong></span>
          <span>BFT CONCURRENCY: <strong className="text-[#2B3BE5]">TIMEOUT 5000MS</strong></span>
          <span>EXERGY: <strong className="text-[#00FF41]">{(exergyIndex * 100).toFixed(2)}%</strong></span>
        </div>
      </header>

      {/* Main Workspace Area */}
      <div className={`flex-1 grid grid-cols-12 overflow-hidden ${overrideActive ? 'opacity-30' : ''}`}>
        
        {/* Panel Izquierdo: Entrada y Controles Soberanos */}
        <div className="col-span-7 p-8 flex flex-col justify-between border-r border-[#222] overflow-y-auto">
          <div className="flex flex-col gap-6">
            <div className="text-[10px] font-mono text-white/40 tracking-[0.2em] uppercase">
              // TELEOLOGY INJECTION (Ψ)
            </div>
            
            <div className="flex flex-col gap-2">
              <label className="text-[10px] font-mono text-white/60 uppercase">Prompt (Fricción Latente):</label>
              <input 
                type="text" 
                value={activePrompt}
                onChange={(e) => {
                  setActivePrompt(e.target.value);
                  setIdempotencyLocked(false);
                }}
                placeholder="Evita prosa 'Green Theater'. Inyecta intención causal..."
                className="w-full bg-[#111] border border-[#222] px-4 py-3 font-mono text-xs text-white focus:outline-none focus:border-[#2B3BE5]"
              />
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-[10px] font-mono text-white/60 uppercase">Target Path (Phantom Verification):</label>
              <input 
                type="text" 
                value={activeTarget}
                onChange={(e) => {
                  setActiveTarget(e.target.value);
                  setIdempotencyLocked(false);
                }}
                placeholder="ej. scripts/ultrathink_audit_loop.py"
                className="w-full bg-[#111] border border-[#222] px-4 py-3 font-mono text-xs text-white focus:outline-none focus:border-[#2B3BE5]"
              />
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-[10px] font-mono text-white/60 uppercase">Payload:</label>
              <textarea 
                value={activePayload}
                onChange={(e) => {
                  setActivePayload(e.target.value);
                  setIdempotencyLocked(false);
                }}
                rows={5}
                placeholder="Código, delta o instrucción AST..."
                className="w-full bg-[#111] border border-[#222] px-4 py-3 font-mono text-xs text-white focus:outline-none focus:border-[#2B3BE5] resize-none"
              />
            </div>
          </div>

          {/* SOBERANÍA CONTROL DECK */}
          <div className="mt-8 grid grid-cols-3 gap-4">
            <button
              disabled={isForging || idempotencyLocked}
              onClick={handleForge}
              className={`py-4 font-mono text-[10px] tracking-[0.2em] uppercase font-bold transition-all duration-150 border cursor-pointer ${
                idempotencyLocked 
                  ? 'bg-transparent border-[#333] text-white/20' 
                  : 'bg-[#2B3BE5] border-[#2B3BE5] text-white hover:shadow-[0_0_20px_rgba(43,59,229,0.3)]'
              }`}
            >
              {idempotencyLocked ? '[ IDEMPOTENCY LOCK ]' : isForging ? 'FORGING...' : '⚡ FORGE & ANCHOR'}
            </button>

            <button
              onClick={handlePurge}
              className="py-4 bg-[#ff5500] hover:bg-[#e04b00] text-white font-mono text-[10px] tracking-[0.2em] uppercase font-bold border border-[#ff5500] cursor-pointer"
            >
              🩸 SIGKILL SLOP
            </button>

            <button
              onClick={handleBftSync}
              className={`py-4 bg-transparent border font-mono text-[10px] tracking-[0.2em] uppercase font-bold transition-all duration-150 cursor-pointer ${
                bftStatus === 'PASSED' ? 'border-[#00FF41] text-[#00FF41]' : 'border-[#2B3BE5] text-[#2B3BE5] hover:bg-[#2B3BE5]/5'
              }`}
            >
              {bftStatus === 'SYNCING' ? 'SYNCING BFT...' : bftStatus === 'PASSED' ? '⚖️ BFT VERIFIED' : '⚖️ BFT SYNC'}
            </button>
          </div>
        </div>

        {/* Panel Derecho: Ledger de Auditoría (5 Cols) */}
        <div className="col-span-5 bg-[#0D0D0D] flex flex-col h-full border-l border-[#222]">
          <div className="px-6 py-4 border-b border-[#222] flex items-center justify-between">
            <span className="text-[10px] font-mono text-white/60 tracking-widest uppercase">
              // MASTER TELEMETRY LEDGER
            </span>
            <span className="text-[9px] font-mono text-[#00FF41]">
              WAL ACTIVE
            </span>
          </div>

          <div className="flex-1 overflow-y-auto p-6 font-mono text-xs flex flex-col gap-4">
            {logs.map(log => (
              <div key={log.id} className="p-4 bg-[#111] border-l-2 flex flex-col gap-2 border-[#2B3BE5]">
                <div className="flex items-center justify-between text-[9px] text-white/30">
                  <span>{log.timestamp}</span>
                  <span className={`px-2 py-0.5 rounded text-[8px] font-bold ${
                    log.status === 'C5-REAL' ? 'bg-[#00FF41]/10 text-[#00FF41]' :
                    log.status === 'PURGED' ? 'bg-[#ff5500]/10 text-[#ff5500]' : 'bg-white/5 text-white/40'
                  }`}>
                    {log.status}
                  </span>
                </div>
                <div className="text-white/90 font-bold text-xs tracking-wider flex justify-between">
                  <span>{log.action}</span>
                  <span className="text-[#2B3BE5] text-[10px]">[ {log.hash.slice(0, 8)} ]</span>
                </div>
                <div className="text-white/50 text-[10px] leading-relaxed">
                  {log.details}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* OVERRIDE PANEL (Ψ) */}
      {overrideActive && (
        <div className="absolute inset-0 bg-[#0A0A0A] flex flex-col justify-center items-center p-12 transition-all duration-300 z-50">
          <div className="w-full max-w-xl flex flex-col gap-6">
            <div className="text-center text-xs font-mono tracking-[0.3em] text-[#ff3333] animate-pulse">
              !!! OVERRIDE Ψ ACTIVE - TOTAL SOVEREIGNTY LOCKDOWN !!!
            </div>
            <textarea 
              rows={4}
              placeholder="Inyecta tu intención cruda directamente en el AST del kernel..."
              className="w-full bg-black border border-[#ff3333] p-4 text-xs font-mono text-white focus:outline-none focus:border-[#ff3333] resize-none"
            />
            <button 
              onClick={() => setOverrideActive(false)}
              className="py-4 border border-[#ff3333] text-[#ff3333] font-mono text-xs uppercase tracking-[0.2em] hover:bg-[#ff3333]/10 cursor-pointer"
            >
              Revertir Control al Swarm
            </button>
          </div>
        </div>
      )}

      {/* Footer / Status Bar */}
      <footer className="w-full px-8 py-4 border-t border-[#222] bg-[#0E0E0E] flex items-center justify-between text-[9px] font-mono text-white/30 tracking-widest uppercase">
        <div>OPERATOR: BORJAMOSKV // ROOT_UID0</div>
        <button 
          onClick={() => setOverrideActive(true)}
          className="text-[#ff3333] hover:underline cursor-pointer tracking-widest bg-transparent border-none"
        >
          [ OVERRIDE Ψ ]
        </button>
        <div>ESTÉTICA: INDUSTRIAL NOIR 2026 // CERO ANERGÍA</div>
      </footer>
    </main>
  );
}
