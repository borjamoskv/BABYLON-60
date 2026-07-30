'use client';
import React, { useCallback, useRef, useState } from 'react';
import { CortexClient } from '@cortex/sdk';

type CollisionResult = {
  id: string;
  hash: string;
  anchored: boolean;
  ts: string;
};

export default function ManualCollisionInjectorClient() {
  const [payload, setPayload] = useState('');
  const [results, setResults] = useState<CollisionResult[]>([]);
  const [loading, setLoading] = useState(false);
  const clientRef = useRef<CortexClient | null>(null);

  const getClient = useCallback(() => {
    if (!clientRef.current) {
      clientRef.current = new CortexClient({
        apiKey: import.meta.env.PUBLIC_CORTEX_DEMO_KEY ?? 'demo',
        apiUrl: '/api/cortex-proxy', // proxied to avoid exposing key
      });
    }
    return clientRef.current;
  }, []);

  const inject = useCallback(async () => {
    if (!payload.trim()) return;
    setLoading(true);
    try {
      const client = getClient();
      const result = await client.event({
        type: 'manual.collision',
        payload: { raw: payload, injectedAt: Date.now() },
      });
      setResults(prev => [{
        ...result,
        ts: new Date().toISOString().slice(11, 23),
      }, ...prev].slice(0, 10));
      setPayload('');
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'unknown error';
      setResults(prev => [{
        id: 'ERROR',
        hash: msg.slice(0, 32),
        anchored: false,
        ts: new Date().toISOString().slice(11, 23),
      }, ...prev].slice(0, 10));
    } finally {
      setLoading(false);
    }
  }, [payload, getClient]);

  return (
    <div style={{
      background: '#030303',
      border: '1px solid rgba(255,255,255,0.06)',
      padding: '16px',
      fontFamily: 'monospace',
      fontSize: '11px',
    }}>
      <div style={{ color: '#444', letterSpacing: '0.15em', marginBottom: 12, fontSize: '9px' }}>
        MANUAL COLLISION INJECTOR · CORTEX LEDGER
      </div>
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <input
          value={payload}
          onChange={e => setPayload(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && inject()}
          placeholder="payload // raw string"
          disabled={loading}
          style={{
            flex: 1, background: 'rgba(255,255,255,0.03)',
            border: '1px solid rgba(255,255,255,0.08)',
            color: '#aaa', padding: '6px 10px', fontFamily: 'monospace',
            fontSize: '11px', outline: 'none',
            opacity: loading ? 0.5 : 1,
          }}
        />
        <button
          onClick={inject}
          disabled={loading || !payload.trim()}
          style={{
            background: loading ? 'rgba(0,255,136,0.05)' : 'rgba(0,255,136,0.1)',
            border: '1px solid rgba(0,255,136,0.2)',
            color: '#00ff88', padding: '6px 14px',
            fontFamily: 'monospace', fontSize: '11px',
            cursor: loading ? 'wait' : 'pointer',
            letterSpacing: '0.1em',
          }}
        >
          {loading ? 'ANCHORING...' : 'INJECT'}
        </button>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {results.map((r, i) => (
          <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <span style={{ color: '#333' }}>{r.ts}</span>
            <span style={{ color: r.anchored ? '#00ff88' : '#ff2244', fontSize: '9px' }}>
              {r.anchored ? '✓ ANCHORED' : '× FAILED'}
            </span>
            <span style={{ color: '#555' }}>{r.id}</span>
            <span style={{ color: '#333', fontSize: '9px' }}>{r.hash.slice(0, 16)}…</span>
          </div>
        ))}
      </div>
    </div>
  );
}
