// C5-REAL EXERGY CERTIFIED
import { useEffect, useRef } from 'react';

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
      const parent = canvas.parentElement;
      if (!parent) return;
      const dpr = window.devicePixelRatio || 1;
      canvas.width = parent.clientWidth * dpr;
      canvas.height = parent.clientHeight * dpr;
      ctx.scale(dpr, dpr);
    };

    window.addEventListener('resize', resize);
    resize();

    const getDisplayWidth = () => canvas.width / (window.devicePixelRatio || 1);
    const getDisplayHeight = () => canvas.height / (window.devicePixelRatio || 1);
    const getShieldX = () => getDisplayWidth() * 0.62;

    const createParticle = (
      forceRed: boolean = false,
      customX?: number,
      customY?: number
    ): Particle => {
      const shieldX = getShieldX();
      const startX = customX !== undefined ? customX : Math.random() * (shieldX * 0.45);
      const startY = customY !== undefined ? customY : Math.random() * getDisplayHeight();
      const isRed = forceRed || Math.random() > 0.12;

      return {
        x: startX,
        y: startY,
        vx: (Math.random() * 2.8 + 1.8) * (forceRed ? 1.8 : 1.1),
        vy: (Math.random() - 0.5) * (forceRed ? 4.5 : 2.2),
        radius: Math.random() * 2.5 + 2,
        isPurged: false,
        isValidated: false,
        color: isRed ? '#FF003C' : '#FFAA00',
        alpha: 1.0,
        tail: [],
        entropyLevel: Math.random() * 0.85 + 0.15,
      };
    };

    // Initialize initial pool
    for (let i = 0; i < 160; i++) {
      particles.push(createParticle());
    }

    const handleClick = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      // Spawn burst of stochastic tokens at click
      for (let i = 0; i < 24; i++) {
        particles.push(createParticle(true, x, y));
      }

      shockwaves.push({
        x,
        y,
        radius: 5,
        maxRadius: 60,
        alpha: 1.0,
        color: '#FF003C',
      });

    };

    canvas.addEventListener('click', handleClick);

    const draw = () => {
      const width = getDisplayWidth();
      const height = getDisplayHeight();
      const shieldX = getShieldX();

      // Atmospheric Fade with subtle trail retention
      ctx.fillStyle = 'rgba(3, 3, 5, 0.28)';
      ctx.fillRect(0, 0, width, height);

      // Grid Matrix Background
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.025)';
      ctx.lineWidth = 1;
      const step = 45;
      for (let x = 0; x < width; x += step) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += step) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // Region Boundaries and Aesthetic Labels
      ctx.font = '10px "JetBrains Mono", monospace';
      ctx.fillStyle = 'rgba(255, 0, 60, 0.4)';
      ctx.fillText('DYNAMIS // STOCHASTIC STREAM (POTENCIA)', 24, 28);

      ctx.fillStyle = isFailStopRef.current
        ? 'rgba(255, 0, 60, 0.8)'
        : 'rgba(0, 255, 65, 0.7)';
      ctx.fillText(
        isFailStopRef.current
          ? 'RING-0 QUARANTINE HALT (CAS)'
          : 'ENTELECHEIA // DETERMINISTIC CANONICAL (ACTO)',
        shieldX + 24,
        28
      );

      // Draw C5-REAL Kernel Boundary (Shield)
      const shieldColor = isFailStopRef.current ? '#FF003C' : '#00FF41';

      ctx.save();
      ctx.strokeStyle = shieldColor;
      ctx.lineWidth = isFailStopRef.current ? 4 : 2.5;
      ctx.shadowColor = shieldColor;
      ctx.shadowBlur = isFailStopRef.current ? 25 : 15;

      ctx.beginPath();
      ctx.moveTo(shieldX, 0);
      ctx.lineTo(shieldX, height);
      ctx.stroke();

      // Pulsing Ring-0 Core Node on the Shield
      const pulseY = (Math.sin(Date.now() * 0.003) * 0.4 + 0.5) * height;
      ctx.fillStyle = shieldColor;
      ctx.beginPath();
      ctx.arc(shieldX, pulseY, isFailStopRef.current ? 7 : 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();

      // Spawn new particles continuously
      const spawnCount = isAttackRef.current ? 7 : 2;
      for (let i = 0; i < spawnCount; i++) {
        particles.push(createParticle(isAttackRef.current));
      }

      // Update & Draw Shockwaves
      shockwaves = shockwaves.filter((sw) => sw.alpha > 0.02);
      shockwaves.forEach((sw) => {
        sw.radius += 2.5;
        sw.alpha *= 0.93;

        ctx.save();
        ctx.strokeStyle = sw.color;
        ctx.lineWidth = 2;
        ctx.globalAlpha = sw.alpha;
        ctx.shadowColor = sw.color;
        ctx.shadowBlur = 10;
        ctx.beginPath();
        ctx.arc(sw.x, sw.y, sw.radius, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();
      });

      // Update & Draw Particles
      particles = particles.filter((p) => p.alpha > 0.02 && p.x < width + 50 && p.y > -50 && p.y < height + 50);

      particles.forEach((p) => {
        // Record trail
        p.tail.push({ x: p.x, y: p.y });
        if (p.tail.length > 5) p.tail.shift();

        // Check Shield Collision
        if (!p.isPurged && !p.isValidated && p.x >= shieldX) {
          if (isFailStopRef.current || p.color === '#FF003C' || p.entropyLevel > 0.3) {
            // PURGE / DISPERSE (Fail-Stop)
            p.isPurged = true;
            p.vx = -Math.abs(p.vx) * 0.7 - Math.random() * 2;
            p.vy = (Math.random() - 0.5) * 6;
            p.color = '#FF003C';

            // Shockwave on collision
            if (Math.random() > 0.6) {
              shockwaves.push({
                x: shieldX,
                y: p.y,
                radius: 3,
                maxRadius: 25,
                alpha: 0.8,
                color: '#FF003C',
              });
                    }
            onParticlePurged?.();
          } else {
            // VALIDATED / ATTESTED (Robinson-Łoś standard part st(x))
            p.isValidated = true;
            p.color = '#00FF41';
            p.vx = Math.abs(p.vx) * 1.3 + 1;
            p.vy *= 0.3; // Laminar smooth trajectory

            shockwaves.push({
              x: shieldX,
              y: p.y,
              radius: 4,
              maxRadius: 30,
              alpha: 0.9,
              color: '#00FF41',
            });

            onParticleValidated?.();
          }
        }

        // Particle Physics
        p.x += p.vx;
        p.y += p.vy;

        if (p.isPurged) {
          p.alpha *= 0.94; // Fast fade out
        }

        // Draw Motion Trail
        if (p.tail.length > 1) {
          ctx.save();
          ctx.strokeStyle = p.color;
          ctx.lineWidth = p.radius * 0.7;
          ctx.globalAlpha = p.alpha * 0.35;
          ctx.beginPath();
          ctx.moveTo(p.tail[0].x, p.tail[0].y);
          for (let t = 1; t < p.tail.length; t++) {
            ctx.lineTo(p.tail[t].x, p.tail[t].y);
          }
          ctx.stroke();
          ctx.restore();
        }

        // Draw Particle Core
        ctx.save();
        ctx.fillStyle = p.color;
        ctx.globalAlpha = p.alpha;
        ctx.shadowColor = p.color;
        ctx.shadowBlur = p.isValidated ? 12 : 6;

        ctx.beginPath();
        if (p.isValidated) {
          // Attested Crystal Diamond shape
          ctx.rect(p.x - p.radius, p.y - p.radius, p.radius * 2, p.radius * 2);
        } else {
          ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        }
        ctx.fill();
        ctx.restore();
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
    <div className="causal-canvas-container">
      <canvas ref={canvasRef} className="causal-canvas" />
      <div className="canvas-overlay-guide">
        <span className="guide-text">CLICK CANVAS TO INJECT STOCHASTIC COLLISION</span>
      </div>
    </div>
  );
};
