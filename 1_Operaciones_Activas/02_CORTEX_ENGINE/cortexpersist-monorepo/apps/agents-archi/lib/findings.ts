import type { AuditFinding } from '@cortex/sdk';

// OUROBOROS canonical findings registry
// Add new findings here — they auto-emit to CortexPersist on build/deploy
export const OUROBOROS_FINDINGS: AuditFinding[] = [
  {
    id: 'OUROBOROS-FD-VM-01',
    severity: 'critical',
    protocol: 'Firedancer VM',
    auditor: 'borja-moskv',
    title: 'Unbounded loop in JIT compiler path',
    description: 'The JIT compiler does not enforce cycle limits on certain bytecode patterns, enabling infinite loop DoS.',
    exploitable: true,
  },
  {
    id: 'OUROBOROS-FD-VM-02',
    severity: 'high',
    protocol: 'Firedancer VM',
    auditor: 'borja-moskv',
    title: 'Memory aliasing in stack frame allocation',
    exploitable: false,
  },
];
