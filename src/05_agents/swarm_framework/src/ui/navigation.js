// C5-REAL EXERGY CERTIFIED
/* ═══════════════════════════════════════════════════════════
   AGENTS.archi — Navigation UI Logic
   ═══════════════════════════════════════════════════════════ */

export function initNavScroll() {
  const nav = document.getElementById('nav-main');
  if (!nav) return;

  let ticking = false;
  window.addEventListener('scroll', () => {
    if (!ticking) {
      window.requestAnimationFrame(() => {
        nav.classList.toggle('scrolled', window.scrollY > 40);
        ticking = false;
      });
      ticking = true;
    }
  }, { passive: true });
}

export function initMobileMenu() {
  const toggle = document.getElementById('nav-toggle');
  const navLinks = document.getElementById('nav-links');
  if (!toggle || !navLinks) return;

  toggle.addEventListener('click', () => {
    toggle.classList.toggle('active');
    navLinks.classList.toggle('active');
    document.body.style.overflow = navLinks.classList.contains('active') ? 'hidden' : '';
  });

  navLinks.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      toggle.classList.remove('active');
      navLinks.classList.remove('active');
      document.body.style.overflow = '';
    });
  });
}

export function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      e.preventDefault();
      const target = document.querySelector(anchor.getAttribute('href'));
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}

export function initActiveNavTracking() {
  const sections = ['threat-vectors', 'solution', 'track-record', 'threat-feed', 'pricing', 'sovereign-council'];
  const navLinks = {
    'threat-vectors': document.getElementById('nav-taxonomy'),
    'solution': document.getElementById('nav-solution'),
    'track-record': document.getElementById('nav-track'),
    'threat-feed': document.getElementById('nav-feed'),
    'pricing': document.getElementById('nav-pricing-link'),
    'sovereign-council': document.getElementById('nav-council'),
  };

  let activeSections = new Set();

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        activeSections.add(entry.target.id);
      } else {
        activeSections.delete(entry.target.id);
      }
    });

    Object.values(navLinks).forEach(l => l && l.classList.remove('active'));

    for (const id of sections) {
      if (activeSections.has(id)) {
        const link = navLinks[id];
        if (link) link.classList.add('active');
        break;
      }
    }
  }, {
    threshold: 0.15,
    rootMargin: '-80px 0px -50% 0px',
  });

  sections.forEach(id => {
    const el = document.getElementById(id);
    if (el) observer.observe(el);
  });
}

export function initBackToTop() {
  const btn = document.getElementById('back-to-top');
  if (!btn) return;

  let ticking = false;
  window.addEventListener('scroll', () => {
    if (!ticking) {
      window.requestAnimationFrame(() => {
        btn.classList.toggle('visible', window.scrollY > 500);
        ticking = false;
      });
      ticking = true;
    }
  }, { passive: true });

  btn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

export function initScrollProgress() {
  const bar = document.createElement('div');
  bar.className = 'scroll-progress';
  document.body.appendChild(bar);

  let docHeight = document.documentElement.scrollHeight - window.innerHeight;
  window.addEventListener('resize', () => {
    docHeight = document.documentElement.scrollHeight - window.innerHeight;
  }, { passive: true });

  let ticking = false;
  window.addEventListener('scroll', () => {
    if (!ticking) {
      window.requestAnimationFrame(() => {
        const pct = docHeight > 0 ? (window.scrollY / docHeight) * 100 : 0;
        bar.style.width = `${pct}%`;
        ticking = false;
      });
      ticking = true;
    }
  }, { passive: true });
}
