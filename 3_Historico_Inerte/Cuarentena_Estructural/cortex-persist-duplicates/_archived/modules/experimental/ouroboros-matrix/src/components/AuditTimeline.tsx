import { ArrowRight } from 'lucide-react';
import type { AuditEvent, DecisionRecord } from '../data/dashboard';

type AuditTimelineProps = {
  decision: DecisionRecord;
  events: AuditEvent[];
  proofHref: string;
};

export function AuditTimeline({ decision, events, proofHref }: AuditTimelineProps) {
  return (
    <div className="timeline-panel">
      <div className="section-head">
        <div>
          <span className="eyebrow">Audit timeline</span>
          <h2>Custody chain for {decision.tx}</h2>
        </div>
        <a className="ghost-link" href={proofHref}>
          <span>Open proof route</span>
          <ArrowRight size={16} />
        </a>
      </div>

      <div className="timeline-list">
        {events.map((event) => (
          <article className="timeline-item" data-tone={event.tone} key={event.id}>
            <span className="timeline-dot" />
            <div className="timeline-content">
              <strong>{event.title}</strong>
              <p>{event.body}</p>
              <div className="timeline-meta">
                {event.meta.map((meta) => (
                  <span key={meta}>{meta}</span>
                ))}
              </div>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
