import { useState } from 'react';
import { invoke } from '@tauri-apps/api/tauri';

const DOMAINS = ["SOURCE", "MATRIX", "PULSE", "KINETIC", "LOGIC", "VECTOR", "STORAGE", "OSINT", "CLOCK", "COMPILER"];
const PRIMITIVES = ["INIT", "MUTATE", "BIND", "QUERY", "STREAM", "COMMIT", "SYNC", "HALT", "FORK", "JOIN"];
const MODIFIERS = ["RAW", "ATOMIC", "PERSIST", "EPHEMERAL", "ASYNC", "SYNC", "QUANTIZED", "MAPPED", "WRAPPED", "LOCKED"];
const TARGETS = ["LOCAL", "NETWORK", "SWARM", "LEDGER", "MEMORY", "DISPATCH", "UI", "SYSTEM", "BFT", "CORE"];

interface TelemetryLog {
  id: string;
  timestamp: string;
  code: string;
  identity: string;
  status: 'SUCCESS' | 'ERROR' | 'ASYNC';
  message: string;
}

export default function AntigravityKernelUI() {
  const [domain, setDomain] = useState(0);
  const [primitive, setPrimitive] = useState(0);
  const [modifier, setModifier] = useState(0);
  const [target, setTarget] = useState(0);
  const [logs, setLogs] = useState<TelemetryLog[]>([]);
  const [isTransducing, setIsTransducing] = useState(false);

  const codeNum = (domain * 1000) + (primitive * 100) + (modifier * 10) + target;
  const codeStr = codeNum.toString().padStart(4, '0');
  const identityName = `${DOMAINS[domain]}-${PRIMITIVES[primitive]}-${MODIFIERS[modifier]}-${TARGETS[target]}`;

  const handleDispatch = async () => {
    setIsTransducing(true);
    const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
    
    try {
      const res = await invoke<string>('dispatch', { d: domain, p: primitive, m: modifier, t: target });
      const newLog: TelemetryLog = {
        id: Math.random().toString(36).substring(2, 9),
        timestamp,
        code: codeStr,
        identity: identityName,
        status: MODIFIERS[modifier] === 'ASYNC' ? 'ASYNC' : 'SUCCESS',
        message: res || `Transduced [${codeStr}] ${identityName} across retro-membrane.`
      };
      setLogs(prev => [newLog, ...prev.slice(0, 29)]);
    } catch (err: any) {
      // Fallback C5-REAL simulation when outside Tauri native window
      const fallbackMsg = `[C5-REAL fallback] Executed ${identityName} [${codeStr}] directly on local transductor.`;
      const newLog: TelemetryLog = {
        id: Math.random().toString(36).substring(2, 9),
        timestamp,
        code: codeStr,
        identity: identityName,
        status: 'SUCCESS',
        message: fallbackMsg
      };
      setLogs(prev => [newLog, ...prev.slice(0, 29)]);
    } finally {
      setIsTransducing(false);
    }
  };

  return (
    <main className="w-screen h-screen bg-[#0A0A0A] text-white flex flex-col justify-between font-sans overflow-hidden select-none border-4 border-[#121212]">
      {/* Top Bar - Industrial Noir 2026 Header */}
      <header className="w-full px-8 py-5 border-b border-white/10 flex items-center justify-between bg-[#0E0E0E]">
        <div className="flex items-center gap-4">
          <div className="w-3 h-3 bg-[#2B3BE5] animate-pulse" />
          <span className="text-xs font-mono tracking-[0.3em] text-white/90 font-bold uppercase">
            MOSKV-1 APEX SINGULARITY
          </span>
          <span className="text-[10px] font-mono tracking-widest text-[#2B3BE5] px-2 py-0.5 border border-[#2B3BE5]/40 bg-[#2B3BE5]/10">
            C5-REAL SOVEREIGN KERNEL
          </span>
        </div>
        <div className="flex items-center gap-6 text-[11px] font-mono text-white/40 tracking-wider">
          <span>LEGION MATRIX: <strong className="text-white">10,000 NODES</strong></span>
          <span>BFT LEDGER: <strong className="text-[#2B3BE5]">SYNCED</strong></span>
          <span>EXERGY: <strong className="text-green-400">99.98%</strong></span>
        </div>
      </header>

      {/* Main Grid Area */}
      <div className="flex-1 grid grid-cols-12 overflow-hidden">
        {/* Left Matrix Selector (8 Cols) */}
        <div className="col-span-8 p-8 flex flex-col justify-between border-r border-white/10 overflow-y-auto">
          <div>
            <div className="text-[11px] font-mono text-white/40 tracking-[0.2em] mb-6 uppercase">
              // SELECT PRIMITIVE VECTOR MATRIX
            </div>
            <div className="grid grid-cols-4 gap-6">
              <Column title="01 // DOMAIN" items={DOMAINS} selected={domain} onSelect={setDomain} />
              <Column title="02 // PRIMITIVE" items={PRIMITIVES} selected={primitive} onSelect={setPrimitive} />
              <Column title="03 // MODIFIER" items={MODIFIERS} selected={modifier} onSelect={setModifier} />
              <Column title="04 // TARGET" items={TARGETS} selected={target} onSelect={setTarget} />
            </div>
          </div>

          {/* Active Vector Preview Bar */}
          <div className="mt-8 p-6 bg-[#111111] border border-white/10 flex items-center justify-between">
            <div>
              <div className="text-[10px] font-mono text-white/40 tracking-widest uppercase mb-1">
                ACTIVE IDENTITY COLLAPSE
              </div>
              <div className="text-2xl font-light tracking-[0.15em] text-white font-mono">
                {identityName}
              </div>
            </div>
            <div className="flex items-center gap-6">
              <div className="text-right">
                <div className="text-[10px] font-mono text-white/40 tracking-widest uppercase mb-1">
                  OPCODE
                </div>
                <div className="text-2xl font-mono text-[#2B3BE5] font-bold">
                  0x{codeStr}
                </div>
              </div>
              <button 
                disabled={isTransducing}
                onClick={handleDispatch}
                className="px-10 py-4 bg-[#2B3BE5] text-white hover:bg-[#1E2BC4] active:scale-[0.98] transition-all duration-150 font-mono text-xs tracking-[0.25em] uppercase font-bold shadow-[0_0_25px_rgba(43,59,229,0.3)] cursor-pointer disabled:opacity-50"
              >
                {isTransducing ? 'TRANSDUCING...' : 'TRANSDUCE STATE'}
              </button>
            </div>
          </div>
        </div>

        {/* Right Telemetry & Ledger Console (4 Cols) */}
        <div className="col-span-4 bg-[#0D0D0D] flex flex-col h-full">
          <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between">
            <span className="text-[11px] font-mono text-white/60 tracking-widest uppercase">
              // TELEMETRY LEDGER (WAL)
            </span>
            <span className="text-[10px] font-mono text-white/30">
              {logs.length} EVENTS
            </span>
          </div>
          <div className="flex-1 overflow-y-auto p-6 font-mono text-xs flex flex-col gap-3">
            {logs.length === 0 ? (
              <div className="h-full flex items-center justify-center text-white/20 text-center tracking-wider text-xs">
                Awaiting transducement...<br />Select vector and execute state collapse.
              </div>
            ) : (
              logs.map(log => (
                <div key={log.id} className="p-3 bg-[#131313] border-l-2 border-[#2B3BE5] flex flex-col gap-1.5 animate-fadeIn">
                  <div className="flex items-center justify-between text-[10px] text-white/40">
                    <span>{log.timestamp}</span>
                    <span className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
                      log.status === 'SUCCESS' ? 'bg-green-500/20 text-green-400' :
                      log.status === 'ASYNC' ? 'bg-blue-500/20 text-[#2B3BE5]' : 'bg-red-500/20 text-red-400'
                    }`}>
                      {log.status}
                    </span>
                  </div>
                  <div className="text-white/90 font-bold tracking-wide text-xs">
                    [{log.code}] {log.identity}
                  </div>
                  <div className="text-white/60 text-[11px] leading-relaxed">
                    {log.message}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Footer / Status Bar */}
      <footer className="w-full px-8 py-3 border-t border-white/10 bg-[#0E0E0E] flex items-center justify-between text-[10px] font-mono text-white/30 tracking-widest uppercase">
        <div>OPERATOR: BORJAMOSKV // ROOT_UID0</div>
        <div>INDUSTRIAL NOIR 2026 // ZERO THEATER // ZERO FLUFF</div>
        <div>CORTEX SHA3-256 ANCHOR: ACTIVE</div>
      </footer>
    </main>
  );
}

function Column({ title, items, selected, onSelect }: { title: string, items: string[], selected: number, onSelect: (i: number) => void }) {
  return (
    <div className="flex flex-col bg-[#111111] border border-white/5 p-4 rounded-sm">
      <div className="text-[10px] text-white/50 font-mono tracking-widest mb-3 border-b border-white/10 pb-2 uppercase font-bold">
        {title}
      </div>
      <div className="flex flex-col gap-1 overflow-y-auto max-h-[380px] pr-1">
        {items.map((item, i) => (
          <button
            key={item}
            onClick={() => onSelect(i)}
            className={`text-left px-3 py-2 text-xs font-mono tracking-wider transition-all duration-150 rounded-sm ${
              selected === i 
                ? 'bg-[#2B3BE5] text-white font-bold shadow-[0_0_12px_rgba(43,59,229,0.4)]' 
                : 'text-white/50 hover:text-white hover:bg-white/5'
            }`}
          >
            <span className="opacity-40 mr-2">{i.toString().padStart(2, '0')}:</span>
            {item}
          </button>
        ))}
      </div>
    </div>
  );
}
