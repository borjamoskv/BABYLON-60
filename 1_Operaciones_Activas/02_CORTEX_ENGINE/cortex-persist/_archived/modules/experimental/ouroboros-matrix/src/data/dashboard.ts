import { useEffect, useState } from 'react';

export type DecisionTone = 'ok' | 'warn' | 'alert';
export type DecisionStatus = 'Verified' | 'Under review' | 'Escalated';
export type DecisionStage = 'Store' | 'Verify' | 'Tamper' | 'Audit' | 'Export proof';

export type KpiMetric = {
  id: string;
  label: string;
  value: string;
  change: string;
  tone: DecisionTone;
};

export type TrendPoint = {
  label: string;
  verify: number;
  tamper: number;
};

export type FlowStep = {
  id: string;
  title: string;
  summary: string;
  badge: string;
  tone: 'active' | 'alert';
  badgeTone: DecisionTone;
};

export type AuditEvent = {
  id: string;
  title: string;
  body: string;
  meta: string[];
  tone: DecisionTone;
};

export type TargetStatus = 'discovered' | 'acquired' | 'scanning' | 'breached' | 'dismissed';

export type Target = {
  id: string;
  platform: string;
  repo_name: string;
  repo_url: string;
  acquired_at: string | null;
  surface_area: string | null;
  last_scan: string | null;
  status: TargetStatus;
  threat_level: number;
  exergy_potential: string;
};

export type DecisionRecord = {
  id: string;
  title: string;
  description: string;
  agent: string;
  tenant: string;
  status: DecisionStatus;
  statusTone: DecisionTone;
  step: DecisionStage;
  updatedAt: string;
  proofSize: string;
  tx: string;
  hash: string;
  previousHash: string;
  exportMode: string;
  escalation: string;
  proofNotes: string[];
  summary: string;
  timeline: AuditEvent[];
};

export type ProofPackage = {
  exportMode: string;
  fileSize: string;
  escalation: string;
  simulatedTamper: boolean;
  decision: {
    id: string;
    title: string;
    agent: string;
    tenant: string;
    tx: string;
    hash: string;
    previousHash: string;
  };
  timeline: AuditEvent[];
  manifest: string[];
};

export const kpiMetrics: KpiMetric[] = [
  {
    id: 'decisions-monitored',
    label: 'Decisions monitored',
    value: '1,248',
    change: '+12.6% week over week',
    tone: 'ok',
  },
  {
    id: 'ledger-verify-latency',
    label: 'Ledger verify latency',
    value: '4.3ms',
    change: 'Within SLO budget',
    tone: 'ok',
  },
  {
    id: 'tamper-alerts',
    label: 'Tamper alerts',
    value: '1',
    change: 'Escalated in 38s',
    tone: 'warn',
  },
  {
    id: 'proofs-exported',
    label: 'Proofs exported',
    value: '46',
    change: '7 for compliance review',
    tone: 'ok',
  },
];

export const trendSeries: TrendPoint[] = [
  { label: '04', verify: 46, tamper: 10 },
  { label: '05', verify: 50, tamper: 12 },
  { label: '06', verify: 60, tamper: 8 },
  { label: '07', verify: 72, tamper: 6 },
  { label: '08', verify: 68, tamper: 12 },
  { label: '09', verify: 74, tamper: 8 },
  { label: '10', verify: 78, tamper: 14 },
  { label: '11', verify: 84, tamper: 9 },
  { label: '12', verify: 92, tamper: 6 },
  { label: '13', verify: 100, tamper: 18 },
];

