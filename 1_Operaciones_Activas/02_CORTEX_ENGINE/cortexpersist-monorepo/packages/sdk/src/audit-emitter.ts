import type { AuditFinding } from './types';
import { CortexClient } from './client';
import type { CortexConfig } from './types';

export class AuditEmitter {
  private client: CortexClient;

  constructor(config: CortexConfig) {
    this.client = new CortexClient(config);
  }

  async finding(finding: AuditFinding) {
    return this.client.event({
      type: 'audit.finding',
      payload: finding as unknown as Record<string, unknown>,
      id: finding.id,
    });
  }

  async resolvedFinding(id: string, notes?: string) {
    return this.client.event({
      type: 'audit.finding.resolved',
      payload: { id, notes: notes ?? '', resolvedAt: Date.now() },
    });
  }

  async sessionStart(sessionId: string, auditor: string, protocol: string) {
    return this.client.event({
      type: 'audit.session.start',
      payload: { sessionId, auditor, protocol, startedAt: Date.now() },
    });
  }

  async sessionEnd(sessionId: string, totalFindings: number) {
    return this.client.event({
      type: 'audit.session.end',
      payload: { sessionId, totalFindings, endedAt: Date.now() },
    });
  }

  getChain() { return this.client.getChain(); }
  getMerkleRoot() { return this.client.getMerkleRoot(); }
}
