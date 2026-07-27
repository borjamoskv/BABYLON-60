import React, { Suspense, lazy } from 'react';

const SwarmTelemetryLogClient = lazy(() => import('./webgl/SwarmTelemetryLogClient'));

const Loading = () => (
  <div style={{
    width: '100%', height: '280px', background: '#030303', border: '1px solid rgba(255,255,255,0.04)',
    fontFamily: 'monospace', fontSize: '10px', color: '#1a1a1a', padding: '12px', overflow: 'hidden',
  }}>
    {Array.from({ length: 8 }).map((_, i) => (
      <div key={i} style={{ marginBottom: 6, height: 12, background: 'rgba(255,255,255,0.03)', borderRadius: 2 }} />
    ))}
  </div>
);

export default function SwarmTelemetryLog() {
  return (
    <Suspense fallback={<Loading />}>
      <SwarmTelemetryLogClient />
    </Suspense>
  );
}