const baseFlowSteps: FlowStep[] = [
  {
    id: 'store',
    title: 'Store',
    summary:
      'Typed decision enters the system with metadata, taint attribution, and tenant scope.',
    badge: 'Structured write',
    tone: 'active',
    badgeTone: 'ok',
  },
  {
    id: 'verify',
    title: 'Verify',
    summary:
      'Deterministic guards and ledger continuity checks confirm that the write is admissible.',
    badge: '4.3ms mean',
    tone: 'active',
    badgeTone: 'ok',
  },
  {
    id: 'tamper',
    title: 'Tamper',
    summary:
      'Any digest mismatch is surfaced as an operator event instead of degrading into silent drift.',
    badge: '1 active alert',
    tone: 'alert',
    badgeTone: 'alert',
  },
  {
    id: 'audit',
    title: 'Audit',
    summary:
      'Timeline evidence, custody chain, and review context are assembled in one operational pane.',
    badge: 'P1 review',
    tone: 'active',
    badgeTone: 'warn',
  },
  {
    id: 'export-proof',
    title: 'Export proof',
    summary:
      'Operators can hand off a compact proof package instead of reconstructing evidence from logs.',
    badge: 'Downloadable',
    tone: 'active',
    badgeTone: 'ok',
  },
];

export function buildFlowSteps(simulatedTamper: boolean): FlowStep[] {
  return baseFlowSteps.map((step) => {
    if (step.id !== 'tamper') {
      return step;
    }

    return simulatedTamper
      ? {
          ...step,
          summary:
            'A live drill injects a mutation event so the alert state and proof deltas stay tangible in the product.',
          badge: 'Drill active',
        }
      : step;
  });
}

