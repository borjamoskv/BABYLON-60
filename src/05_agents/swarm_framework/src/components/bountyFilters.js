// C5-REAL EXERGY CERTIFIED
/* ══════════════════════════════════════════════════════════
   Bounty Grid Renderer & Filters — C5-REAL
   ══════════════════════════════════════════════════════════ */

export async function initBountyFilters() {
  const grid = document.getElementById('bounty-grid');
  if (!grid) return;

  try {
    const response = await fetch('/_facts.json');
    if (!response.ok) throw new Error('Failed to fetch _facts.json');

    const data = await response.json();

    grid.innerHTML = ''; // Limpiar fallback estático

    const validBounties = data.filter(t => t.id && (t.target_name || t.target));

    validBounties.forEach(t => {
      const severity = (t.severity || 'high').toLowerCase();
      // Translate severity for display
      const severityDisplay = severity === 'critical' ? 'Crítico' : severity === 'high' ? 'Alta' : severity === 'medium' ? 'Media' : severity.toUpperCase();

      let titleParts = t.title.split(':');
      let vulnName = titleParts.length > 1 ? titleParts.slice(1).join(':').trim() : t.title;

      const card = document.createElement('div');
      card.className = `bounty-card`;
      card.id = `bounty-${t.id}`;

      card.innerHTML = `
        <div class="bounty-severity ${severity}">${severityDisplay}</div>
        <h4>${t.target_name || t.target}</h4>
        <p class="bounty-vuln">${vulnName}</p>
        <p class="bounty-desc">Plataforma: ${t.platform} | Confianza: ${t.confidence} | Estado: ${t.status}</p>
        <div class="bounty-meta">
          <span class="bounty-id">${t.id}</span>
          <span class="bounty-link locked" style="color: rgba(243, 244, 246, 0.4); text-decoration: none; border-bottom: 1px dotted rgba(255,255,255,0.2); cursor: not-allowed;">[ EMBARGO ACTIVO ]</span>
        </div>
      `;
      grid.appendChild(card);
    });

  } catch (err) {
    console.error('Bounty fetch error:', err);
  }

  // Init filters
  const filters = document.querySelectorAll('.bounty-filter');
  const cards = document.querySelectorAll('.bounty-card');

  if (!filters.length || !cards.length) return;

  filters.forEach(btn => {
    btn.addEventListener('click', () => {
      const filter = btn.dataset.filter;

      filters.forEach(f => f.classList.remove('active'));
      btn.classList.add('active');

      let delay = 0;
      cards.forEach(card => {
        const severityNode = card.querySelector('.bounty-severity');
        if (!severityNode) return;

        const severityClass = severityNode.classList.contains('critical') ? 'critical'
          : severityNode.classList.contains('high') ? 'high'
          : severityNode.classList.contains('medium') ? 'medium'
          : 'all';

        if (filter === 'all' || severityClass === filter) {
          card.classList.remove('filtered-out');
          card.style.animation = 'none';
          card.offsetHeight; // trigger reflow
          card.style.animation = '';
          card.style.animationDelay = `${delay * 50}ms`;
          delay++;
        } else {
          card.classList.add('filtered-out');
        }
      });
    });
  });
}
