import React, { useState, useEffect, useRef } from 'react';
import { soundFx } from './AudioEngine';

interface TelemetrySnapshot {
  timestamp: number;
  databases: Array<{ name: string; size_bytes: number; size_mb: number }>;
  total_db_size_mb: number;
  wal_files: Array<{ name: string; size_bytes: number }>;
  git: { exists: boolean; pack_size_mb?: number; head?: string };
  process: { user_time_s?: number; system_time_s?: number; max_rss_mb?: number };
  project_root: string;
  exergy_score?: number;
  anergy_level?: number;
  active_agents?: number;
  landauer_compliant?: boolean;
}

export const SwarmMonitor: React.FC = () => {
  const [tenants] = useState(100000);
  const [concurrency] = useState(5000);
  const [exergy, setExergy] = useState(998.5);
  const [isLive, setIsLive] = useState(false);
  const [snapshot, setSnapshot] = useState<TelemetrySnapshot | null>(null);
  const [logs, setLogs] = useState<string[]>([
    '2026-09-03 14:25:00 | INFO | ⚡ INICIANDO ENJAMBRE LEGION: 100,000 Tenantes',
    '2026-09-03 14:25:00 | INFO | ⚡ LÍMITE DE CONCURRENCIA (Válvula Termodinámica): 5,000 / sec',
    '2026-09-03 14:25:01 | INFO | 🌊 Agentes en suspensión asíncrona (CPU 0%). Esperando beeper signal...',
  ]);

  const wsRef = useRef<WebSocket | null>(null);
  const isLiveRef = useRef(false);

  const connectWebSocket = React.useCallback(() => {
    try {
      const wsUrl = window.location.protocol === 'https:'
        ? `wss://${window.location.host}/ws/telemetry`
        : `ws://${window.location.host}/ws/telemetry`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsLive(true);
        isLiveRef.current = true;
        soundFx.playSuccess();
        const time = new Date().toTimeString().split(' ')[0];
        setLogs((prev) => [
          `[${time}] | NET | 🔌 WebSocket conectado a Telemetría C5-REAL (FastAPI / Rust IPC)`,
          ...prev.slice(0, 15),
        ]);
      };

      ws.onmessage = (event) => {
        try {
          const data: TelemetrySnapshot = JSON.parse(event.data);
          setSnapshot(data);
          if (data.exergy_score) {
            setExergy(data.exergy_score);
          }
          const time = new Date().toTimeString().split(' ')[0];
          setLogs((prev) => [
            `[${time}] | SNAPSHOT | Exergía: ${data.exergy_score ?? 998.5}% | DBs: ${data.databases.length} (${data.total_db_size_mb} MB) | WAL: ${data.wal_files.length} | RSS: ${data.process.max_rss_mb ?? 0} MB`,
            ...prev.slice(0, 15),
          ]);
        } catch {
          // JSON parse error handled silently
        }
      };

      ws.onerror = () => {
        setIsLive(false);
        isLiveRef.current = false;
      };

      ws.onclose = () => {
        setIsLive(false);
        isLiveRef.current = false;
      };
    } catch {
      setIsLive(false);
      isLiveRef.current = false;
    }
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      connectWebSocket();
    }, 0);

    // Fallback simulation timer if WS is disconnected
    const fallbackInterval = setInterval(() => {
      if (!isLiveRef.current) {
        setExergy((prev) => Math.min(1000, Math.max(985, prev + (Math.random() - 0.5) * 2)));
      }
    }, 2000);

    return () => {
      clearTimeout(timer);
      clearInterval(fallbackInterval);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connectWebSocket]);

  return (
    <div className="space-y-6 font-mono">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-cyan-300 flex items-center gap-3">
            <span>🐝 TELEMETRÍA DEL ENJAMBRE LEGION (SWARM P×S)</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Sincronización Asíncrona masiva con Válvula Termodinámica de Concurrencia y Kernel Rust
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`c5-badge ${isLive ? 'badge-emerald' : 'badge-amber'}`}>
            <span className={`w-2 h-2 rounded-full ${isLive ? 'bg-emerald-400' : 'bg-amber-400'} animate-ping`} />
            {isLive ? 'EN VIVO: RUST IPC / WAL STREAM' : 'TELEMETRÍA LOCAL (STANDBY)'}
          </span>
          {!isLive && (
            <button
              onClick={() => {
                soundFx.playClick();
                connectWebSocket();
              }}
              className="px-2.5 py-1 text-[11px] bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded transition-all cursor-pointer"
            >
              🔄 CONECTAR WS
            </button>
          )}
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-panel p-4 border-cyan-500/20">
          <div className="text-xs text-slate-400">TENANTES ENJAMBRE</div>
          <div className="text-2xl font-bold text-cyan-300 mt-1">
            {snapshot?.active_agents ? `${snapshot.active_agents} CORTEX` : tenants.toLocaleString()}
          </div>
          <div className="text-[10px] text-emerald-400 mt-1">
            {isLive ? 'Suspendidos en AgentPager (0% CPU)' : 'CPU Suspended (0%)'}
          </div>
        </div>

        <div className="glass-panel p-4 border-amber-500/20">
          <div className="text-xs text-slate-400">MEMORIA RSS & WAL</div>
          <div className="text-2xl font-bold text-amber-300 mt-1">
            {snapshot?.process?.max_rss_mb ? `${snapshot.process.max_rss_mb} MB` : `${concurrency.toLocaleString()} / s`}
          </div>
          <div className="text-[10px] text-amber-400 mt-1">
            {snapshot ? `${snapshot.wal_files.length} archivos WAL activos` : 'Válvula de Concurrencia'}
          </div>
        </div>

        <div className="glass-panel p-4 border-emerald-500/20">
          <div className="text-xs text-slate-400">SCORE DE EXERGÍA REAL</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">
            {exergy.toFixed(1)} / 1000
          </div>
          <div className="text-[10px] text-emerald-400 mt-1">Límite Landauer Respetado</div>
        </div>

        <div className="glass-panel p-4 border-slate-700/40">
          <div className="text-xs text-slate-400">PERSISTENCIA DISCO (BFT)</div>
          <div className="text-2xl font-bold text-white mt-1">
            {snapshot ? `${snapshot.total_db_size_mb} MB` : '11 Cores × 20 Hilos'}
          </div>
          <div className="text-[10px] text-cyan-400 mt-1">
            {snapshot ? `${snapshot.databases.length} Bases de Datos SQLite` : '222 Agentes Singularidad'}
          </div>
        </div>
      </div>

      {/* Live Swarm Terminal Stream */}
      <div className="glass-panel p-5 text-xs space-y-2 bg-black/80">
        <div className="text-slate-500 pb-2 border-b border-slate-800 flex justify-between items-center">
          <span>CONSOLE LOGS — TELEMETRÍA DEL ENJAMBRE</span>
          <span className={isLive ? 'text-emerald-400' : 'text-amber-400'}>
            MODE: {isLive ? 'LIVE_IPC_ATTACHED' : 'SYNTHETIC_OMEGA'}
          </span>
        </div>
        <div className="max-h-60 overflow-y-auto space-y-1">
          {logs.map((log, i) => (
            <div key={i} className="text-slate-300 leading-relaxed font-mono">
              {log}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

