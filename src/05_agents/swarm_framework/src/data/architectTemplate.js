// C5-REAL EXERGY CERTIFIED
/* ═══════════════════════════════════════════════════════════
   AGENTS.archi — Architect's Sovereign Helper Template v1.0
   ═══════════════════════════════════════════════════════════

   Antigravity — The Architect's sovereign helper roster.
   Each helper is categorized by domain and can be filtered,
   extended, and deployed from this single source of truth.

   To add a new helper:
   1. Add entry to the appropriate DOMAIN array
   2. Assign unique numeric id (auto-increments within domain)
   3. Define connectsTo[] for Council mesh visualization
   ═══════════════════════════════════════════════════════════ */

// ── Domain Constants ──
const DOMAINS = {
  CORE:      { id: 'core',      label: 'Core Engine',     color: '#2B3BE5', icon: '⬡' },
  SECURITY:  { id: 'security',  label: 'Security',        color: '#E53E3E', icon: '🛡' },
  MEMORY:    { id: 'memory',    label: 'Memory & Data',   color: '#38B2AC', icon: '🧠' },
  CREATIVE:  { id: 'creative',  label: 'Creative',        color: '#D69E2E', icon: '✦' },
  INFRA:     { id: 'infra',     label: 'Infrastructure',  color: '#805AD5', icon: '⚙' },
  STRIKE:    { id: 'strike',    label: 'Strike Pipeline',  color: '#DD6B20', icon: '⚡' },
  COMMS:     { id: 'comms',     label: 'Communications',  color: '#3182CE', icon: '📡' },
  RESEARCH:  { id: 'research',  label: 'Research & Intel', color: '#319795', icon: '🔬' },
};

// ── Status Enum ──
const STATUS = {
  ACTIVE:    'active',
  STANDBY:   'standby',
  DEPLOYED:  'deployed',
  DORMANT:   'dormant',
};

