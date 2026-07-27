'use client';
import React, { useEffect, useRef } from 'react';

type Point = { x: number; y: number; z: number };

// Lorenz attractor parameters
const SIGMA = 10;
const RHO = 28;
const BETA = 8 / 3;
const DT = 0.005;
const TRAIL_LENGTH = 800;

function lorenzStep(p: Point): Point {
  return {
    x: p.x + DT * SIGMA * (p.y - p.x),
    y: p.y + DT * (p.x * (RHO - p.z) - p.y),
    z: p.z + DT * (p.x * p.y - BETA * p.z),
  };
}

export default function WebGLAttractor() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let point: Point = { x: 0.1, y: 0, z: 0 };
    const trail: Point[] = [];
    let frame = 0;

    const resize = () => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    const draw = () => {
      const { width, height } = canvas;
      ctx.fillStyle = 'rgba(3, 3, 3, 0.08)';
      ctx.fillRect(0, 0, width, height);

      // Advance attractor
      for (let i = 0; i < 3; i++) {
        point = lorenzStep(point);
        trail.push({ ...point });
      }
      if (trail.length > TRAIL_LENGTH) trail.splice(0, trail.length - TRAIL_LENGTH);

      // Project 3D -> 2D (orthographic XZ)
      const scaleX = width / 60;
      const scaleY = height / 50;
      const offsetX = width / 2;
      const offsetY = height * 0.55;

      ctx.beginPath();
      trail.forEach((p, i) => {
        const sx = p.x * scaleX + offsetX;
        const sy = -p.z * scaleY + offsetY;
        const alpha = i / trail.length;
        const hue = (frame * 0.2 + i * 0.1) % 360;
        ctx.strokeStyle = `hsla(${hue}, 80%, 55%, ${alpha * 0.8})`;
        if (i === 0) ctx.moveTo(sx, sy);
        else ctx.lineTo(sx, sy);
      });
      ctx.lineWidth = 0.8;
      ctx.stroke();

      frame++;
      rafRef.current = requestAnimationFrame(draw);
    };

    rafRef.current = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(rafRef.current);
      ro.disconnect();
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{ width: '100%', height: '100%', display: 'block', background: '#030303' }}
    />
  );
}
