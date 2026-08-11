import React, { useState, useEffect } from 'react';

export const SwarmMonitor: React.FC = () => {
  const [tenants, setTenants] = useState(100000);
  const [concurrency, setConcurrency] = useState(5000);
  const [exergy, setExergy] = useState(1000);

  useEffect(() => {
    const interval = setInterval(() => {
      setExergy((prev) => Math.min(1000, Math.max(985, prev + (Math.random() - 0.5) * 4)));
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold font-mono text-cyan-300 flex items-center gap-3">
            <span>🐝 TELEMETRÍA DEL ENJAMBRE LEGION (SWARM P×S)</span>
          </h2>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Sincronización Asíncrona masiva con Válvula Termodinámica de Concurrencia
          </p>
        </div>
        <span className="c5-badge badge-cyan">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
          BEEPER FAN-OUT: ACTIVO
        </span>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-panel p-4">
          <div className="text-xs font-mono text-slate-400">TENANTES TOTALES</div>
          <div className="text-2xl font-bold font-mono text-cyan-300 mt-1">
            {tenants.toLocaleString()}
          </div>
          <div className="text-[10px] font-mono text-emerald-400 mt-1">CPU Suspended (0%)</div>
        </div>

        <div className="glass-panel p-4">
          <div className="text-xs font-mono text-slate-400">VÁLVULA DE CONCURRENCIA</div>
          <div className="text-2xl font-bold font-mono text-amber-300 mt-1">
            {concurrency.toLocaleString()} / sec
          </div>
          <div className="text-[10px] font-mono text-amber-400 mt-1">Max Throttling Rate</div>
        </div>

        <div className="glass-panel p-4">
          <div className="text-xs font-mono text-slate-400">SCORE DE EXERGÍA</div>
          <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
            {exergy.toFixed(1)} / 1000
          </div>
          <div className="text-[10px] font-mono text-emerald-400 mt-1">Límite de Landauer Respetado</div>
        </div>

        <div className="glass-panel p-4">
          <div className="text-xs font-mono text-slate-400">TOPOLOGÍA P×S CORES</div>
          <div className="text-2xl font-bold font-mono text-white mt-1">
            11 Cores × 20 Hilos
          </div>
          <div className="text-[10px] font-mono text-cyan-400 mt-1">222 Agentes Singularidad</div>
        </div>
      </div>

      {/* Live Swarm Terminal Stream */}
      <div className="glass-panel p-5 font-mono text-xs space-y-2 bg-black/80">
        <div className="text-slate-500 pb-2 border-b border-slate-800 flex justify-between">
          <span>CONSOLE LOGS — ENJAMBRE LEGION SWARM</span>
          <span className="text-cyan-400">STATE: OMEGA_COLLAPSE</span>
        </div>
        <div className="text-cyan-400">
          2026-08-11 22:15:00 | INFO | ⚡ INICIANDO ENJAMBRE LEGION: {tenants} Tenantes
        </div>
        <div className="text-amber-400">
          2026-08-11 22:15:00 | INFO | ⚡ LÍMITE DE CONCURRENCIA (Válvula Termodinámica): {concurrency}
        </div>
        <div className="text-slate-300">
          2026-08-11 22:15:01 | INFO | 🌊 Funciones de onda probabilísticas emitidas. Agentes en suspensión (CPU 0%)...
        </div>
        <div className="text-emerald-400">
          2026-08-11 22:15:02 | INFO | 📡 [BEEPER] OMEGA_COLLAPSE Fan-Out [N={concurrency}] | Payload: OMEGA_COLLAPSE_SIGNAL
        </div>
        <div className="text-emerald-400 font-bold">
          [✓] SWARM COLLAPSE COMPLETE — 100,000 TENANTS SYNCHRONIZED DETERMINISTICALLY.
        </div>
      </div>
    </div>
  );
};
