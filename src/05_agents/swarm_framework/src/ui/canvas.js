// C5-REAL EXERGY CERTIFIED
/* ═══════════════════════════════════════════════════════════
   AGENTS.archi — Canvas UI Logic
   ═══════════════════════════════════════════════════════════ */

export function initHeroInteractive() {
  const hero = document.getElementById('hero');
  const glow = document.getElementById('hero-interactive-glow');
  if (!hero || !glow) return;

  hero.addEventListener('mousemove', (e) => {
    const rect = hero.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    requestAnimationFrame(() => {
      glow.style.left = `${x - 300}px`;
      glow.style.top = `${y - 300}px`;
      glow.style.opacity = '0.6';
    });
  });

  hero.addEventListener('mouseleave', () => {
    glow.style.opacity = '0';
  });
}

export function initParticleGrid() {
  const canvas = document.getElementById('hero-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let particles = [];
  let animationId;

  function resize() {
    const hero = document.getElementById('hero');
    if (!hero) return;
    const dpr = window.devicePixelRatio || 1;
    const w = hero.offsetWidth;
    const h = hero.offsetHeight;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    canvas.style.width = w + 'px';
    canvas.style.height = h + 'px';
    ctx.scale(dpr, dpr);
  }

  function createParticles() {
    particles = [];
    const dpr = window.devicePixelRatio || 1;
    const w = canvas.width / dpr;
    const h = canvas.height / dpr;
    const count = Math.floor((w * h) / 18000);
    for (let i = 0; i < count; i++) {
      particles.push({
        x: Math.random() * w,
        y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.3,
        vy: (Math.random() - 0.5) * 0.3,
        r: Math.random() * 1.5 + 0.5,
      });
    }
  }

  function draw() {
    const dpr = window.devicePixelRatio || 1;
    const w = canvas.width / dpr;
    const h = canvas.height / dpr;
    ctx.clearRect(0, 0, w, h);

    const maxDist = 120;
    const maxDist2 = maxDist * maxDist;
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        if (dx > maxDist || dx < -maxDist) continue;
        const dy = particles[i].y - particles[j].y;
        if (dy > maxDist || dy < -maxDist) continue;
        const dist2 = dx * dx + dy * dy;
        if (dist2 < maxDist2) {
          const dist = Math.sqrt(dist2);
          ctx.beginPath();
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.strokeStyle = `rgba(43, 59, 229, ${0.08 * (1 - dist / maxDist)})`;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }

    for (const p of particles) {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(77, 91, 247, 0.3)';
      ctx.fill();

      p.x += p.vx;
      p.y += p.vy;

      if (p.x < 0 || p.x > w) p.vx *= -1;
      if (p.y < 0 || p.y > h) p.vy *= -1;
    }

    animationId = requestAnimationFrame(draw);
  }

  resize();
  createParticles();
  draw();

  window.addEventListener('resize', () => {
    resize();
    createParticles();
  });

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        if (!animationId) draw();
      } else {
        cancelAnimationFrame(animationId);
        animationId = null;
      }
    });
  }, { threshold: 0 });

  const heroSection = document.getElementById('hero');
  if (heroSection) observer.observe(heroSection);
}
