// C5-REAL EXERGY CERTIFIED
export async function initNexusGraph() {
  const container = document.getElementById('nexus-graph-container');
  if (!container) return;

  try {
    const response = await fetch('/docs_nexus/nexus_index.json');
    if (!response.ok) throw new Error('Nexus graph not found');

    const nodes = await response.json();

    if (nodes.length === 0) {
      container.innerHTML = '<p class="text-dim">El grafo Nexus está vacío o en cristalización.</p>';
      return;
    }

    const html = nodes.map(node => `
      <div class="nexus-node-card">
        <div class="nexus-node-header">
          <span class="nexus-node-source">${node.source}</span>
          <h3 class="nexus-node-title">${node.name}</h3>
        </div>
        <div class="nexus-node-meta">
          <span class="nexus-node-id">${node.id}</span>
          <a href="${node.path}" target="_blank" class="nexus-node-link">Inspeccionar Módulo →</a>
        </div>
      </div>
    `).join('');

    container.innerHTML = `<div class="nexus-graph-grid">${html}</div>`;
  } catch (error) {
    console.error('[C5-REAL] Error loading Nexus Graph:', error);
    container.innerHTML = '<p class="text-error">Fallo de Telemetría al cargar Nexus Graph.</p>';
  }
}
