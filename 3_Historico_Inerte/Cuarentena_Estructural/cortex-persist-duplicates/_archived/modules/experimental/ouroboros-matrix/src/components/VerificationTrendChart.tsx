import type { TrendPoint } from '../data/dashboard';

type VerificationTrendChartProps = {
  points: TrendPoint[];
};

export function VerificationTrendChart({ points }: VerificationTrendChartProps) {
  return (
    <div className="chart-panel">
      <div className="section-head">
        <div>
          <span className="eyebrow">Trend</span>
          <h2>Verification volume vs tamper noise</h2>
        </div>
        <span className="section-meta">10-day window</span>
      </div>

      <div className="chart-grid" aria-hidden="true">
        {points.map((point) => (
          <div className="chart-column" key={point.label}>
            <div className="chart-stack">
              <div className="chart-bar chart-bar--verify" style={{ height: `${point.verify}%` }} />
              <div className="chart-bar chart-bar--tamper" style={{ height: `${point.tamper}%` }} />
            </div>
            <span>{point.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
