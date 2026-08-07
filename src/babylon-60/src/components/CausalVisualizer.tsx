// C5-REAL EXERGY CERTIFIED
import React, { useEffect, useRef } from 'react';
import { sound } from './AudioSynthesizer';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  isPurged: boolean;
  isValidated: boolean;
  color: string;
  alpha: number;
  tail: { x: number; y: number }[];
  entropyLevel: number;
}

interface Shockwave {
  x: number;
  y: number;
  radius: number;
  maxRadius: number;
  alpha: number;
  color: string;
}

interface Props {
  isAttackActive: boolean;
  isFailStopActive: boolean;
  onParticlePurged?: () => void;
  onParticleValidated?: () => void;
}

export const CausalVisualizer = ({
  isAttackActive,
  isFailStopActive,
  onParticlePurged,
  onParticleValidated,
}: Props) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const isAttackRef = useRef(isAttackActive);
  const isFailStopRef = useRef(isFailStopActive);

  useEffect(() => {
    isAttackRef.current = isAttackActive;
  }, [isAttackActive]);

  useEffect(() => {
    isFailStopRef.current = isFailStopActive;
  }, [isFailStopActive]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let particles: Particle[] = [];
    let shockwaves: Shockwave[] = [];

    const resize = () => {
      canvas.width = canvas.parentElement?.clientWidth || window.innerWidth;
      canvas.height = canvas.parentElement?.clientHeight || window.innerHeight;
    };

    window.addEventListener('resize', resize);
    resize();

    const getShieldX = () => canvas.width * 0.65;

    const createParticle = (forceRed: boolean = false, customX?: number, customY?: number): Particle => {
      const shieldX = getShieldX();
      const startX = customX !== undefined ? customX : Math.random() * (shieldX * 0.5);
      const startY = customY !== undefined ? customY : Math.random() * canvas.height;
      const isRed = forceRed || Math.random() > 0.1;

      return {
        x: startX,
        y: startY,
        vx: (Math.random() * 2.5 + 1.5) * (forceRed ? 1.5 : 1),
        vy: (Math.random() - 0.5) * (forceRed ? 4 : 2),
        radius: Math.random() * 2 + 2,
        isPurged: false,
        isValidated: false,
        color: isRed ? '#FF003C' : '#FFAA00',
        alpha: 1.0,
        tail: [],
        entropyLevel: Math.random() * 0.8 + 0.2,
      };
    };

    // Initialize initial pool
    for (let i = 0; i < 180; i++) {
      particles.push(createParticle());
    }

    const handleClick = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      // Spawn burst of red stochastic tokens
      for (let i = 0; i < 20; i++) {
        particles.push(createParticle(true, x, y));
      }
      sound.playPurge();
    };

    canvas.addEventListener('click', handleClick);

    const draw = () => {
      const shieldX = getShieldX();

      // Atmospheric Fade
      ctx.fillStyle = 'rgba(5, 5, 5, 0.25)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw Grid Matrix Background
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.02)';
      ctx.lineWidth = 1;
      const step = 40;
      for (let x = 0; x < canvas.width; x += step) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
      }
      for (let y = 0; y < canvas.height; y += step) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
      }

      // Draw C5-REAL Kernel Boundary (Shield)
      const shieldColor = isFailStopRef.current ? '#FF003C' : '#00FF41';

      ctx.save();
      ctx.beginPath();
      ctx.moveTo(shieldX, 0);
      ctx.lineTo(shieldX, canvas.height);
      ctx.strokeStyle = shieldColor;
      ctx.lineWidth = isFailStopRef.current ? 4 : 2;
      ctx.shadowBlur = isFailStopRef.current ? 25 : 15;
      ctx.shadowColor = shieldColor;
      ctx.stroke();

      // Draw Boundary Chevron Markers
      for (let y = 30; y < canvas.height; y += 60) {
        ctx.beginPath();
        ctx.arc(shieldX, y, 3, 0, Math.PI * 2);
        ctx.fillStyle = shieldColor;
        ctx.fill();
      }
      ctx.restore();

      // If attack is active, spawn aggressive swarms
      if (isAttackRef.current && Math.random() > 0.4) {
        particles.push(createParticle(true, 0, Math.random() * canvas.height));
      }

      // Update & Draw Shockwaves
      shockwaves = shockwaves.filter((sw) => {
        sw.radius += 2.5;
        sw.alpha -= 0.03;

        if (sw.alpha <= 0) return false;

        ctx.save();
        ctx.beginPath();
        ctx.arc(sw.x, sw.y, sw.radius, 0, Math.PI * 2);
        ctx.strokeStyle = sw.color;
        ctx.lineWidth = 2;
        ctx.globalAlpha = Math.max(0, sw.alpha);
        ctx.shadowBlur = 10;
        ctx.shadowColor = sw.color;
        ctx.stroke();
        ctx.restore();

        return true;
      });

      // Update & Draw Particles
      particles.forEach((p) => {
        // Save tail
        p.tail.push({ x: p.x, y: p.y });
        if (p.tail.length > 6) p.tail.shift();

        p.x += p.vx;
        p.y += p.vy;

        // Collision Check with Ring-0 Barrier
        if (!p.isPurged && !p.isValidated && p.x >= shieldX - 4) {
          if (isFailStopRef.current) {
            // FAIL-STOP: 100% REJECTION
            p.vx = -Math.abs(p.vx) * 1.2;
            p.vy = (Math.random() - 0.5) * 6;
            p.isPurged = true;
            p.color = '#FF003C';
            shockwaves.push({
              x: shieldX,
              y: p.y,
              radius: 4,
              maxRadius: 35,
              alpha: 0.9,
              color: '#FF003C',
            });
            sound.playPurge();
            onParticlePurged?.();
          } else {
            // Standard Deterministic Gate: 85% purge, 15% validate
            const isCompliant = Math.random() <= 0.15;
            if (isCompliant) {
              p.isValidated = true;
              p.x = shieldX + 2;
              p.vx = 5.5; // Acceleration of validated state
              p.vy = (Math.random() - 0.5) * 0.5;
              p.color = '#00FF41';
              shockwaves.push({
                x: shieldX,
                y: p.y,
                radius: 4,
                maxRadius: 25,
                alpha: 0.8,
                color: '#00FF41',
              });
              sound.playValidate();
              onParticleValidated?.();
            } else {
              p.isPurged = true;
              p.vx = -Math.abs(p.vx) * 0.7;
              p.vy = (Math.random() - 0.5) * 5;
              p.color = '#FF003C';
              shockwaves.push({
                x: shieldX,
                y: p.y,
                radius: 3,
                maxRadius: 20,
                alpha: 0.6,
                color: '#FF003C',
              });
              sound.playPurge();
              onParticlePurged?.();
            }
          }
        }

        // Draw particle tail
        if (p.tail.length > 1) {
          ctx.save();
          ctx.beginPath();
          ctx.moveTo(p.tail[0].x, p.tail[0].y);
          for (let i = 1; i < p.tail.length; i++) {
            ctx.lineTo(p.tail[i].x, p.tail[i].y);
          }
          ctx.strokeStyle = p.color;
          ctx.globalAlpha = p.isValidated ? 0.4 : 0.15;
          ctx.lineWidth = p.radius * 0.8;
          ctx.stroke();
          ctx.restore();
        }

        // Draw Particle Body
        ctx.save();
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.shadowBlur = p.isValidated ? 12 : p.isPurged ? 0 : 8;
        ctx.shadowColor = p.color;
        ctx.fill();

        // Draw geometric ring for validated crystal tokens
        if (p.isValidated) {
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.radius + 3, 0, Math.PI * 2);
          ctx.strokeStyle = 'rgba(0, 255, 65, 0.4)';
          ctx.lineWidth = 1;
          ctx.stroke();
        }
        ctx.restore();

        // Recycle particle
        if (p.x > canvas.width || p.x < 0 || p.y > canvas.height || p.y < 0) {
          const np = createParticle();
          Object.assign(p, np);
        }
      });

      animationFrameId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener('resize', resize);
      canvas.removeEventListener('click', handleClick);
      cancelAnimationFrame(animationFrameId);
    };
  }, [onParticlePurged, onParticleValidated]);

  return (
    <div className="visualizer-wrapper">
      <canvas ref={canvasRef} className="visualizer-container" />
      <div className="canvas-watermark">
        <span>LEFT: STOCHASTIC POTENTIAL DYNAMIS (H(X))</span>
        <span>RIGHT: CANONICAL ENTELECHEIA (RING-0 DETERMINISM)</span>
      </div>
    </div>
  );
};
