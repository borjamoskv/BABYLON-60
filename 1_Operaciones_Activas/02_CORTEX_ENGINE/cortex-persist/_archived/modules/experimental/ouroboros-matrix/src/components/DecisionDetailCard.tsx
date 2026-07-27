import { ArrowRight } from 'lucide-react';
import type { DecisionRecord, ProofPackage } from '../data/dashboard';

type DecisionDetailCardProps = {
  decision: DecisionRecord;
  proofPackage: ProofPackage;
  onOpenDecision: () => void;
};

export function DecisionDetailCard({
  decision,
  proofPackage,
  onOpenDecision,
}: DecisionDetailCardProps) {
  return (
    <aside className="panel detail-card">
      <div>
        <span className="eyebrow">Selected decision</span>
        <h2>{decision.title}</h2>
      </div>

      <div className="detail-card__summary">
        <span className="status-pill" data-tone={decision.statusTone}>
          {decision.status}
        </span>
        <p>{decision.summary}</p>
      </div>

      <div className="detail-grid">
        <div className="detail-metric">
          <span className="detail-key">Agent</span>
          <strong>{decision.agent}</strong>
        </div>
        <div className="detail-metric">
          <span className="detail-key">Tenant</span>
          <strong>{decision.tenant}</strong>
        </div>
        <div className="detail-metric">
          <span className="detail-key">Ledger tx</span>
          <strong>{decision.tx}</strong>
        </div>
        <div className="detail-metric">
          <span className="detail-key">Escalation</span>
          <strong>{decision.escalation}</strong>
        </div>
      </div>

      <div className="proof-lines">
        <div className="proof-line">
          <span className="proof-line__label">Record hash</span>
          <code>{decision.hash}</code>
        </div>
        <div className="proof-line">
          <span className="proof-line__label">Prev hash</span>
          <code>{decision.previousHash}</code>
        </div>
        <div className="proof-line">
          <span className="proof-line__label">Export mode</span>
          <code>{proofPackage.exportMode}</code>
        </div>
      </div>

      <div className="detail-card__actions">
        <button className="ghost-link" onClick={onOpenDecision} type="button">
          <span>Open linked route</span>
          <ArrowRight size={16} />
        </button>
      </div>
    </aside>
  );
}
