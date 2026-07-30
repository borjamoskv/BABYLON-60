import { Download, FileJson } from 'lucide-react';
import type { DecisionRecord, ProofPackage } from '../data/dashboard';

type ProofPackageCardProps = {
  decision: DecisionRecord;
  proofPackage: ProofPackage;
  onDownload: () => void;
  onOpenDecision: () => void;
};

export function ProofPackageCard({
  decision,
  proofPackage,
  onDownload,
  onOpenDecision,
}: ProofPackageCardProps) {
  return (
    <div className="proof-card">
      <div>
        <span className="eyebrow">Proof package</span>
        <h2>{decision.title}</h2>
      </div>

      <div className="proof-card__summary">
        <p>
          Export mode: <strong>{proofPackage.exportMode}</strong> · File size:{' '}
          <strong>{proofPackage.fileSize}</strong> · Escalation:{' '}
          <strong>{proofPackage.escalation}</strong>
        </p>
      </div>

      <ul className="proof-list">
        {proofPackage.manifest.map((item) => (
          <li className="proof-list__item" key={item}>
            <span>Manifest item</span>
            <strong>{item}</strong>
          </li>
        ))}
      </ul>

      <div className="proof-lines">
        <div className="proof-line">
          <span className="proof-line__label">Route decision id</span>
          <code>{proofPackage.decision.id}</code>
        </div>
        <div className="proof-line">
          <span className="proof-line__label">Hash continuity</span>
          <code>{proofPackage.decision.hash}</code>
        </div>
        <div className="proof-line">
          <span className="proof-line__label">Simulated tamper</span>
          <code>{proofPackage.simulatedTamper ? 'true' : 'false'}</code>
        </div>
      </div>

      <div className="proof-card__actions">
        <button className="topbar-button topbar-button--accent" onClick={onDownload} type="button">
          <Download aria-hidden="true" />
          <span>Download JSON</span>
        </button>
        <button className="ghost-link" onClick={onOpenDecision} type="button">
          <FileJson size={16} />
          <span>Back to decision</span>
        </button>
      </div>
    </div>
  );
}
