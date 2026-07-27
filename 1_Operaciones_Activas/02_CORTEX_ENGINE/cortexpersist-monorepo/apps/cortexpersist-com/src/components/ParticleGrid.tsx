'use client';
import React, { lazy, Suspense } from 'react';

const WebGLParticleGrid = lazy(() => import('./webgl/WebGLParticleGrid'));

export default function ParticleGrid({ count = 800 }: { count?: number }) {
  return (
    <div className="relative w-full h-[300px]">
      <Suspense
        fallback={
          <div
            style={{
              width: '100%', height: '100%',
              background: 'repeating-linear-gradient(0deg, rgba(255,255,255,0.01) 0px, transparent 1px, transparent 40px), repeating-linear-gradient(90deg, rgba(255,255,255,0.01) 0px, transparent 1px, transparent 40px)',
              animation: 'pulse 2s infinite',
            }}
          />
        }
      >
        <WebGLParticleGrid count={count} />
      </Suspense>
    </div>
  );
}
