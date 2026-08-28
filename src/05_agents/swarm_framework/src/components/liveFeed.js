// C5-REAL EXERGY CERTIFIED
/* ═══════════════════════════════════════════════════════════
   AGENTS.archi — Live Threat Feed Component
   ═══════════════════════════════════════════════════════════ */

export async function renderLiveFeed() {
  const grid = document.getElementById('feed-grid');
  if (!grid) return;

  try {
    const response = await fetch('/_facts.json');
    if (!response.ok) throw new Error('Ouroboros feed failed, falling back to static');

    const data = await response.json();
    const threats = data.reverse().slice(0, 12).map((t, i) => {
      // Mapping Ouroboros schema to the visual feed schema
      return {
        id: t.id || `OB-${t.target_id || i}`,
        cve: t.id || `AGENT-STRIKE-${t.target_id || i}`,
        severity: (t.severity || 'high').toLowerCase(),
        title: t.title,
        desc: `Target: ${t.target_name || t.target || 'Unknown'}. Status: ${t.status}. ${t.poc_verified ? 'PoC Verified [C5-REAL]' : ''}`,
        source: t.platform || 'Unknown',
        cvss: t.confidence || 'C5-REAL',
        date: new Date(t.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
      };
    });

    if (threats.length === 0) throw new Error('Empty feed');

    grid.innerHTML = '';

    threats.forEach((t, i) => {
      const card = document.createElement('div');
      card.className = `feed-card feed-${t.severity} reveal`;
      card.id = `feed-${t.id}`;
      card.style.transitionDelay = `${i * 80}ms`;

      // ── Header ──
      const header = document.createElement('div');
      header.className = 'feed-card-header';

      const headerLeft = document.createElement('div');
      headerLeft.className = 'feed-header-left';
      const cve = document.createElement('span');
      cve.className = 'feed-cve';
      cve.textContent = t.cve;
      headerLeft.appendChild(cve);
      if (i === 0) {
        const badge = document.createElement('span');
        badge.className = 'feed-badge-new';
        badge.textContent = 'NEW';
        headerLeft.appendChild(badge);
      }

      const severity = document.createElement('span');
      severity.className = `feed-severity ${t.severity}`;
      severity.textContent = t.severity.toUpperCase();

      header.append(headerLeft, severity);

      // ── Body ──
      const title = document.createElement('h4');
      title.textContent = t.title;
      const desc = document.createElement('p');
      desc.textContent = t.desc;

      // ── Meta ──
      const meta = document.createElement('div');
      meta.className = 'feed-meta';
      const source = document.createElement('span');
      source.className = 'feed-source';
      source.textContent = t.source;
      meta.appendChild(source);
      if (t.cvss) {
        const cvss = document.createElement('span');
        cvss.className = `feed-cvss cvss-${t.severity}`;
        cvss.textContent = t.cvss;
        meta.appendChild(cvss);
      }
      const date = document.createElement('span');
      date.className = 'feed-date';
      date.textContent = t.date;
      meta.appendChild(date);

      card.append(header, title, desc, meta);
      grid.appendChild(card);
    });

    // Re-init reveal observer for new elements
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
        }
      });
    }, { threshold: 0.1 });

    grid.querySelectorAll('.reveal').forEach(el => observer.observe(el));

  } catch (err) {
    console.error(err);
    // Feed unavailable — hardcoded fallbacks rendered by static HTML
  }
}
