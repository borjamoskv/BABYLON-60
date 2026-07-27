import type { FlowStep } from '../data/dashboard';

type TrustFlowRailProps = {
  steps: FlowStep[];
};

export function TrustFlowRail({ steps }: TrustFlowRailProps) {
  return (
    <div className="flow-panel">
      <div className="section-head">
        <div>
          <span className="eyebrow">Narrative flow</span>
          <h2>Store → verify → tamper → audit → export proof</h2>
        </div>
        <span className="section-meta">Core demo motion</span>
      </div>

      <div className="flow-rail">
        {steps.map((step, index) => (
          <article className="flow-step" data-tone={step.tone} key={step.id}>
            <span className="flow-step__index">0{index + 1}</span>
            <div className="flow-step__copy">
              <span className="eyebrow">{step.title}</span>
              <strong>{step.title}</strong>
              <p>{step.summary}</p>
            </div>
            <span className="status-pill" data-tone={step.badgeTone}>
              {step.badge}
            </span>
          </article>
        ))}
      </div>
    </div>
  );
}
