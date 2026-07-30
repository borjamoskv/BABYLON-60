import React, { Suspense, lazy } from 'react';

const ThermodynamicVectorSpaceClient = lazy(() => import('./webgl/ThermodynamicVectorSpaceClient'));

const Loading = () => (
  <div
    style={{
      width: '100%', height: '500px', background: '#030303', border: '1px solid rgba(255,255,255,0.04)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'monospace',
      fontSize: '10px', color: '#222', letterSpacing: '0.2em',
    }}
  >
    THERMODYNAMIC VECTOR SPACE // INITIALIZING
  </div>
);

export default function ThermodynamicVectorSpace() {
  return (
    <Suspense fallback={<Loading />}>
      <ThermodynamicVectorSpaceClient />
    </Suspense>
  );
}