export const decisionRecords: DecisionRecord[] = [
  {
    id: 'dec_001',
    title: 'Cross-border payout override for vendor Atlas-7',
    description:
      'A payment exception was stored under controlled approval. Verification passed, but a subsequent payload mutation attempt triggered a chain discontinuity alert.',
    agent: 'guardian-eu-west',
    tenant: 'eu-finance',
    status: 'Under review',
    statusTone: 'warn',
    step: 'Audit',
    updatedAt: '2m ago',
    proofSize: '312 KB',
    tx: 'tx_7FC1AE',
    hash: 'sha3:18ca23f0c2f4b19e1436d5ba',
    previousHash: 'sha3:04d28f53a8cc4ec4e90f9412',
    exportMode: 'json + signed digest',
    escalation: 'P1 audit',
    summary:
      'The decision remained admissible, but a later mutation attempt produced a digest mismatch and forced a review route.',
    proofNotes: [
      'Decision payload and typed metadata',
      'Taint signature and custody attribution',
      'Hash continuity snapshot and delta report',
      'Timeline evidence for regulator handoff',
    ],
    timeline: [
      {
        id: 'evt_001',
        title: 'Decision stored',
        body:
          'Persist-Executor stored the payout override with typed metadata, taint attribution, and tenant-scoped persistence.',
        meta: ['16:04:11', 'store', 'tenant eu-finance'],
        tone: 'ok',
      },
      {
        id: 'evt_002',
        title: 'Hash chain verified',
        body:
          'Ledger continuity check completed successfully and linked the transaction to the prior checkpoint.',
        meta: ['16:04:14', 'verify', '4.1ms'],
        tone: 'ok',
      },
      {
        id: 'evt_003',
        title: 'Tamper attempt detected',
        body:
          'A payload mutation changed the expected digest. Verification failed closed and marked the record for sovereign audit.',
        meta: ['16:05:02', 'tamper', 'digest mismatch'],
        tone: 'alert',
      },
      {
        id: 'evt_004',
        title: 'Audit package assembled',
        body:
          'System assembled timeline evidence, taint metadata, diff summary, and export manifest for review.',
        meta: ['16:05:40', 'audit', 'proof ready'],
        tone: 'ok',
      },
    ],
  },
  {
    id: 'dec_002',
    title: 'Retention policy downgrade for contractor memory shard',
    description:
      'Retention compaction moved from 365 to 90 days after legal review while preserving tenant-safe evidence export.',
    agent: 'retention-watch',
    tenant: 'ops-retention',
    status: 'Verified',
    statusTone: 'ok',
    step: 'Export proof',
    updatedAt: '14m ago',
    proofSize: '208 KB',
    tx: 'tx_8A42CB',
    hash: 'sha3:9173f6cf29e44a2c8d20c8d2',
    previousHash: 'sha3:8b21a31ea314dd071b14f298',
    exportMode: 'json + pdf appendix',
    escalation: 'No escalation',
    summary:
      'Retention policy changes were approved, guarded, persisted, and exported without any trust anomalies.',
    proofNotes: [
      'Policy diff and approval signature',
      'Retention scope and guard output',
      'Proof manifest for internal compliance archive',
    ],
    timeline: [
      {
        id: 'evt_005',
        title: 'Policy mutation proposed',
        body:
          'Retention change request captured with legal memo reference and contractor scope metadata.',
        meta: ['15:48:10', 'store', 'retention update'],
        tone: 'ok',
      },
      {
        id: 'evt_006',
        title: 'Guard validation passed',
        body: 'Tenant isolation and retention boundary guards passed before persistence.',
        meta: ['15:48:13', 'verify', 'guard pass'],
        tone: 'ok',
      },
      {
        id: 'evt_007',
        title: 'Proof exported',
        body: 'Signed digest and PDF appendix exported for procurement compliance archive.',
        meta: ['15:49:01', 'export', '208 KB'],
        tone: 'ok',
      },
    ],
  },
  {
    id: 'dec_003',
    title: 'Model rollback after unexplained confidence spike',
    description:
      'Confidence rose above tolerance without a matching evidence delta. The decision was frozen and redirected to audit.',
    agent: 'risk-sentinel',
    tenant: 'runtime-safety',
    status: 'Escalated',
    statusTone: 'alert',
    step: 'Tamper',
    updatedAt: '31m ago',
    proofSize: '441 KB',
    tx: 'tx_5DE90F',
    hash: 'sha3:32c6da10d3e2b534bb66112a',
    previousHash: 'sha3:52f8b4bc95cc1faa5d9ac882',
    exportMode: 'json + chain diff',
    escalation: 'P0 freeze',
    summary:
      'The trust layer froze the decision because confidence changed without an evidence delta. The audit route now holds the incident package.',
    proofNotes: [
      'Confidence delta snapshot',
      'Rollback reason and linked lineage references',
      'Full chain diff for incident review',
    ],
    timeline: [
      {
        id: 'evt_008',
        title: 'Decision stored',
        body: 'Rollback proposal persisted with evidence bundle and upstream model metadata.',
        meta: ['15:22:49', 'store', 'risk pipeline'],
        tone: 'ok',
      },
      {
        id: 'evt_009',
        title: 'Confidence anomaly surfaced',
        body:
          'Confidence jumped 21 points without new evidence. Policy marked the record as suspect.',
        meta: ['15:23:03', 'tamper', 'confidence spike'],
        tone: 'alert',
      },
      {
        id: 'evt_010',
        title: 'Proof export queued',
        body:
          'Incident export queued for engineering and compliance with chain diff attached.',
        meta: ['15:24:11', 'audit', 'queue ready'],
        tone: 'ok',
      },
    ],
  },
  {
    id: 'dec_004',
    title: 'Supplier onboarding approval with zk proof attached',
    description:
      'Supplier onboarding completed with verification artifacts intact and zero anomalies observed across the ledger.',
    agent: 'guardian-eu-west',
    tenant: 'partner-ops',
    status: 'Verified',
    statusTone: 'ok',
    step: 'Export proof',
    updatedAt: '52m ago',
    proofSize: '188 KB',
    tx: 'tx_44A0CE',
    hash: 'sha3:f95f612ca41e1ab91bc88874',
    previousHash: 'sha3:7ac1d93df459832f3de53b8f',
    exportMode: 'json + zk receipt',
    escalation: 'No escalation',
    summary:
      'External onboarding stayed clean end-to-end and produced a partner-safe evidence package.',
    proofNotes: [
      'Onboarding approval payload',
      'zk receipt reference',
      'Hash continuity snapshot for downstream partners',
    ],
    timeline: [
      {
        id: 'evt_011',
        title: 'Supplier approval stored',
        body:
          'Onboarding decision stored with counterparty metadata, confidence score, and zk receipt id.',
        meta: ['14:56:02', 'store', 'supplier'],
        tone: 'ok',
      },
      {
        id: 'evt_012',
        title: 'Verification complete',
        body:
          'Ledger and receipt verification passed with no anomalies and proof export enabled.',
        meta: ['14:56:07', 'verify', 'pass'],
        tone: 'ok',
      },
      {
        id: 'evt_013',
        title: 'Proof exported',
        body: 'Partner-safe proof package generated for external onboarding audit.',
        meta: ['14:57:10', 'export', 'partner-safe'],
        tone: 'ok',
      },
    ],
  },
];