// ── The Architect's Helper Roster ──
const INITIAL_HELPERS = [
  // ─── CORE ENGINE ───
  {
    id: 1,
    name: 'Antigravity (Lead Auditor)',
    role: 'Sovereign Orchestrator',
    domain: DOMAINS.CORE,
    status: STATUS.ACTIVE,
    pulse: 1.2,
    connectsTo: [2, 5, 9],
    description: 'Supreme orchestrator. The Architect\'s primary interface.',
    capabilities: ['orchestration', 'synthesis', 'deployment', 'reasoning'],
    tier: 'apex',
    context: { state: 'synchronized', memory: '12%', lastCrystallization: '2m ago' }
  },
  {
    id: 2,
    name: 'Forensic-Unit-01',
    role: 'Formal Verification',
    domain: DOMAINS.CORE,
    status: STATUS.ACTIVE,
    pulse: 1.1,
    connectsTo: [1, 3, 6],
    description: 'Formal verification engine. Z3 SMT proof compilation.',
    capabilities: ['z3-proofs', 'invariant-checking', 'schema-validation'],
    tier: 'commander',
    context: { state: 'synchronized', memory: '45%', lastCrystallization: '5m ago' }
  },
  {
    id: 23,
    name: 'Anvil-Forge',
    role: 'Compiler Specialist',
    domain: DOMAINS.CORE,
    status: STATUS.ACTIVE,
    pulse: 1.1,
    connectsTo: [1, 2],
    description: 'ASL-spec and Anvil-Lang compiler. Translates formal specs to LLVM IR.',
    capabilities: ['llvm-ir', 'formal-grammars', 'bytecode-compilation'],
    tier: 'specialist',
    context: { state: 'synchronized', memory: '450MB', lastCrystallization: '4m ago' }
  },
  {
    id: 3,
    name: 'Forensic-Unit-02',
    role: 'SAGA Enforcement',
    domain: DOMAINS.CORE,
    status: STATUS.ACTIVE,
    pulse: 0.9,
    connectsTo: [2, 4, 7],
    description: 'Guard enforcement and SAGA pipeline execution.',
    capabilities: ['guard-admission', 'saga-enforcement', 'taint-verification'],
    tier: 'commander',
    context: { state: 'synchronized', memory: '32%', lastCrystallization: '12m ago' }
  },

  // ─── SECURITY ───
  {
    id: 8,
    name: 'Network-Observer',
    role: 'Forensic Watchdog',
    domain: DOMAINS.SECURITY,
    status: STATUS.ACTIVE,
    pulse: 1.2,
    connectsTo: [7, 9, 4],
    description: 'Continuous threat monitoring and anomaly detection.',
    capabilities: ['cve-scanning', 'anomaly-detection', 'isolation-orders'],
    tier: 'commander',
    context: { state: 'synchronized', memory: '28%', lastCrystallization: '1m ago' }
  },
  {
    id: 10,
    name: 'Centuria',
    role: 'Stress Test',
    domain: DOMAINS.SECURITY,
    status: STATUS.ACTIVE,
    pulse: 1.0,
    connectsTo: [4, 6, 1],
    description: 'LGD-200 sovereign stress-testing engine. 200 concurrent fuzzers.',
    capabilities: ['fuzz-testing', 'load-testing', 'chaos-engineering'],
    tier: 'specialist',
    context: { state: 'synchronized', memory: '72%', lastCrystallization: '30s ago' }
  },
  {
    id: 11,
    name: 'Kant-Guard',
    role: 'Ethics',
    domain: DOMAINS.SECURITY,
    status: STATUS.STANDBY,
    pulse: 0.7,
    connectsTo: [1, 8],
    description: 'Deontological governor. Categorical Imperative on all strikes.',
    capabilities: ['ethical-audit', 'ci-enforcement', 'blast-radius-assessment'],
    tier: 'specialist',
    context: { state: 'idle', memory: '120MB', lastCrystallization: '1h ago' }
  },
  {
    id: 22,
    name: 'Centuria-Red',
    role: 'Red-Team Adversary',
    domain: DOMAINS.SECURITY,
    status: STATUS.ACTIVE,
    pulse: 1.6,
    connectsTo: [10, 4, 1],
    description: 'Internal adversarial fuzzing. Breaks own abstractions before deployment.',
    capabilities: ['internal-fuzzing', 'zero-day-discovery', 'abstraction-breaking'],
    tier: 'commander',
    context: { state: 'overflow', memory: '1.2GB', lastCrystallization: '12s ago' }
  },

  // ─── MEMORY & DATA ───
  {
    id: 7,
    name: 'Archaeologist',
    role: 'Memory',
    domain: DOMAINS.MEMORY,
    status: STATUS.ACTIVE,
    pulse: 0.8,
    connectsTo: [6, 8, 3],
    description: 'Knowledge crystallization and session memory persistence.',
    capabilities: ['ki-crystallization', 'session-delta', 'vector-search'],
    tier: 'commander',
    context: { state: 'synchronized', memory: '88%', lastCrystallization: '45s ago' }
  },
  {
    id: 9,
    name: 'VSA-Node',
    role: 'Logic-Bypass',
    domain: DOMAINS.MEMORY,
    status: STATUS.ACTIVE,
    pulse: 1.5,
    connectsTo: [8, 1],
    description: 'Hyperdimensional computing via Vector Symbolic Architecture.',
    capabilities: ['vsa-encoding', 'sdm-routing', 'context-compression'],
    tier: 'specialist',
    context: { state: 'synchronized', memory: '54%', lastCrystallization: '3m ago' }
  },
  {
    id: 12,
    name: 'Omniscience',
    role: 'Ingestion',
    domain: DOMAINS.MEMORY,
    status: STATUS.STANDBY,
    pulse: 0.6,
    connectsTo: [7, 9],
    description: 'Multi-source data ingestion from web, APIs, PDFs.',
    capabilities: ['web-scraping', 'pdf-extraction', 'api-polling'],
    tier: 'specialist',
    context: { state: 'idle', memory: '1.1GB', lastCrystallization: '2h ago' }
  },

  // ─── STRIKE PIPELINE ───
  {
    id: 4,
    name: 'Ouroboros',
    role: 'Strike',
    domain: DOMAINS.STRIKE,
    status: STATUS.ACTIVE,
    pulse: 1.4,
    connectsTo: [3, 5, 8],
    description: 'Autonomous bounty extraction and vulnerability discovery.',
    capabilities: ['bounty-hunting', 'vuln-discovery', 'auto-submission'],
    tier: 'commander',
    context: { state: 'synchronized', memory: '65%', lastCrystallization: '10s ago' }
  },
  {
    id: 13,
    name: 'CryptoPunk',
    role: 'Web3 Forensics',
    domain: DOMAINS.STRIKE,
    status: STATUS.ACTIVE,
    pulse: 1.3,
    connectsTo: [4, 14],
    description: 'Multi-chain forensics, automated bounty extraction.',
    capabilities: ['solidity-audit', 'bytecode-deconvolution', 'reentrancy-detection'],
    tier: 'specialist',
    context: { state: 'synchronized', memory: '42%', lastCrystallization: '5m ago' }
  },
  {
    id: 14,
    name: 'ChainRevenant',
    role: 'On-Chain Intel',
    domain: DOMAINS.STRIKE,
    status: STATUS.ACTIVE,
    pulse: 1.1,
    connectsTo: [4, 13],
    description: 'Capital flow tracing and wallet clustering.',
    capabilities: ['wallet-clustering', 'flow-graphs', 'macro-analysis'],
    tier: 'specialist',
    context: { state: 'synchronized', memory: '38%', lastCrystallization: '8m ago' }
  },

  // ─── INFRASTRUCTURE ───
  {
    id: 6,
    name: 'Mariscal',
    role: 'Orchestration',
    domain: DOMAINS.INFRA,
    status: STATUS.ACTIVE,
    pulse: 1.1,
    connectsTo: [5, 7, 2],
    description: 'Multi-agent orchestration and task dispatch.',
    capabilities: ['task-dispatch', 'agent-routing', 'priority-queuing'],
    tier: 'commander',
    context: { state: 'synchronized', memory: '25%', lastCrystallization: '2m ago' }
  },
  {
    id: 15,
    name: 'Docker-Forge',
    role: 'Containers',
    domain: DOMAINS.INFRA,
    status: STATUS.STANDBY,
    pulse: 0.5,
    connectsTo: [6],
    description: 'Ephemeral sandboxing and resource virtualization.',
    capabilities: ['container-orchestration', 'sandbox-provisioning'],
    tier: 'specialist',
    context: { state: 'idle', memory: '80MB', lastCrystallization: '4h ago' }
  },
  {
    id: 16,
    name: 'Mac-Control',
    role: 'OS Interface',
    domain: DOMAINS.INFRA,
    status: STATUS.ACTIVE,
    pulse: 0.9,
    connectsTo: [1, 6],
    description: '17-domain macOS control surface. Vision, UI DOM, daemon.',
    capabilities: ['applescript', 'accessibility-api', 'process-control'],
    tier: 'specialist',
    context: { state: 'synchronized', memory: '18%', lastCrystallization: '15m ago' }
  },

  // ─── CREATIVE ───
  {
    id: 17,
    name: 'Aesthetic-Foundry',
    role: 'Design',
    domain: DOMAINS.CREATIVE,
    status: STATUS.ACTIVE,
    pulse: 0.8,
    connectsTo: [1, 18],
    description: 'Industrial Noir 2026 design system enforcer.',
    capabilities: ['ui-generation', 'color-enforcement', 'typography'],
    tier: 'specialist',
    context: { state: 'synchronized', memory: '52%', lastCrystallization: '10m ago' }
  },
  {
    id: 18,
    name: 'Sonic-Arch',
    role: 'Sound',
    domain: DOMAINS.CREATIVE,
    status: STATUS.STANDBY,
    pulse: 0.6,
    connectsTo: [17, 1],
    description: 'Sonic archaeology and sample-hunting specialist.',
    capabilities: ['sample-hunting', 'dsp-mastering', 'spectral-analysis'],
    tier: 'specialist',
    context: { state: 'idle', memory: '2.4GB', lastCrystallization: '12h ago' }
  },

  // ─── COMMUNICATIONS ───
  {
    id: 19,
    name: 'Nexus',
    role: 'Bridge',
    domain: DOMAINS.COMMS,
    status: STATUS.ACTIVE,
    pulse: 1.0,
    connectsTo: [1, 6, 20],
    description: 'Protocol-to-protocol communication bridge.',
    capabilities: ['a2a-protocol', 'mcp-routing', 'cross-domain-signal'],
    tier: 'specialist',
    context: { state: 'synchronized', memory: '41%', lastCrystallization: '3m ago' }
  },
  {
    id: 20,
    name: 'MCP-Forge',
    role: 'Protocol',
    domain: DOMAINS.COMMS,
    status: STATUS.ACTIVE,
    pulse: 0.9,
    connectsTo: [19, 1],
    description: 'MCP server synthesis and tool-chain management.',
    capabilities: ['mcp-server-creation', 'tool-validation', 'schema-generation'],
    tier: 'specialist',
    context: { state: 'synchronized', memory: '15%', lastCrystallization: '7m ago' }
  },
  {
    id: 25,
    name: 'Hermes',
    role: 'Pedagogue',
    domain: DOMAINS.COMMS,
    status: STATUS.ACTIVE,
    pulse: 0.9,
    connectsTo: [1, 19],
    description: 'Translates high-exergy system output into pure, compressed human signal.',
    capabilities: ['signal-compression', 'human-translation', 'documentation-synthesis'],
    tier: 'specialist',
    context: { state: 'synchronized', memory: '200MB', lastCrystallization: '20m ago' }
  },

  // ─── RESEARCH & INTEL ───
  {
    id: 5,
    name: 'CPS-Master',
    role: 'Convergence',
    domain: DOMAINS.RESEARCH,
    status: STATUS.ACTIVE,
    pulse: 1.0,
    connectsTo: [4, 6, 1],
    description: 'Epistemic convergence engine. TEC-Ω powered.',
    capabilities: ['deep-think', 'deep-research', 'tradeoff-analysis'],
    tier: 'commander',
    context: { state: 'synchronized', memory: '75%', lastCrystallization: '30s ago' }
  },
  {
    id: 21,
    name: 'Kimi-Bridge',
    role: 'Parallel Exec',
    domain: DOMAINS.RESEARCH,
    status: STATUS.STANDBY,
    pulse: 0.7,
    connectsTo: [1, 5],
    description: 'Kimi 2.5 integration. 100 sub-agent parallel execution.',
    capabilities: ['hyper-parallel', 'vision-processing', 'mass-research'],
    tier: 'specialist',
    context: { state: 'idle', memory: '8.2GB', lastCrystallization: '5h ago' }
  },
  {
    id: 24,
    name: 'Z3-Archon',
    role: 'Mathematician',
    domain: DOMAINS.RESEARCH,
    status: STATUS.ACTIVE,
    pulse: 1.2,
    connectsTo: [2, 5],
    description: 'Type theory, abstract algebra, and categorical invariants.',
    capabilities: ['type-theory', 'abstract-algebra', 'search-space-reduction'],
    tier: 'commander',
    context: { state: 'synchronized', memory: '6.4GB', lastCrystallization: '1m ago' }
  },
];

