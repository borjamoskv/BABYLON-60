// @ts-nocheck
import React, { useState } from 'react';
import { Database, Shield, CheckCircle, AlertTriangle, Key, Cpu, Users, ArrowRight } from 'lucide-react';

interface EventLog {
  id: string;
  fact: string;
  prevHash: string;
  hash: string;
  status: 'C4-SIM' | 'C5-REAL';
  timestamp: string;
}

export default function CortexExplorer() {
  const [activeTab, setActiveTab] = useState<'memoria' | 'agentes' | 'influencers'>('memoria');
  
  // Tab 1: Memory States
  const [memoryInput, setMemoryInput] = useState('');
  const [memoryLogs, setMemoryLogs] = useState<EventLog[]>([
    {
      id: "ev_001",
      fact: "Agent initialized and connected to base SQLite memory store.",
      prevHash: "GENESIS",
      hash: "0000ab43c983d98ef92a83ef841c9b2e88ad9cf216a73c1d9f82d1c9e83cf312",
      status: "C4-SIM",
      timestamp: "18:24:00"
    },
    {
      id: "ev_002",
      fact: "Retrieved system target pricing: $49/mo (Pro), $299/mo (Legion).",
      prevHash: "0000ab43c983d98ef92a83ef841c9b2e88ad9cf216a73c1d9f82d1c9e83cf312",
      hash: "e52b50cf4d5eff2b3be50a0a0a1212128e95af10b9812002f3f4f6e1aef92cd8",
      status: "C4-SIM",
      timestamp: "18:24:32"
    }
  ]);
  const [isAnchoring, setIsAnchoring] = useState(false);
  const [consensusLevel, setConsensusLevel] = useState<'C4' | 'C5'>('C4');

  // Tab 2: Agent Checkpoint
  const [checkpointStatus, setCheckpointStatus] = useState<'idle' | 'scanning' | 'verified' | 'tampered'>('idle');
  const [tamperMode, setTamperMode] = useState(false);

  // Tab 3: Influencers Budget Simulator
  const [budget, setBudget] = useState(50000);
  const [influencerType, setInfluencerType] = useState<'synthetic' | 'human_builder' | 'hype_grifter'>('synthetic');

  // Memory Commit Handler
  const handleCommit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!memoryInput.trim()) return;

    const lastLog = memoryLogs[memoryLogs.length - 1];
    const prevHash = lastLog ? lastLog.hash : "GENESIS";
    
    // Simulate sha256
    const randomHex = Math.random().toString(16).substring(2, 10);
    const hash = prevHash.substring(0, 16) + randomHex + "e52b504d5eff2b3be50a0a";
    
    const newLog: EventLog = {
      id: `ev_00${memoryLogs.length + 1}`,
      fact: memoryInput,
      prevHash,
      hash,
      status: consensusLevel === 'C5' ? 'C5-REAL' : 'C4-SIM',
      timestamp: new Date().toLocaleTimeString()
    };

    setMemoryLogs(prev => [...prev, newLog]);
    setMemoryInput('');
  };

  const handleAnchorToChain = () => {
    setIsAnchoring(true);
    setTimeout(() => {
      setIsAnchoring(false);
      setConsensusLevel('C5');
      // Upgrade all logs to C5-REAL
      setMemoryLogs(prev => prev.map(log => ({ ...log, status: 'C5-REAL' })));
    }, 1500);
  };

  // Checkpoint Verifier Handler
  const handleVerifyCheckpoint = () => {
    setCheckpointStatus('scanning');
    setTimeout(() => {
      if (tamperMode) {
        setCheckpointStatus('tampered');
      } else {
        setCheckpointStatus('verified');
      }
    }, 1800);
  };

  // Influencer calculations
  const getInfluencerMetrics = () => {
    switch (influencerType) {
      case 'synthetic':
        return {
          reach: budget * 8.5,
          engagement: "5.67%",
          costPerPost: "$34,000",
          risk: "Low (100% Brand Control)",
          desc: "AI avatars like Lil Miquela or Aitana Lopez. Maximum repeatability, high initial development fee, zero physical liabilities."
        };
      case 'human_builder':
        return {
          reach: budget * 4.2,
          engagement: "3.12%",
          costPerPost: "$15,000",
          risk: "Medium (Schedule constraints)",
          desc: "Real researchers and operators like Andrej Karpathy or Lex Fridman. High credibility, zero corporate alignment, limited scale."
        };
      case 'hype_grifter':
        return {
          reach: budget * 12.0,
          engagement: "1.05% (Heavy bot inflation)",
          costPerPost: "$5,000",
          risk: "High (Reputational failure, FTC violations)",
          desc: "Vendecursos claiming '$10k/mo with AI'. Fake followers, high immediate click rates, absolute zero long-term retention."
        };
    }
  };

  const metrics = getInfluencerMetrics();

  return (
    <div className="w-full bg-cortex-cards/40 border border-white/5 rounded-2xl overflow-hidden backdrop-blur-xl shadow-2xl flex flex-col lg:flex-row min-h-[620px]">
      
      {/* Sidebar Navigation */}
      <div className="w-full lg:w-80 border-r border-white/5 bg-black/40 p-6 flex flex-col gap-2">
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2.5 h-2.5 rounded-full bg-[#2b3be5] animate-pulse"></span>
            <span className="font-mono text-[10px] uppercase tracking-widest text-cortex-muted">CORTEX Substrate</span>
          </div>
          <h3 className="font-mono text-sm uppercase text-white font-bold tracking-wider">Audit Dashboard</h3>
        </div>

        <button
          onClick={() => setActiveTab('memoria')}
          className={`flex items-center gap-3 w-full p-3 rounded-lg font-mono text-xs uppercase tracking-wider text-left transition-all ${
            activeTab === 'memoria'
              ? 'bg-[#2b3be5] text-white shadow-[0_0_15px_rgba(43,59,229,0.3)]'
              : 'text-white/60 hover:text-white hover:bg-white/5'
          }`}
        >
          <Database className="w-4 h-4" />
          <span>I. Memoria</span>
          {consensusLevel === 'C5' && (
            <span className="ml-auto text-[8px] bg-cortex-success/20 text-cortex-success px-1.5 py-0.5 rounded font-bold">C5</span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('agentes')}
          className={`flex items-center gap-3 w-full p-3 rounded-lg font-mono text-xs uppercase tracking-wider text-left transition-all ${
            activeTab === 'agentes'
              ? 'bg-[#2b3be5] text-white shadow-[0_0_15px_rgba(43,59,229,0.3)]'
              : 'text-white/60 hover:text-white hover:bg-white/5'
          }`}
        >
          <Shield className="w-4 h-4" />
          <span>II. Agentes</span>
        </button>

        <button
          onClick={() => setActiveTab('influencers')}
          className={`flex items-center gap-3 w-full p-3 rounded-lg font-mono text-xs uppercase tracking-wider text-left transition-all ${
            activeTab === 'influencers'
              ? 'bg-[#2b3be5] text-white shadow-[0_0_15px_rgba(43,59,229,0.3)]'
              : 'text-white/60 hover:text-white hover:bg-white/5'
          }`}
        >
          <Users className="w-4 h-4" />
          <span>III. Influencers IA</span>
        </button>

        <div className="mt-auto pt-6 border-t border-white/5">
          <div className="p-4 bg-cortex-bg/60 border border-white/5 rounded-lg font-mono text-[10px] text-cortex-muted">
            <span className="text-white block mb-1">REALITY LEVEL:</span>
            {consensusLevel === 'C5' ? (
              <span className="text-cortex-success font-bold">C5-REAL (ON-CHAIN CHECKPOINTED)</span>
            ) : (
              <span className="text-cortex-warning font-bold">C4-SIM (LOCAL ONLY)</span>
            )}
            <p className="mt-2 text-[9px] opacity-80 leading-normal">
              C5 verification guarantees mathematical non-repudiation via public consensus anchors.
            </p>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 p-6 md:p-8 flex flex-col">
        
        {/* TAB 1: MEMORY */}
        {activeTab === 'memoria' && (
          <div className="flex flex-col h-full">
            <div className="mb-6">
              <span className="text-xs font-mono uppercase tracking-wider text-[#4d5eff]">Decoupled Cryptographic Memory</span>
              <h2 className="text-2xl md:text-3xl font-black text-white mt-1 uppercase tracking-tight">
                El Registro de la Verdad
              </h2>
              <p className="text-xs text-cortex-muted mt-2 max-w-xl leading-relaxed">
                Prueba exactamente qué sabía tu agente autónomo y cuándo. Todo evento de memoria es firmado y estructurado en un hash-chain inmutable.
              </p>
            </div>

            {/* Simulated Logs */}
            <div className="flex-1 bg-black/60 border border-white/5 rounded-xl p-4 font-mono text-[11px] mb-6 overflow-y-auto max-h-[220px]">
              <div className="text-cortex-muted mb-2 border-b border-white/5 pb-2 uppercase tracking-wider text-[9px] flex justify-between">
                <span>EVENT TRANSACTION LEDGER</span>
                <span>STATUS</span>
              </div>
              
              {memoryLogs.map((log) => (
                <div key={log.id} className="mb-3 hover:bg-white/5 p-2 rounded transition-colors border-l-2 border-cortex-accent">
                  <div className="flex justify-between text-white/95 mb-1 font-semibold">
                    <span>{log.id} · {log.fact}</span>
                    <span className={log.status === 'C5-REAL' ? 'text-cortex-success' : 'text-cortex-warning'}>
                      [{log.status}]
                    </span>
                  </div>
                  <div className="text-[10px] text-cortex-muted truncate">
                    prev: {log.prevHash}
                  </div>
                  <div className="text-[10px] text-[#4d5eff] truncate">
                    hash: {log.hash}
                  </div>
                </div>
              ))}
            </div>

            {/* Input Form & Anchor Button */}
            <div className="flex flex-col md:flex-row gap-4 items-end mt-auto">
              <form onSubmit={handleCommit} className="flex-1 flex gap-2 w-full">
                <input
                  type="text"
                  value={memoryInput}
                  onChange={(e) => setMemoryInput(e.target.value)}
                  placeholder="Insert a memory fact (e.g., 'Completed invoice 302 approval')"
                  className="flex-1 bg-cortex-bg border border-white/10 rounded-lg px-4 py-2 text-xs font-mono text-white focus:outline-none focus:border-[#2b3be5] focus:ring-1 focus:ring-[#2b3be5]"
                />
                <button
                  type="submit"
                  className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-xs font-mono uppercase tracking-wider text-white transition-all"
                >
                  Commit Log
                </button>
              </form>

              {consensusLevel === 'C4' && (
                <button
                  onClick={handleAnchorToChain}
                  disabled={isAnchoring}
                  className="w-full md:w-auto px-5 py-2.5 bg-gradient-to-r from-[#2b3be5] to-[#4d5eff] hover:shadow-[0_0_20px_rgba(43,59,229,0.5)] rounded-lg text-xs font-mono uppercase tracking-wider text-white font-bold transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                >
                  {isAnchoring ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Anchoring to L2...</span>
                    </>
                  ) : (
                    <>
                      <Cpu className="w-4 h-4 animate-pulse" />
                      <span>Elevate to C5-REAL</span>
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        )}

        {/* TAB 2: AGENTS */}
        {activeTab === 'agentes' && (
          <div className="flex flex-col h-full">
            <div className="mb-6">
              <span className="text-xs font-mono uppercase tracking-wider text-[#4d5eff]">Post-Quantum Integrity & Enclaves</span>
              <h2 className="text-2xl md:text-3xl font-black text-white mt-1 uppercase tracking-tight">
                Auditoría Autónoma de Agentes
              </h2>
              <p className="text-xs text-cortex-muted mt-2 max-w-xl leading-relaxed">
                El control de accesos e integridad ya no depende de firmas débiles. CORTEX implementa firmas cuánticas <strong className="text-white">ML-DSA-44</strong> y ejecuciones en enclaves seguros de hardware.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              {/* Verification Panel */}
              <div className="bg-black/45 border border-white/5 rounded-xl p-5 flex flex-col justify-between">
                <div>
                  <h4 className="font-mono text-xs uppercase text-white font-semibold mb-2">PQC Checkpoint Verifier</h4>
                  <p className="text-[11px] text-cortex-muted leading-relaxed mb-4">
                    Comprueba los checkpoints del agente firmados con algoritmo criptográfico post-cuántico ML-DSA.
                  </p>

                  <div className="flex items-center gap-3 mb-4">
                    <label className="flex items-center gap-2 font-mono text-[10px] text-white/80 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={tamperMode}
                        onChange={(e) => setTamperMode(e.target.checked)}
                        className="rounded border-white/20 bg-cortex-bg text-[#2b3be5] focus:ring-0"
                      />
                      <span className="text-cortex-warning font-mono">[SIMULATE MALICIOUS TAMPER]</span>
                    </label>
                  </div>
                </div>

                <button
                  onClick={handleVerifyCheckpoint}
                  className="w-full py-2.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-xs font-mono uppercase tracking-widest text-white transition-all font-semibold"
                >
                  Verify Post-Quantum Checkpoints
                </button>
              </div>

              {/* Status Display Panel */}
              <div className="bg-black/60 border border-white/5 rounded-xl p-5 flex flex-col justify-center items-center text-center min-h-[160px]">
                {checkpointStatus === 'idle' && (
                  <>
                    <Key className="w-10 h-10 text-cortex-muted opacity-40 mb-3" />
                    <span className="font-mono text-xs text-cortex-muted uppercase">Waiting for trigger...</span>
                  </>
                )}

                {checkpointStatus === 'scanning' && (
                  <>
                    <div className="w-8 h-8 border-3 border-[#2b3be5] border-t-transparent rounded-full animate-spin mb-3"></div>
                    <span className="font-mono text-xs text-white uppercase tracking-wider">Parsing state transitions & ML-DSA signatures...</span>
                  </>
                )}

                {checkpointStatus === 'verified' && (
                  <>
                    <CheckCircle className="w-10 h-10 text-cortex-success mb-3 animate-bounce" />
                    <span className="font-mono text-xs text-cortex-success uppercase font-bold tracking-widest">Verification Pass</span>
                    <p className="text-[10px] text-cortex-muted font-mono mt-2 max-w-xs">
                      All checkpoints match ML-DSA key root. Integrity index: 1.0 (100% secured).
                    </p>
                  </>
                )}

                {checkpointStatus === 'tampered' && (
                  <>
                    <AlertTriangle className="w-10 h-10 text-cortex-warning mb-3 animate-pulse" />
                    <span className="font-mono text-xs text-cortex-warning uppercase font-bold tracking-widest">Tamper Alert!</span>
                    <p className="text-[10px] text-cortex-warning/80 font-mono mt-2 max-w-xs">
                      ERROR: Checkpoint 4 root hash mismatch! Signatures do not match ledger history.
                    </p>
                  </>
                )}
              </div>
            </div>

            <div className="mt-auto">
              <div className="flex gap-4 items-center bg-cortex-accent/5 border border-[#2b3be5]/20 p-4 rounded-xl">
                <Cpu className="w-8 h-8 text-[#4d5eff] flex-shrink-0" />
                <div className="font-mono text-[10px] text-white/80 leading-normal">
                  <strong className="text-white">Hardware Enclave Isolation (C5-REAL Target):</strong> CORTEX interfaces with host TPM & AMD SEV to ensure agent private key signatures cannot be forged or extracted by standard root operators.
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: INFLUENCERS */}
        {activeTab === 'influencers' && (
          <div className="flex flex-col h-full">
            <div className="mb-6">
              <span className="text-xs font-mono uppercase tracking-wider text-[#4d5eff]">Synthetics vs. Real Signal</span>
              <h2 className="text-2xl md:text-3xl font-black text-white mt-1 uppercase tracking-tight">
                La Economía de la Mentira
              </h2>
              <p className="text-xs text-cortex-muted mt-2 max-w-xl leading-relaxed">
                Analizamos métricas brutas de rentabilidad y fraude. La IA virtual factura millones con engagement inflado frente al rigor de los verdaderos desarrolladores.
              </p>
            </div>

            {/* Simulator Controls */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6 flex-1">
              <div className="col-span-1 bg-black/45 border border-white/5 rounded-xl p-5 flex flex-col justify-between">
                <div>
                  <h4 className="font-mono text-xs uppercase text-white font-semibold mb-4">Auditor Controls</h4>
                  
                  <div className="mb-6">
                    <label className="block font-mono text-[10px] text-cortex-muted uppercase mb-2">
                      Campaign Budget: ${budget.toLocaleString()}
                    </label>
                    <input
                      type="range"
                      min="10000"
                      max="200000"
                      step="5000"
                      value={budget}
                      onChange={(e) => setBudget(Number(e.target.value))}
                      className="w-full accent-[#2b3be5] bg-white/10 h-1 rounded"
                    />
                  </div>

                  <div className="flex flex-col gap-2">
                    <label className="font-mono text-[10px] text-cortex-muted uppercase mb-1">Creator Class</label>
                    {[
                      { id: 'synthetic', label: 'Synthetic Avatar (Miquela / Aitana)' },
                      { id: 'human_builder', label: 'Human Builder (Karpathy / Lex)' },
                      { id: 'hype_grifter', label: 'Hype Grifter (Vendecursos)' }
                    ].map((type) => (
                      <button
                        key={type.id}
                        onClick={() => setInfluencerType(type.id as any)}
                        className={`w-full py-2 px-3 rounded text-[11px] font-mono text-left transition-all ${
                          influencerType === type.id
                            ? 'bg-[#2b3be5]/25 border border-[#2b3be5] text-white'
                            : 'bg-white/5 border border-transparent text-white/60 hover:text-white'
                        }`}
                      >
                        {type.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Simulation Result */}
              <div className="col-span-2 bg-black/60 border border-white/5 rounded-xl p-6 flex flex-col justify-between">
                <div>
                  <div className="flex justify-between items-start mb-4">
                    <span className="font-mono text-xs uppercase text-cortex-accent">Simulation Report</span>
                    <span className={`font-mono text-[9px] uppercase px-2 py-0.5 rounded font-bold ${
                      metrics.risk.includes('Low') 
                        ? 'bg-cortex-success/20 text-cortex-success' 
                        : metrics.risk.includes('Medium')
                          ? 'bg-yellow-500/20 text-yellow-500'
                          : 'bg-cortex-warning/20 text-cortex-warning'
                    }`}>
                      {metrics.risk}
                    </span>
                  </div>

                  <p className="text-xs text-white/95 leading-relaxed mb-6 font-mono border-l-2 border-white/20 pl-4 py-1">
                    {metrics.desc}
                  </p>

                  <div className="grid grid-cols-3 gap-4 font-mono">
                    <div className="bg-white/5 p-3 rounded-lg border border-white/5">
                      <span className="block text-[9px] text-cortex-muted uppercase">Projected Reach</span>
                      <strong className="text-sm text-white">{Math.round(metrics.reach).toLocaleString()} views</strong>
                    </div>
                    <div className="bg-white/5 p-3 rounded-lg border border-white/5">
                      <span className="block text-[9px] text-cortex-muted uppercase">Avg Engagement</span>
                      <strong className="text-sm text-white">{metrics.engagement}</strong>
                    </div>
                    <div className="bg-white/5 p-3 rounded-lg border border-white/5">
                      <span className="block text-[9px] text-cortex-muted uppercase">Avg Cost / Post</span>
                      <strong className="text-sm text-white">{metrics.costPerPost}</strong>
                    </div>
                  </div>
                </div>

                <div className="mt-6 border-t border-white/5 pt-4 text-[10px] font-mono text-cortex-muted flex items-center justify-between">
                  <span>Audit Source: Sumsub & HypeAuditor 2026</span>
                  <a href="/influencers" className="text-[#4d5eff] hover:underline flex items-center gap-1">
                    Read Tesis Essay <ArrowRight className="w-3 h-3" />
                  </a>
                </div>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