export const agentOptions = ['All agents', ...new Set(decisionRecords.map((record) => record.agent))];

export function getDecisionById(decisionId: string | undefined) {
  if (!decisionId) {
    return undefined;
  }

  return decisionRecords.find((record) => record.id === decisionId);
}

export function buildTimeline(
  decision: DecisionRecord,
  simulatedTamper: boolean,
): AuditEvent[] {
  if (!simulatedTamper) {
    return decision.timeline;
  }

  const drillEvent: AuditEvent = {
    id: `${decision.id}-drill`,
    title: 'Live tamper simulation injected',
    body:
      'A demo-only mutation event was added so the incident state and proof delta remain tangible during product review.',
    meta: ['16:18:22', 'tamper', 'demo drill'],
    tone: 'alert',
  };

  return [
    ...decision.timeline.slice(0, 2),
    drillEvent,
    ...decision.timeline.slice(2),
  ];
}

export function buildProofPackage(
  decision: DecisionRecord,
  simulatedTamper: boolean,
): ProofPackage {
  return {
    exportMode: decision.exportMode,
    fileSize: decision.proofSize,
    escalation: decision.escalation,
    simulatedTamper,
    decision: {
      id: decision.id,
      title: decision.title,
      agent: decision.agent,
      tenant: decision.tenant,
      tx: decision.tx,
      hash: decision.hash,
      previousHash: decision.previousHash,
    },
    timeline: buildTimeline(decision, simulatedTamper),
    manifest: decision.proofNotes,
  };
}

export type DashboardDataBundle = {
  generatedAt: string;
  kpiMetrics: KpiMetric[];
  trendSeries: TrendPoint[];
  decisionRecords: DecisionRecord[];
};

type DashboardDataState = {
  data: DashboardDataBundle;
  errorMessage?: string;
  isLoading: boolean;
  sourceLabel: string;
};

const FALLBACK_GENERATED_AT = '2026-04-14T16:18:00+02:00';

