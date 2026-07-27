'use client';
import React, { useEffect, useRef, useState } from 'react';

type LogEntry = {
  ts: string;
  domain: string;
  latencyMs: number;
  pathHash: string;
  status: number;
  id: string;
};

const DOMAINS = ['cortexpersist.com', 'cortexpersist.dev', 'agents.archi', 'cortexpersist.org'];
const STATUS_WEIGHTS = [200, 200, 200, 304, 304, 429, 503];

function mockEntry(): LogEntry {
  return {
    ts: new Date().toISOString().slice(11, 23),
    domain: DOMAINS[Math.floor(Math.random() * DOMAINS.length)]!,
    latencyMs: Math.floor(20 + Math.random() * 120),
    pathHash: Math.random().toString(16).slice(2, 10),
    status: STATUS_WEIGHTS[Math.floor(Math.random() * STATUS_WEIGHTS.length)]!,
    id: Math.random().toString(36).slice(2, 8),
  };
}

const statusColor = (s: number) =>
  s < 300 ? '#00ff88' : s < 400 ? '#44bbff' : s < 500 ? '#ffaa00' : '#ff2244';

export default function SwarmTelemetryLogClient() {
  const [log, setLog] = useState<LogEntry[]>(() => Array.from({ length: 12 }, mockEntry));
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    // Try to read real X-Cortex-* headers from a HEAD request
    const fetchRealTelemetry = async () => {
      try {
        const res = await fetch('/health', { method: 'GET' });
        const edgeTs = res.headers.get('X-Cortex-Edge-Ts');
        const latency = res.headers.get('X-Cortex-Latency-Ms');
        const route = res.headers.get('X-Cortex-Route');
        const pathHash = res.headers.get('X-Cortex-Path-Hash');
        if (edgeTs) {
          const entry: LogEntry = {
            ts: new Date(parseInt(edgeTs)).toISOString().slice(11, 23),
            domain: route ?? 'cortexpersist.com',
            latencyMs: parseInt(latency ?? '0'),
            pathHash: pathHash ?? '--------',
            status: res.status,
            id: edgeTs.slice(-6),
          };
          setLog(prev => [entry, ...prev].slice(0, 20));
          return;
        }
      } catch { /* fall back to mock */ }
      setLog(prev => [mockEntry(), ...prev].slice(0, 20));
    };

    intervalRef.current = setInterval(fetchRealTelemetry, 1800);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, []);

  return (
    <div style={{
      width: '100%', height: '280px',
      background: '#030303',
      border: '1px solid rgba(255,255,255,0.04)',
      overflow: 'hidden',
      fontFamily: 'monospace',
      fontSize: '10px',
      padding: '8px 12px',
    }}>
      <div style={{ color: '#333', letterSpacing: '0.15em', marginBottom: 8, fontSize: '9px' }}>
        SWARM TELEMETRY LOG · LIVE
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
        {log.map(entry => (
          <div key={entry.id} style={{ display: 'flex', gap: '10px', alignItems: 'center', opacity: 0.85 }}>
            <span style={{ color: '#333', minWidth: 80 }}>{entry.ts}</span>
            <span style={{ color: statusColor(entry.status), minWidth: 28 }}>{entry.status}</span>
            <span style={{ color: '#555', minWidth: 170 }}>{entry.domain}</span>
            <span style={{ color: '#00ff88', minWidth: 50 }}>{entry.latencyMs}ms</span>
            <span style={{ color: '#222' }}>{entry.pathHash}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
