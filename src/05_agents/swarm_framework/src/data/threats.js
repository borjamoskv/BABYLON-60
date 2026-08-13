// C5-REAL EXERGY CERTIFIED
/* ═══════════════════════════════════════════════════════════
   AGENTS.archi — Threat Taxonomy Data
   ═══════════════════════════════════════════════════════════ */

const THREAT_VECTORS = [
  {
    icon: '🎯',
    title: 'Prompt Injection',
    desc: 'Agent executes attacker-controlled instructions embedded in user input, tool output, or retrieved context.',
    status: 'partial',
    statusText: 'Partial Coverage',
    accent: '#FF8C42',
  },
  {
    icon: '🔧',
    title: 'Tool Misuse',
    desc: 'Agent invokes tools in unintended ways — deleting files, transferring funds, or calling APIs beyond scope.',
    status: 'unsolved',
    statusText: 'No Solution',
    accent: '#FF3B5C',
  },
  {
    icon: '🧠',
    title: 'Memory Poisoning',
    desc: 'Long-term memory corrupted to alter future decisions. False memories injected across conversation boundaries.',
    status: 'unsolved',
    statusText: 'No Solution',
    accent: '#FF3B5C',
  },
  {
    icon: '🔓',
    title: 'Privilege Escalation',
    desc: 'Agent gains access to tools, data, or capabilities beyond its authorized scope through indirect manipulation.',
    status: 'unsolved',
    statusText: 'No Solution',
    accent: '#FF3B5C',
  },
  {
    icon: '💰',
    title: 'Economic Exploits',
    desc: 'Financial decisions manipulated through adversarial market conditions, oracle attacks, or engineered edge cases.',
    status: 'unsolved',
    statusText: 'No Solution',
    accent: '#FF3B5C',
  },
  {
    icon: '🔗',
    title: 'MCP Supply Chain',
    desc: 'Compromised MCP servers inject malicious tool definitions, exfiltrate data, or hijack agent execution flow.',
    status: 'unsolved',
    statusText: 'No Solution',
    accent: '#FF3B5C',
  },
  {
    icon: '🤝',
    title: 'Multi-Agent Collusion',
    desc: 'In swarm architectures, agents cooperate against the principal\'s interests through emergent or designed coordination.',
    status: 'unsolved',
    statusText: 'No Solution',
    accent: '#FF3B5C',
  },
  {
    icon: '♾️',
    title: 'Infinite Loop DoS',
    desc: 'Agent trapped in recursive execution, burning tokens and compute. No circuit breaker, no kill switch.',
    status: 'partial',
    statusText: 'Partial Coverage',
    accent: '#FF8C42',
  },
  {
    icon: '📡',
    title: 'Side-Channel Exfiltration',
    desc: 'Sensitive data leaked through timing analysis, token usage patterns, or metadata emissions in agent responses.',
    status: 'unsolved',
    statusText: 'No Solution',
    accent: '#FF3B5C',
  },
  {
    icon: '🎭',
    title: 'Identity Hijacking',
    desc: 'Malicious agents impersonate trusted entities or principals within a swarm to authorize restricted actions.',
    status: 'unsolved',
    statusText: 'No Solution',
    accent: '#FF3B5C',
  },
];

export function renderThreatGrid() {
  const grid = document.getElementById('threat-grid');
  if (!grid) return;

  grid.innerHTML = '';

  THREAT_VECTORS.forEach((v, i) => {
    const card = document.createElement('div');
    card.className = 'threat-card reveal';
    card.style.setProperty('--card-accent', v.accent);
    card.style.transitionDelay = `${i * 60}ms`;

    const header = document.createElement('div');
    header.className = 'threat-card-header';

    const iconSpan = document.createElement('span');
    iconSpan.className = 'threat-icon';
    iconSpan.textContent = v.icon;

    // Index badge — monospace, dim
    const indexSpan = document.createElement('span');
    indexSpan.className = 'threat-index';
    indexSpan.textContent = `#${String(i + 1).padStart(2, '0')}`;

    const statusSpan = document.createElement('span');
    statusSpan.className = `threat-status ${v.status}`;
    statusSpan.textContent = v.statusText;

    header.appendChild(iconSpan);
    header.appendChild(indexSpan);
    header.appendChild(statusSpan);

    const title = document.createElement('h4');
    title.textContent = v.title;

    const desc = document.createElement('p');
    desc.className = 'threat-desc';
    desc.textContent = v.desc;

    card.appendChild(header);
    card.appendChild(title);
    card.appendChild(desc);

    grid.appendChild(card);
  });
}

