import React, { Suspense, lazy } from 'react';

const ManualCollisionInjectorClient = lazy(() => import('./webgl/ManualCollisionInjectorClient'));

export default function ManualCollisionInjector() {
  return (
    <Suspense fallback={<div style={{ minHeight: '100px', background: '#030303', fontFamily: 'monospace', fontSize: '10px', color: '#333', padding: '12px' }}>LOADING COLLISION INJECTOR...</div>}>
      <ManualCollisionInjectorClient />
    </Suspense>
  );
}