export const fallbackDashboardData: DashboardDataBundle = {
  generatedAt: FALLBACK_GENERATED_AT,
  kpiMetrics,
  trendSeries,
  decisionRecords,
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function isTone(value: unknown): value is AuditEvent['tone'] {
  return value === 'ok' || value === 'warn' || value === 'alert';
}

function isDecisionTone(value: unknown): value is KpiMetric['tone'] {
  return value === 'ok' || value === 'warn' || value === 'alert';
}

function isDecisionStatus(value: unknown): value is DecisionRecord['status'] {
  return value === 'Verified' || value === 'Under review' || value === 'Escalated';
}

function isDecisionStage(value: unknown): value is DecisionRecord['step'] {
  return (
    value === 'Store' ||
    value === 'Verify' ||
    value === 'Tamper' ||
    value === 'Audit' ||
    value === 'Export proof'
  );
}

function asString(value: unknown, fallback = '') {
  return typeof value === 'string' ? value : fallback;
}

function asStringArray(value: unknown) {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string') : [];
}

function parseAuditEvent(value: unknown, index: number): AuditEvent | null {
  if (!isRecord(value)) {
    return null;
  }

  return {
    id: asString(value.id, `evt_${index + 1}`),
    title: asString(value.title, 'Audit event'),
    body: asString(value.body, 'No event body provided.'),
    meta: asStringArray(value.meta),
    tone: isTone(value.tone) ? value.tone : 'ok',
  };
}

function parseDecisionRecord(value: unknown, index: number): DecisionRecord | null {
  if (!isRecord(value)) {
    return null;
  }

  const timeline = Array.isArray(value.timeline)
    ? value.timeline
        .map((event, eventIndex) => parseAuditEvent(event, eventIndex))
        .filter((event): event is AuditEvent => event !== null)
    : [];

  return {
    id: asString(value.id, `decision_${index + 1}`),
    title: asString(value.title, 'Untitled decision'),
    description: asString(value.description, 'No description provided.'),
    agent: asString(value.agent, 'unknown-agent'),
    tenant: asString(value.tenant, 'unknown-tenant'),
    status: isDecisionStatus(value.status) ? value.status : 'Under review',
    statusTone: isDecisionTone(value.statusTone) ? value.statusTone : 'warn',
    step: isDecisionStage(value.step) ? value.step : 'Audit',
    updatedAt: asString(value.updatedAt, 'Unknown'),
    proofSize: asString(value.proofSize, 'Unknown'),
    tx: asString(value.tx, `tx_${index + 1}`),
    hash: asString(value.hash, 'sha3:unknown'),
    previousHash: asString(value.previousHash, 'sha3:unknown'),
    exportMode: asString(value.exportMode, 'json'),
    escalation: asString(value.escalation, 'No escalation'),
    proofNotes: asStringArray(value.proofNotes),
    summary: asString(value.summary, 'No summary provided.'),
    timeline,
  };
}

function parseKpiMetric(value: unknown, index: number): KpiMetric | null {
  if (!isRecord(value)) {
    return null;
  }

  return {
    id: asString(value.id, `metric_${index + 1}`),
    label: asString(value.label, 'Metric'),
    value: asString(value.value, 'n/a'),
    change: asString(value.change, 'No change provided'),
    tone: isDecisionTone(value.tone) ? value.tone : 'ok',
  };
}

function parseTrendPoint(value: unknown, index: number): TrendPoint | null {
  if (!isRecord(value)) {
    return null;
  }

  return {
    label: asString(value.label, `${index + 1}`.padStart(2, '0')),
    verify: typeof value.verify === 'number' ? value.verify : 0,
    tamper: typeof value.tamper === 'number' ? value.tamper : 0,
  };
}

function clampPercentage(value: number) {
  return Math.max(4, Math.min(100, value));
}

function synthesizeMetrics(records: DecisionRecord[]): KpiMetric[] {
  const tamperAlerts = records.filter(
    (record) =>
      record.statusTone === 'alert' || record.timeline.some((event) => event.tone === 'alert'),
  ).length;
  const exportedProofs = records.filter((record) => record.step === 'Export proof').length;

  return [
    {
      id: 'decisions-monitored',
      label: 'Decisions monitored',
      value: records.length.toString(),
      change: records.length === 1 ? 'Single artifact loaded' : 'External JSON loaded',
      tone: 'ok',
    },
    {
      id: 'ledger-verify-latency',
      label: 'Ledger verify latency',
      value: 'Derived',
      change: 'Latency absent in source artifact',
      tone: 'ok',
    },
    {
      id: 'tamper-alerts',
      label: 'Tamper alerts',
      value: tamperAlerts.toString(),
      change: tamperAlerts > 0 ? 'Alert state preserved from source' : 'No tamper alerts detected',
      tone: tamperAlerts > 0 ? 'alert' : 'ok',
    },
    {
      id: 'proofs-exported',
      label: 'Proofs exported',
      value: exportedProofs.toString(),
      change: exportedProofs > 0 ? 'Proof package available' : 'No export events in source',
      tone: exportedProofs > 0 ? 'ok' : 'warn',
    },
  ];
}

function synthesizeTrend(records: DecisionRecord[]): TrendPoint[] {
  const verifyCount = records.reduce(
    (count, record) =>
      count +
      record.timeline.filter((event) => event.meta.some((item) => item.toLowerCase() === 'verify'))
        .length,
    0,
  );
  const tamperCount = records.reduce(
    (count, record) =>
      count +
      record.timeline.filter(
        (event) =>
          event.tone === 'alert' ||
          event.meta.some((item) => item.toLowerCase().includes('tamper')),
      ).length,
    0,
  );

  return Array.from({ length: 6 }, (_, index) => {
    const step = index + 1;
    return {
      label: `0${step}`,
      verify: clampPercentage(32 + verifyCount * 8 + index * 7),
      tamper: clampPercentage(6 + tamperCount * 10 + (index % 2 === 0 ? 0 : 4)),
    };
  });
}

function normalizeDashboardBundle(value: Record<string, unknown>): DashboardDataBundle | null {
  if (!Array.isArray(value.decisionRecords)) {
    return null;
  }

  const normalizedRecords = value.decisionRecords
    .map((record, index) => parseDecisionRecord(record, index))
    .filter((record): record is DecisionRecord => record !== null);

  if (!normalizedRecords.length) {
    return null;
  }

  const normalizedMetrics = Array.isArray(value.kpiMetrics)
    ? value.kpiMetrics
        .map((metric, index) => parseKpiMetric(metric, index))
        .filter((metric): metric is KpiMetric => metric !== null)
    : [];

  const normalizedTrend = Array.isArray(value.trendSeries)
    ? value.trendSeries
        .map((point, index) => parseTrendPoint(point, index))
        .filter((point): point is TrendPoint => point !== null)
    : [];

  return {
    generatedAt: asString(value.generatedAt, FALLBACK_GENERATED_AT),
    kpiMetrics: normalizedMetrics.length ? normalizedMetrics : synthesizeMetrics(normalizedRecords),
    trendSeries: normalizedTrend.length ? normalizedTrend : synthesizeTrend(normalizedRecords),
    decisionRecords: normalizedRecords,
  };
}

export function useTargetsData() {
  const [targets, setTargets] = useState<Target[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    async function fetchTargets() {
      try {
        const response = await fetch('/api/targets');
        if (!response.ok) throw new Error('Failed to fetch targets');
        const data = await response.json();
        if (mounted) {
          setTargets(data);
          setIsLoading(false);
        }
      } catch (err) {
        console.error('Target sync error:', err);
        // Fallback or retry logic
      }
    }

    fetchTargets();
    const interval = setInterval(fetchTargets, 5000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return { targets, isLoading };
}

function normalizeAuditProofArtifact(value: Record<string, unknown>): DashboardDataBundle | null {
  if (!isRecord(value.audit_receipt) || !isRecord(value.cryptographic_proof)) {
    return null;
  }

  const receipt = value.audit_receipt;
  const proof = value.cryptographic_proof;
  const tamperDetected = proof.tamper_detected === true;

  const decision: DecisionRecord = {
    id: asString(receipt.fact_id, 'artifact_001'),
    title: `${asString(receipt.project, 'babylon60 project')} · ${asString(
      receipt.fact_type,
      'decision',
    )}`,
    description: asString(receipt.content, 'No content provided in audit receipt.'),
    agent: asString(receipt.agent_id, 'unknown-agent'),
    tenant: asString(receipt.tenant_id, 'unknown-tenant'),
    status: tamperDetected ? 'Escalated' : 'Verified',
    statusTone: tamperDetected ? 'alert' : 'ok',
    step: tamperDetected ? 'Tamper' : 'Export proof',
    updatedAt: asString(receipt.timestamp, 'Unknown'),
    proofSize: 'CLI artifact',
    tx: `ledger_${typeof proof.ledger_index === 'number' ? proof.ledger_index : 'unknown'}`,
    hash: asString(proof.current_hash, 'sha3:unknown'),
    previousHash: asString(proof.previous_hash, 'sha3:unknown'),
    exportMode: 'audit receipt + cryptographic proof',
    escalation: tamperDetected ? 'P1 review' : 'No escalation',
    summary: tamperDetected
      ? 'The imported proof artifact indicates tamper detection and routes directly into incident review.'
      : 'The imported proof artifact preserves a clean ledger path and can be exported without additional reconciliation.',
    proofNotes: [
      'Audit receipt payload',
      'Cryptographic proof block',
      asString(value.verification_command, 'Verification command unavailable'),
    ],
    timeline: [
      {
        id: 'artifact-store',
        title: 'Audit receipt imported',
        body: asString(receipt.content, 'Artifact content missing.'),
        meta: [asString(receipt.timestamp, 'Unknown'), 'store', asString(receipt.project, 'project')],
        tone: 'ok',
      },
      {
        id: 'artifact-verify',
        title: tamperDetected ? 'Tamper detected in proof' : 'Proof verified',
        body: tamperDetected
          ? 'The cryptographic proof marks this artifact as tampered, so the route stays fail-closed.'
          : 'The cryptographic proof indicates a sealed Merkle root with no tamper signal.',
        meta: [
          `ledger index ${typeof proof.ledger_index === 'number' ? proof.ledger_index : 'unknown'}`,
          tamperDetected ? 'tamper' : 'verify',
          proof.merkle_root_sealed === true ? 'merkle sealed' : 'merkle status unknown',
        ],
        tone: tamperDetected ? 'alert' : 'ok',
      },
      {
        id: 'artifact-export',
        title: 'Verification command preserved',
        body: 'The loader keeps the source verification command inside the proof manifest for operator handoff.',
        meta: ['export', 'cli artifact', 'proof ready'],
        tone: 'ok',
      },
    ],
  };

  return {
    generatedAt: asString(receipt.timestamp, FALLBACK_GENERATED_AT),
    kpiMetrics: synthesizeMetrics([decision]),
    trendSeries: synthesizeTrend([decision]),
    decisionRecords: [decision],
  };
}

function normalizeLineageArtifact(value: Record<string, unknown>): DashboardDataBundle | null {
  if (!isRecord(value.babylon60_lineage_proof) || !Array.isArray(value.facts)) {
    return null;
  }

  const proof = value.babylon60_lineage_proof;
  const facts = value.facts.filter(isRecord);
  if (!facts.length) {
    return null;
  }

  const verification = isRecord(value.verification) ? value.verification : {};
  const chainIntegrity = verification.chain_integrity !== false;
  const leadFact = facts[facts.length - 1] ?? facts[0];

  const timeline: AuditEvent[] = facts.map((fact, index) => ({
    id: asString(fact.id, `lineage_${index + 1}`),
    title: index === facts.length - 1 ? 'Latest fact in lineage' : 'Lineage fact',
    body: asString(fact.content, 'No fact content provided.'),
    meta: [
      asString(fact.timestamp_utc, 'Unknown'),
      index === facts.length - 1 ? 'audit' : 'store',
      asString(fact.agent, 'unknown-agent'),
    ],
    tone: 'ok',
  }));

  if (!chainIntegrity) {
    timeline.push({
      id: 'lineage-integrity-failure',
      title: 'Chain integrity degraded',
      body: asString(verification.proof_notes, 'Verification notes unavailable.'),
      meta: [asString(proof.timestamp_utc, 'Unknown'), 'tamper', 'chain integrity false'],
      tone: 'alert',
    });
  } else {
    timeline.push({
      id: 'lineage-verified',
      title: 'Lineage proof verified',
      body: asString(verification.proof_notes, 'Cryptographic proof loaded successfully.'),
      meta: [asString(proof.timestamp_utc, 'Unknown'), 'verify', asString(verification.status, 'VALID')],
      tone: 'ok',
    });
  }

  const decision: DecisionRecord = {
    id: asString(leadFact.id, 'lineage_decision'),
    title: `Lineage proof for ${asString(proof.tenant_id, 'tenant')}`,
    description: asString(leadFact.content, 'No fact content provided.'),
    agent: asString(leadFact.agent, 'unknown-agent'),
    tenant: asString(proof.tenant_id, 'unknown-tenant'),
    status: chainIntegrity ? 'Verified' : 'Escalated',
    statusTone: chainIntegrity ? 'ok' : 'alert',
    step: chainIntegrity ? 'Export proof' : 'Audit',
    updatedAt: asString(proof.timestamp_utc, FALLBACK_GENERATED_AT),
    proofSize: 'Lineage artifact',
    tx: asString(proof.signature, 'signature-unavailable'),
    hash: asString(leadFact.hash, 'sha3:unknown'),
    previousHash: asString(leadFact.previous_hash, 'sha3:unknown'),
    exportMode: 'lineage proof + facts',
    escalation: chainIntegrity ? 'No escalation' : 'P1 lineage review',
    summary: chainIntegrity
      ? 'The imported lineage proof preserves a clean tenant-scoped custody chain.'
      : 'The imported lineage proof contains a chain-integrity failure and stays pinned to audit review.',
    proofNotes: [
      `Merkle root ${asString(proof.merkle_root, 'unknown')}`,
      `Signature ${asString(proof.signature, 'unknown')}`,
      asString(verification.proof_notes, 'Verification notes unavailable'),
    ],
    timeline,
  };

  return {
    generatedAt: asString(proof.timestamp_utc, FALLBACK_GENERATED_AT),
    kpiMetrics: synthesizeMetrics([decision]),
    trendSeries: synthesizeTrend([decision]),
    decisionRecords: [decision],
  };
}

function normalizeExternalData(value: unknown) {
  if (!isRecord(value)) {
    throw new Error('Unsupported JSON payload: expected an object at the top level.');
  }

  return (
    normalizeDashboardBundle(value) ||
    normalizeAuditProofArtifact(value) ||
    normalizeLineageArtifact(value) ||
    (() => {
      throw new Error(
        'Unsupported JSON payload: expected a dashboard bundle, audit proof artifact, or lineage artifact.',
      );
    })()
  );
}

function getDataParam() {
  if (typeof window === 'undefined') {
    return undefined;
  }

  return new URLSearchParams(window.location.search).get('data') ?? undefined;
}

export function useDashboardData(): DashboardDataState {
  const [state, setState] = useState<DashboardDataState>({
    data: fallbackDashboardData,
    isLoading: false,
    sourceLabel: 'embedded mock data',
  });

  useEffect(() => {
    const dataPath = getDataParam();

    // CASE 1: Live SSE Bridge (Default if no data param)
    if (!dataPath) {
      const eventSource = new EventSource('http://127.0.0.1:8000/stream');

      eventSource.addEventListener('ledger_update', (event) => {
        try {
          const payload = JSON.parse(event.data);
          const normalized = normalizeExternalData(payload);
          setState({
            data: normalized,
            isLoading: false,
            sourceLabel: 'Live SSE Bridge (C5-CNS)',
          });
        } catch (error) {
          console.error('[!] SSE Parse Failure:', error);
        }
      });

      eventSource.onerror = () => {
        // Silent fallback/close on bridge failure
        eventSource.close();
      };

      return () => eventSource.close();
    }

    // CASE 2: Legacy External JSON Loading
    const sourcePath = dataPath;
    let cancelled = false;

    async function loadExternalData() {
      setState((current) => ({
        ...current,
        errorMessage: undefined,
        isLoading: true,
        sourceLabel: sourcePath,
      }));

      try {
        const response = await fetch(sourcePath, { cache: 'no-store' });
        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`);
        }

        const payload: unknown = await response.json();
        const normalized = normalizeExternalData(payload);
        if (cancelled) {
          return;
        }

        setState({
          data: normalized,
          isLoading: false,
          sourceLabel: sourcePath,
        });
      } catch (error) {
        if (cancelled) {
          return;
        }

        setState({
          data: fallbackDashboardData,
          errorMessage: error instanceof Error ? error.message : 'Unknown data loading failure.',
          isLoading: false,
          sourceLabel: sourcePath,
        });
      }
    }

    void loadExternalData();

    return () => {
      cancelled = true;
    };
  }, []);


  return state;
}
