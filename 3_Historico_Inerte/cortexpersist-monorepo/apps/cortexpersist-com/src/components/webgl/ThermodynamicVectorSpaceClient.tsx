'use client';
import React, { useEffect, useRef } from 'react';

type Vector = { x: number; y: number; vx: number; vy: number; temp: number; id: number };

const VECTOR_COUNT = 120;
const INTERACTION_RADIUS = 80;
const DAMPING = 0.995;
const THERMAL_NOISE = 0.08;

function kelvinToHue(temp: number): number {
  // Map 0-1 temp to 240 (cold/blue) -> 0 (hot/red)
  return 240 - temp * 240;
}

export default function ThermodynamicVectorSpaceClient() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resize = () => { canvas.width = canvas.offsetWidth; canvas.height = canvas.offsetHeight; };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    const vectors: Vector[] = Array.from({ length: VECTOR_COUNT }, (_, id) => ({
      x: Math.random() * (canvas.width || 800),
      y: Math.random() * (canvas.height || 500),
      vx: (Math.random() - 0.5) * 1.5,
      vy: (Math.random() - 0.5) * 1.5,
      temp: Math.random(),
      id,
    }));

    const draw = () => {
      const { width, height } = canvas;
      ctx.fillStyle = 'rgba(3,3,3,0.12)';
      ctx.fillRect(0, 0, width, height);

      // Update positions + thermodynamic interaction
      vectors.forEach(v => {
        // Thermal noise (Langevin)
        v.vx += (Math.random() - 0.5) * THERMAL_NOISE * v.temp;
        v.vy += (Math.random() - 0.5) * THERMAL_NOISE * v.temp;
        v.vx *= DAMPING;
        v.vy *= DAMPING;
        v.x += v.vx;
        v.y += v.vy;

        // Boundary reflection
        if (v.x < 0 || v.x > width) { v.vx *= -1; v.x = Math.max(0, Math.min(width, v.x)); }
        if (v.y < 0 || v.y > height) { v.vy *= -1; v.y = Math.max(0, Math.min(height, v.y)); }
      });

      // Draw interaction edges (entropy visualization)
      vectors.forEach((a, i) => {
        for (let j = i + 1; j < vectors.length; j++) {
          const b = vectors[j]!;
          const dx = b.x - a.x;
          const dy = b.y - a.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < INTERACTION_RADIUS) {
            const alpha = (1 - dist / INTERACTION_RADIUS) * 0.15;
            const avgTemp = (a.temp + b.temp) / 2;
            const hue = kelvinToHue(avgTemp);
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.strokeStyle = `hsla(${hue}, 70%, 55%, ${alpha})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();

            // Heat exchange (2nd law asymmetry — Ω₂)
            const dTemp = (b.temp - a.temp) * 0.001;
            a.temp += dTemp;
            b.temp -= dTemp;
            a.temp = Math.max(0, Math.min(1, a.temp));
            b.temp = Math.max(0, Math.min(1, b.temp));
          }
        }
      });

      // Draw nodes
      vectors.forEach(v => {
        const hue = kelvinToHue(v.temp);
        const size = 1.5 + v.temp * 2.5;
        ctx.beginPath();
        ctx.arc(v.x, v.y, size, 0, Math.PI * 2);
        ctx.fillStyle = `hsla(${hue}, 80%, 60%, 0.85)`;
        ctx.fill();
      });

      rafRef.current = requestAnimationFrame(draw);
    };

    rafRef.current = requestAnimationFrame(draw);
    return () => { cancelAnimationFrame(rafRef.current); ro.disconnect(); };
  }, []);

  return (
    <div style={{ position: 'relative', width: '100%', height: '500px' }}>
      <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />
      <div style={{
        position: 'absolute', bottom: 8, left: 12,
        fontFamily: 'monospace', fontSize: '9px', color: '#333', letterSpacing: '0.15em',
      }}>
        THERMODYNAMIC SEMANTIC VECTOR SPACE · Ω₂ ENTROPIC ASYMMETRY
      </div>
    </div>
  );
}
