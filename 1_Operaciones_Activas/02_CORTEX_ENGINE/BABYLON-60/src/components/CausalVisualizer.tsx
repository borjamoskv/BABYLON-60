// C5-REAL EXERGY CERTIFIED
import React, { useEffect, useRef } from 'react';

export const CausalVisualizer: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let particles: { x: number; y: number; vx: number; vy: number; isPurged: boolean }[] = [];

    const resize = () => {
      canvas.width = canvas.parentElement?.clientWidth || window.innerWidth;
      canvas.height = canvas.parentElement?.clientHeight || window.innerHeight;
    };

    window.addEventListener('resize', resize);
    resize();

    // Shield properties
    const shieldX = canvas.width * 0.7;

    const initParticles = () => {
      for (let i = 0; i < 150; i++) {
        particles.push({
          x: Math.random() * shieldX,
          y: Math.random() * canvas.height,
          vx: (Math.random() * 2 + 1), // moving right
          vy: (Math.random() - 0.5) * 2,
          isPurged: false
        });
      }
    };

    initParticles();

    const draw = () => {
      // Fade effect for trails
      ctx.fillStyle = 'rgba(5, 5, 5, 0.2)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw Kernel Shield
      ctx.beginPath();
      ctx.moveTo(shieldX, 0);
      ctx.lineTo(shieldX, canvas.height);
      ctx.strokeStyle = 'rgba(0, 255, 65, 0.5)';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Shield Glow
      ctx.shadowBlur = 15;
      ctx.shadowColor = '#00FF41';
      ctx.stroke();
      ctx.shadowBlur = 0;

      // Update and draw particles
      particles.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;

        // Collision with shield
        if (!p.isPurged && p.x >= shieldX - 5) {
          // 80% chance of being rejected (stochastic noise)
          if (Math.random() > 0.2) {
            // Rejected: bounce back, turn darker red and die eventually
            p.vx = -p.vx * 0.5;
            p.vy = (Math.random() - 0.5) * 5;
            p.isPurged = true;
          } else {
            // Accepted: turn green, move fast to the right
            p.isPurged = true;
            p.vx = 4;
            p.vy = 0;
            p.x = shieldX + 1;
          }
        }

        // Draw particle
        ctx.beginPath();
        ctx.arc(p.x, p.y, 2, 0, Math.PI * 2);

        if (p.x > shieldX) {
          // Validated state
          ctx.fillStyle = '#00FF41';
          ctx.shadowBlur = 5;
          ctx.shadowColor = '#00FF41';
        } else if (p.isPurged && p.x < shieldX) {
          // Rejected state
          ctx.fillStyle = 'rgba(255, 0, 60, 0.3)';
          ctx.shadowBlur = 0;
        } else {
          // Stochastic potential
          ctx.fillStyle = '#FF003C';
          ctx.shadowBlur = 8;
          ctx.shadowColor = '#FF003C';
        }

        ctx.fill();
        ctx.shadowBlur = 0;

        // Respawn
        if (p.x > canvas.width || p.x < 0 || p.y > canvas.height || p.y < 0) {
          p.x = 0;
          p.y = Math.random() * canvas.height;
          p.vx = (Math.random() * 2 + 1);
          p.vy = (Math.random() - 0.5) * 2;
          p.isPurged = false;
        }
      });

      animationFrameId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return <canvas ref={canvasRef} className="visualizer-container" />;
};
