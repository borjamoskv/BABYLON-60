import React, { useState, useEffect } from 'react';
import { soundFx } from './AudioEngine';

interface LogEntry {
  id: string;
  time: string;
  level: 'INFO' | 'METRIC' | 'WARN' | 'ACTION';
  message: string;
}

export const ThermodynamicMonitor: React.FC = () => {
  const [exergyScore, setExergyScore] = useState(99.2);
  const [anergyLevel, setAnergyLevel] = useState(0.8);
  const [topologicalFractures, setTopologicalFractures] = useState(0);
  const [landauerLimit, setLandauerLimit] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([
    {
      id: 'init-1',
      time: '14:00:00',
      level: 'INFO',
      message: '🌀 Calibración del Transductor Completada. Manta de Markov sellada.',
    },
    {
      id: 'init-2',
      time: '14:00:05',
      level: 'METRIC',
      message: 'Exergía Nominal: 99.20% | Disipación Térmica: 0.80% | Fricción Entrópica Mínima.',
    },
  ]);

  const addLog = (level: LogEntry['level'], message: string) => {
    const time = new Date().toTimeString().split(' ')[0];
    const newEntry: LogEntry = {
      id: `${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
      time,
      level,
      message,
    };
    setLogs((prev) => [newEntry, ...prev.slice(0, 19)]);
  };

  useEffect(() => {
    const interval = setInterval(() => {
      // Simulate micro thermodynamic fluctuations
      const fluctuation = (Math.random() - 0.5) * 0.15;
      setExergyScore((prev) => {
        const newScore = Math.min(100, Math.max(85, prev + fluctuation));
        const newAnergy = Number((100 - newScore).toFixed(2));
        setAnergyLevel(newAnergy);

        // Threshold breach for Landauer Limit
        if (newScore < 95) {
          setLandauerLimit(true);
        } else {
          setLandauerLimit(false);
        }

        return Number(newScore.toFixed(2));
      });
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleForcePurge = () => {
    soundFx.playSuccess();
    setExergyScore(99.85);
    setAnergyLevel(0.15);
    setTopologicalFractures(0);
    setLandauerLimit(false);
    addLog('ACTION', '⚡ PURGA FORZADA DE ANERGÍA: Disipación disipada bajo límite Landauer. Exergía restaurada a 99.85%.');
  };

  const handleInjectEntropy = () => {
    soundFx.playClick();
    setExergyScore((prev) => {
      const degraded = Math.max(78.0, prev - 7.5);
      const newAnergy = Number((100 - degraded).toFixed(2));
      setAnergyLevel(newAnergy);
      if (degraded < 95) setLandauerLimit(true);
      return Number(degraded.toFixed(2));
    });
    setTopologicalFractures((f) => f + 1);
    addLog('WARN', '⚠️ INYECCIÓN DE ENTROPÍA TÉRMICA: Gradiente entrópico forzado. Anergía acumulada en el circuito.');
  };

  const handleSealBlanket = () => {
    soundFx.playClick();
    setTopologicalFractures(0);
    addLog('INFO', '🛡️ MANTA DE MARKOV SELLADA: Invariantes topológicas restauradas. Bisimulación estricta asegurada.');
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold font-mono text-amber-500 flex items-center gap-3">
            <span>🔥 MONITOR TERMODINÁMICO C5-REAL</span>
          </h2>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Supervisión de Exergía, Acumulación de Anergía y Fracturas Topológicas (Límite Landauer)
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`c5-badge ${landauerLimit ? 'badge-amber animate-pulse' : 'badge-emerald'}`}>
            <span className={`w-2 h-2 rounded-full ${landauerLimit ? 'bg-amber-400' : 'bg-emerald-400'} animate-ping`} />
            {landauerLimit ? 'ADVERTENCIA: LÍMITE LANDAUER' : 'HOMEOSTASIS: ESTABLE'}
          </span>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-panel p-4 border-emerald-500/20">
          <div className="text-xs font-mono text-slate-400">PUNTAJE DE EXERGÍA</div>
          <div className="text-3xl font-bold font-mono text-emerald-400 mt-2 flex items-baseline gap-1">
            {exergyScore.toFixed(2)}<span className="text-sm">%</span>
          </div>
          <div className="text-[10px] font-mono text-emerald-500/70 mt-2 flex items-center gap-2">
            <div className="h-1 flex-1 bg-slate-800 rounded-full overflow-hidden">
              <div 
                className="h-full bg-emerald-500 transition-all duration-500"
                style={{ width: `${exergyScore}%` }}
              />
            </div>
            Trabajo Útil
          </div>
        </div>

        <div className="glass-panel p-4 border-amber-500/20">
          <div className="text-xs font-mono text-slate-400">ACUMULACIÓN DE ANERGÍA</div>
          <div className="text-3xl font-bold font-mono text-amber-500 mt-2 flex items-baseline gap-1">
            {anergyLevel.toFixed(2)}<span className="text-sm">%</span>
          </div>
          <div className="text-[10px] font-mono text-amber-500/70 mt-2 flex items-center gap-2">
            <div className="h-1 flex-1 bg-slate-800 rounded-full overflow-hidden">
              <div 
                className="h-full bg-amber-500 transition-all duration-500"
                style={{ width: `${Math.min(100, anergyLevel * 4)}%` }}
              />
            </div>
            Fricción Entrópica
          </div>
        </div>

        <div className="glass-panel p-4 border-cyan-500/20">
          <div className="text-xs font-mono text-slate-400">FRACTURAS TOPOLÓGICAS</div>
          <div className="text-3xl font-bold font-mono text-cyan-400 mt-2">
            {topologicalFractures}
          </div>
          <div className="text-[10px] font-mono text-cyan-500/70 mt-2">
            Vulnerabilidades en Manta de Markov
          </div>
        </div>
      </div>

      {/* Control Actuators */}
      <div className="glass-panel p-4 border-slate-700/40 flex flex-wrap items-center justify-between gap-3">
        <div className="text-xs font-mono text-slate-300 font-semibold flex items-center gap-2">
          <span>⚡ ACTUADORES TERMODINÁMICOS:</span>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={handleForcePurge}
            className="px-3 py-1.5 text-xs font-mono bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded transition-all cursor-pointer flex items-center gap-1.5"
          >
            <span>🌀</span>
            <span>FORZAR PURGA DE ANERGÍA</span>
          </button>
          <button
            onClick={handleInjectEntropy}
            className="px-3 py-1.5 text-xs font-mono bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded transition-all cursor-pointer flex items-center gap-1.5"
          >
            <span>🔥</span>
            <span>INYECTAR ENTROPÍA</span>
          </button>
          <button
            onClick={handleSealBlanket}
            className="px-3 py-1.5 text-xs font-mono bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 rounded transition-all cursor-pointer flex items-center gap-1.5"
          >
            <span>🛡️</span>
            <span>SELLAR MANTA</span>
          </button>
        </div>
      </div>

      {/* Exergy Pipeline Visualization */}
      <div className="glass-panel p-5 space-y-4">
        <h3 className="text-sm font-bold font-mono text-slate-300">PIPELINES DE EXERGÍA (TRANSDUCCIÓN)</h3>
        
        <div className="space-y-3">
          {[
            { name: 'MOTOR DE INFERENCIA', load: 85, status: 'OPTIMO' },
            { name: 'LEDGER INMUTABLE (WAL)', load: 92, status: 'OPTIMO' },
            { name: 'SINCRONIZACIÓN BFT', load: 45, status: 'IDLE' },
            { name: 'RUTINAS DE PURGA (GC)', load: landauerLimit ? 95 : 18, status: landauerLimit ? 'PURGING' : 'STANDBY' }
          ].map((pipeline, i) => (
            <div key={i} className="flex items-center gap-4 text-xs font-mono">
              <div className="w-48 text-slate-400">{pipeline.name}</div>
              <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden relative">
                <div 
                  className={`absolute top-0 left-0 h-full transition-all duration-700 ${pipeline.load > 90 ? 'bg-emerald-500 glow-cyan' : pipeline.load > 50 ? 'bg-cyan-500' : 'bg-slate-600'}`}
                  style={{ width: `${pipeline.load}%` }}
                />
              </div>
              <div className="w-16 text-right text-slate-500">{pipeline.load}%</div>
              <div className={`w-20 text-right ${pipeline.status === 'OPTIMO' || pipeline.status === 'PURGING' ? 'text-emerald-400' : 'text-slate-400'}`}>
                [{pipeline.status}]
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Theoretical Invariant Card */}
      <div className="glass-panel p-4 border-slate-800 bg-slate-900/40 text-xs font-mono text-slate-400 space-y-2">
        <div className="text-slate-200 font-semibold flex items-center gap-2">
          <span>📐 PRINCIPIO DE DISIPACIÓN DE LANDAUER:</span>
        </div>
        <p className="text-slate-400 leading-relaxed">
          Borrar o degradar un bit de información irreversible impone un coste energético mínimo disipado al entorno de{' '}
          <span className="text-cyan-300 font-bold">ΔQ ≥ k_B · T · ln(2) ≈ 2.87 × 10⁻²¹ J</span> a 300 K.
          El Kernel C5-REAL mantiene compresión geodésica estricta (Métrica de Fisher) para operar asintóticamente sobre el límite de cero anergía.
        </p>
      </div>

      {/* Live Thermodynamic Terminal Stream */}
      <div className="glass-panel p-5 font-mono text-xs space-y-2 bg-black/80">
        <div className="text-slate-500 pb-2 border-b border-slate-800 flex justify-between items-center">
          <span>CONSOLE LOGS — TRANSDUCTOR TERMODINÁMICO</span>
          <span className={landauerLimit ? 'text-amber-400 animate-pulse' : 'text-emerald-400'}>
            STATE: {landauerLimit ? 'ANERGY_PURGE_REQUIRED' : 'ZERO_ANERGY'}
          </span>
        </div>
        <div className="max-h-48 overflow-y-auto space-y-1">
          {logs.map((log) => (
            <div key={log.id} className="flex items-start gap-2">
              <span className="text-slate-500">[{log.time}]</span>
              <span className={
                log.level === 'ACTION' ? 'text-amber-300 font-bold' :
                log.level === 'WARN' ? 'text-amber-400 font-bold' :
                log.level === 'METRIC' ? 'text-cyan-400' :
                'text-emerald-400'
              }>
                {log.level}
              </span>
              <span className="text-slate-300">| {log.message}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