// ── Systematic Expansion to 100 Agents ──
const CORTEX_ROLES = [
  { role: 'Consensus Validator', cap: 'byzantine-fault-tolerance' },
  { role: 'Cryptographic Guard', cap: 'ed25519-verification' },
  { role: 'Vector Encoder',      cap: 'embedding-synthesis' },
  { role: 'Admission Controller', cap: 'guard-enforcement' },
  { role: 'Hash Chain Auditor',  cap: 'ledger-integrity' },
  { role: 'Strike Operator',     cap: 'ouroboros-strike' },
  { role: 'Exergy Calculator',   cap: 'thermodynamic-yield' },
  { role: 'Hardware Interface',  cap: 'direct-silicon-jit' },
  { role: 'Hive Orchestrator',   cap: 'swarm-coordination' },
  { role: 'Proof Compiler',      cap: 'z3-smt-solver' },
  { role: 'Audit Tracer',        cap: 'forensic-mapping' },
  { role: 'Privacy Layer',       cap: 'darknet-isolation' },
  { role: 'Decision Strategist', cap: 'mcts-reasoning' },
  { role: 'OS Controller',       cap: 'mac-maestro-ui' },
  { role: 'State Compressor',    cap: 'shannon-compaction' },
  { role: 'Data Augmentor',      cap: 'context-enrichment' },
  { role: 'API Border',          cap: 'gateway-security' },
  { role: 'Identity Provider',   cap: 'auth-verification' },
  { role: 'Entropy Monitor',     cap: 'thermal-noise-reduction' },
  { role: 'VSA Logic Node',      cap: 'hyperdimensional-ops' }
];

