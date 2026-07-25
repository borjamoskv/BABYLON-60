// C5-REAL EXERGY CERTIFIED
export interface DatabaseTable {
  name: string;
  rows: number;
  columns: { name: string; type: string; pk: boolean }[];
}

export interface SwarmNode {
  id: string;
  name: string;
  role: string;
  status: 'synced' | 'voting' | 'idle' | 'fault';
  latency: number;
  lamport: number;
  hash: string;
  x: number;
  y: number;
}


export const INITIAL_SWARM: SwarmNode[] = [
  { id: 'node-0', name: 'MOSKV-1 APEX (Leader)', role: 'Leader / Proposer', status: 'synced', latency: 0.4, lamport: 104, hash: '7a3f95b...e9', x: 200, y: 120 },
  { id: 'node-1', name: 'Worker Alpha (Rust Core)', role: 'Execution Transducer', status: 'synced', latency: 1.2, lamport: 104, hash: '8a339ce...b5', x: 100, y: 220 },
  { id: 'node-2', name: 'Worker Beta (Prolog Engine)', role: 'Unification Verifier', status: 'synced', latency: 1.8, lamport: 104, hash: '9b440df...c6', x: 300, y: 220 },
  { id: 'node-3', name: 'Worker Gamma (Python Inf)', role: 'Free Energy Minimizer', status: 'synced', latency: 2.1, lamport: 104, hash: '1c551ea...d7', x: 80, y: 340 },
  { id: 'node-4', name: 'Worker Delta (Go Transducer)', role: 'IPC Buffer & WAL', status: 'voting', latency: 3.4, lamport: 104, hash: '2d662fb...e8', x: 320, y: 340 }
];

export const MOCK_TABLES: DatabaseTable[] = [
  {
    name: 'ledger_entries',
    rows: 14502,
    columns: [
      { name: 'seq', type: 'INTEGER', pk: true },
      { name: 'entry_hash', type: 'VARCHAR(64)', pk: false },
      { name: 'lamport_t', type: 'INTEGER', pk: false },
      { name: 'created_at', type: 'TIMESTAMP', pk: false },
      { name: 'payload', type: 'TEXT', pk: false }
    ]
  },
  {
    name: 'swarm_nodes',
    rows: 5,
    columns: [
      { name: 'node_id', type: 'VARCHAR(36)', pk: true },
      { name: 'role', type: 'VARCHAR(50)', pk: false },
      { name: 'status', type: 'VARCHAR(20)', pk: false },
      { name: 'last_seen', type: 'TIMESTAMP', pk: false }
    ]
  },
  {
    name: 'epistemic_invariants',
    rows: 65,
    columns: [
      { name: 'code', type: 'VARCHAR(10)', pk: true },
      { name: 'title', type: 'VARCHAR(100)', pk: false },
      { name: 'reality_level', type: 'VARCHAR(10)', pk: false },
      { name: 'proof_hash', type: 'VARCHAR(64)', pk: false }
    ]
  }
];
