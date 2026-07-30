import type { KpiMetric } from '../data/dashboard';

type KpiStripProps = {
  metrics: KpiMetric[];
};

export function KpiStrip({ metrics }: KpiStripProps) {
  return (
    <div className="kpi-strip">
      {metrics.map((metric) => (
        <article className="metric-card" key={metric.id}>
          <span className="metric-card__label">{metric.label}</span>
          <strong className="metric-card__value">{metric.value}</strong>
          <span className="metric-card__change" data-tone={metric.tone}>
            {metric.change}
          </span>
        </article>
      ))}
    </div>
  );
}
