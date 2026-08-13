// C5-REAL EXERGY CERTIFIED
/* ═══════════════════════════════════════════════════════════
   AGENTS.archi — Sovereign Enhancements v2.0
   Hero Terminal · Live Counter · Ambient Orbs · Risk Bars
   ═══════════════════════════════════════════════════════════ */

// ── 1. AMBIENT ORB SYSTEM ──────────────────────────────────
export function initAmbientOrbs() {
  const orbs = [
    { cls: 'orb-blue',   delay: 0 },
    { cls: 'orb-purple', delay: 0 },
    { cls: 'orb-red',    delay: 0 },
  ];

  orbs.forEach(o => {
    if (document.querySelector(`.${o.cls}`)) return; // avoid dupe
    const el = document.createElement('div');
    el.className = `ambient-orb ${o.cls}`;
    document.body.insertAdjacentElement('afterbegin', el);
  });
}

// ── 2. HERO TERMINAL ANIMATION ────────────────────────────
const TERMINAL_LINES = [
  { cls: 't-prompt',  text: '$ cortex audit --target=k2-lending' },
  { cls: 't-output',  text: '→ Scanning KineticRouter.sol …' },
  { cls: 't-warning', text: '⚠  close-factor: unbounded (0x2e3…)' },
  { cls: 't-output',  text: '→ Generating Anvil-Lang PoC …' },
  { cls: 't-success', text: '✓ OUROBOROS-K2-01 [CRITICAL] verified' },
  { cls: 't-prompt',  text: '$ git commit -m "C5-REAL forensic bundle"' },
  { cls: 't-success', text: '✓ Merkle root: 0xa3f7c9…' },
];

export function initHeroTerminal() {
  const wrapper = document.getElementById('hero-terminal');
  if (!wrapper) return;

  const body = wrapper.querySelector('.hero-terminal-body');
  if (!body) return;

  let idx = 0;

  function showLine() {
    if (idx >= TERMINAL_LINES.length) {
      // Reset after pause
      setTimeout(() => {
        idx = 0;
        body.innerHTML = '';
        setTimeout(showLine, 600);
      }, 3500);
      return;
    }

    const { cls, text } = TERMINAL_LINES[idx];
    const line = document.createElement('span');
    line.className = `hero-term-line ${cls}`;
    line.textContent = text;
    body.appendChild(line);

    // Trigger animation on next frame
    requestAnimationFrame(() => {
      requestAnimationFrame(() => line.classList.add('visible'));
    });

    idx++;
    setTimeout(showLine, 650);
  }

  // Start after page load delay
  setTimeout(showLine, 2200);
}

// ── 3. LIVE THREAT COUNTER ────────────────────────────────
export function initLiveThreatCounter() {
  const el = document.getElementById('hero-live-count');
  if (!el) return;

  let base = 847;
  el.textContent = base;

  // Slowly increment to simulate live stream
  setInterval(() => {
    if (Math.random() > 0.6) {
      base += Math.floor(Math.random() * 3) + 1;
      el.textContent = base.toLocaleString();
    }
  }, 4200);
}

// ── 4. THREAT CARD RISK BARS ──────────────────────────────
const RISK_SCORES = {
  'Prompt Injection':         82,
  'Tool Misuse':              91,
  'Memory Poisoning':         88,
  'Privilege Escalation':     95,
  'Economic Exploits':        97,
  'MCP Supply Chain':         89,
  'Multi-Agent Collusion':    76,
  'Infinite Loop DoS':        62,
  'Side-Channel Exfiltration':74,
  'Identity Hijacking':       85,
};

export function initThreatRiskBars() {
  // Called after renderThreatGrid() populates the DOM
  document.querySelectorAll('.threat-card').forEach(card => {
    const title = card.querySelector('h4')?.textContent?.trim();
    const pct = RISK_SCORES[title] ?? 70;

    card.style.setProperty('--risk-pct', `${pct}%`);

    const bar = document.createElement('div');
    bar.className = 'threat-risk-bar';
    const fill = document.createElement('div');
    fill.className = 'threat-risk-fill';
    fill.setAttribute('aria-label', `Risk score: ${pct}%`);
    bar.appendChild(fill);
    card.appendChild(bar);
  });
}

// ── 5. SCROLL PROGRESS BAR ────────────────────────────────
export function initScrollProgressBar() {
  let bar = document.getElementById('scroll-progress');
  if (!bar) {
    bar = document.createElement('div');
    bar.id = 'scroll-progress';
    document.body.insertAdjacentElement('afterbegin', bar);
  }

  window.addEventListener('scroll', () => {
    const scrolled = window.scrollY;
    const total = document.documentElement.scrollHeight - window.innerHeight;
    const pct = total > 0 ? (scrolled / total) * 100 : 0;
    bar.style.width = `${pct}%`;
  }, { passive: true });
}

// ── 6. SECTION WARP REVEAL (enhanced) ────────────────────
export function initWarpReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        el.classList.add('visible');
        observer.unobserve(el);
      }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -30px 0px' });

  document.querySelectorAll('.threat-card, .feed-card, .bounty-card, .pillar, .cert-item, .saga-step').forEach(el => {
    el.classList.add('reveal');
    observer.observe(el);
  });
}
