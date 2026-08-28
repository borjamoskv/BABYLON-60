// C5-REAL EXERGY CERTIFIED
/* ═══════════════════════════════════════════════════════════
   AGENTS.archi — Animations UI Logic
   ═══════════════════════════════════════════════════════════ */

export function initScrollReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.1,
    rootMargin: '0px 0px -40px 0px',
  });

  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

  document.querySelectorAll('.pillar, .bounty-card, .feed-card').forEach((el, i) => {
    el.classList.add('reveal');
    el.style.transitionDelay = `${i * 100}ms`;
    observer.observe(el);
  });
}

export function animateCounters() {
  const counters = document.querySelectorAll('.stat-value[data-count]');

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const target = parseInt(el.dataset.count, 10);
        if (isNaN(target)) return;

        let current = 0;
        const duration = 1500;
        const step = Math.ceil(target / (duration / 16));

        const tick = () => {
          current = Math.min(current + step, target);
          el.textContent = current;
          if (current < target) requestAnimationFrame(tick);
        };

        requestAnimationFrame(tick);
        observer.unobserve(el);
      }
    });
  }, { threshold: 0.5 });

  counters.forEach(c => observer.observe(c));
}

export function initScoreBars() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.querySelectorAll('.score-fill').forEach(fill => {
          fill.style.width = `${fill.dataset.fill}%`;
        });
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.3 });

  document.querySelectorAll('.scorecard-preview').forEach(el => observer.observe(el));
}

export function initLabMetrics() {
  const throughputEl = document.getElementById('lab-throughput');
  const bars = document.querySelectorAll('#lab-chart .bar');
  if (!throughputEl || bars.length === 0) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        let val = 0;
        const target = 3996470;
        const tick = () => {
          val += Math.floor(Math.random() * 80000) + 40000;
          if (val >= target) {
            throughputEl.replaceChildren();
            throughputEl.appendChild(document.createTextNode('3.99M '));
            const u = document.createElement('small');
            u.textContent = 'agts/sec';
            throughputEl.appendChild(u);
          } else {
            throughputEl.replaceChildren();
            throughputEl.appendChild(document.createTextNode(`${(val / 1000000).toFixed(2)}M `));
            const u = document.createElement('small');
            u.textContent = 'agts/sec';
            throughputEl.appendChild(u);
            requestAnimationFrame(tick);
          }
        };
        requestAnimationFrame(tick);

        bars.forEach((bar, i) => {
          setTimeout(() => {
            bar.style.height = `${bar.dataset.h}%`;
          }, i * 100);
        });

        setInterval(() => {
          const randomBar = bars[Math.floor(Math.random() * bars.length)];
          if (!randomBar) return;
          const baseH = parseInt(randomBar.dataset.h, 10);
          const jitter = (Math.random() - 0.5) * 15;
          randomBar.style.height = `${Math.max(20, Math.min(100, baseH + jitter))}%`;
        }, 800);

        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.2 });

  const labSection = document.getElementById('lab');
  if (labSection) observer.observe(labSection);
}

export function initTerminalAnimation() {
  const terminals = document.querySelectorAll('.pillar-terminal');

  terminals.forEach(terminal => {
    const lines = terminal.querySelectorAll('.terminal-body .line');
    lines.forEach(line => {
      line.style.animationPlayState = 'paused';
    });

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          lines.forEach(line => {
            line.style.animationPlayState = 'running';
          });
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.4 });

    observer.observe(terminal);
  });
}

export function initTypingCursor() {
  const cursor = document.getElementById('council-cursor');
  if (!cursor) return;

  setInterval(() => {
    cursor.style.opacity = cursor.style.opacity === '0' ? '1' : '0';
  }, 500);
}

export function initFooterYear() {
  const el = document.getElementById('footer-year');
  if (el) el.textContent = new Date().getFullYear();
}
