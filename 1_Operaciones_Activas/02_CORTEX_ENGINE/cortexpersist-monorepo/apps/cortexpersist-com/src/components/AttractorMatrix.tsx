'use client';
import React, { lazy, Suspense } from 'react';

const WebGLAttractor = lazy(() => import('./webgl/WebGLAttractor'));

export default function AttractorMatrix() {
  return (
    <div className="attractor-matrix-container relative w-full h-[400px]">
      <Suspense
        fallback={
          <div className="animate-pulse bg-neutral-900 border border-white/5 w-full h-full rounded flex items-center justify-center">
            <span style={{ fontFamily: 'monospace', fontSize: '10px', color: '#333', letterSpacing: '0.2em' }}>
              ATTRACTOR MATRIX // LOADING
            </span>
          </div>
        }
      >
        <WebGLAttractor />
      </Suspense>
    </div>
  );
}