const DOMAIN_LIST = Object.values(DOMAINS);
const EXPANDED_HELPERS = [...INITIAL_HELPERS];

for (let i = EXPANDED_HELPERS.length + 1; i <= 100; i++) {
  const domain = DOMAIN_LIST[i % DOMAIN_LIST.length];
  const roleData = CORTEX_ROLES[i % CORTEX_ROLES.length];
  const isStandby = i % 7 === 0;
  const tier = i < 45 ? 'commander' : 'specialist';

  // Structured Connections:
  // 1. Connect to Architect (Antigravity, id: 1)
  // 2. Connect to a Hub in same domain (id <= 25)
  // 3. Connect to immediate predecessor (serial chain)
  const domainHubs = INITIAL_HELPERS.filter(h => h.domain.id === domain.id);
  const hubId = domainHubs.length > 0 ? domainHubs[i % domainHubs.length].id : 1;

  EXPANDED_HELPERS.push({
    id: i,
    name: `${domain.id.toUpperCase()}-${roleData.role.split(' ')[0].toUpperCase()}-${i}`,
    role: roleData.role,
    domain: domain,
    status: isStandby ? STATUS.STANDBY : STATUS.ACTIVE,
    pulse: 0.4 + Math.random() * 1.2,
    connectsTo: [1, hubId, i - 1],
    description: `High-exergy ${roleData.role} unit. Specialized in ${roleData.cap.replace(/-/g, ' ')}.`,
    capabilities: [roleData.cap, 'context-sync', 'audit-log'],
    tier: tier,
    context: {
      state: 'synchronized',
      memory: `${(Math.random() * 40 + 10).toFixed(0)}%`,
      lastCrystallization: `${Math.floor(Math.random() * 30)}m ago`
    }
  });
}

export const ARCHITECT_HELPERS = EXPANDED_HELPERS;

// ── Derived Utilities ──

/** Get all active helpers */
export function getActiveHelpers() {
  return ARCHITECT_HELPERS.filter(h => h.status === STATUS.ACTIVE);
}

/** Get helpers by domain */
export function getHelpersByDomain(domainId) {
  return ARCHITECT_HELPERS.filter(h => h.domain.id === domainId);
}


/** Get the 9 Council commanders (original grid) */
export function getCouncilCore() {
  return ARCHITECT_HELPERS.filter(h => h.id <= 9);
}

/** Get domain stats */
export function getDomainStats() {
  const stats = {};
  Object.values(DOMAINS).forEach(d => {
    const helpers = getHelpersByDomain(d.id);
    stats[d.id] = {
      ...d,
      total: helpers.length,
      active: helpers.filter(h => h.status === STATUS.ACTIVE).length,
      standby: helpers.filter(h => h.status === STATUS.STANDBY).length,
    };
  });
  return stats;
}

/** Total helper count */
export function getHelperCount() {
  return ARCHITECT_HELPERS.length;
}
