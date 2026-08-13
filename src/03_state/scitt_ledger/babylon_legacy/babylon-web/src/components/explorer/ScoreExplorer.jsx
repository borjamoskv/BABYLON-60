// C5-REAL EXERGY CERTIFIED
import React, { useState, useCallback } from 'react';
import { useWasmEngine } from '../../hooks/useWasmEngine';

export function ScoreExplorer() {
  const { wasmBenchmark, runWasmHyperEval } = useWasmEngine();
  const [scoresData, setScoresData] = useState(null);
  const [scoreQuery, setScoreQuery] = useState('');
  const [scoreResult, setScoreResult] = useState(null);
  const [scoreLoading, setScoreLoading] = useState(false);

  // Lazy-load scores.json on first interaction
  const loadScores = useCallback(async () => {
    if (scoresData) return scoresData;
    setScoreLoading(true);
    try {
      const res = await fetch('/scores.json');
      const data = await res.json();
      setScoresData(data);
      setScoreLoading(false);
      return data;
    } catch (err) {
      console.error('Failed to load scores.json:', err);
      setScoreLoading(false);
      return null;
    }
  }, [scoresData]);

  const lookupScore = async (num) => {
    const data = await loadScores();
    if (!data) return;
    const n = parseInt(num, 10);
    if (isNaN(n) || n < 1 || n > 120000) {
      setScoreResult({ error: true, message: `Invalid: must be 1–120,000` });
      return;
    }
    const score = data.scores[String(n)];
    setScoreResult({ number: n, score, metadata: data.metadata });
  };

  return (
    <section id="score-explorer" style={{ marginTop: '8rem' }}>
      <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
        <h2 className="text-mono" style={{ fontSize: '2rem', color: 'var(--accent-secondary)', marginBottom: '0.5rem' }}>
          Score Explorer (1–120,000)
        </h2>
        <p style={{ color: 'var(--text-muted)' }}>
          Multi-criteria evaluation engine: Primality (30%) · Divisor Richness (25%) · Bit Density (20%) · Fibonacci Proximity (15%) · Perfect Power (10%)
        </p>
      </div>

      <div className="grid-3">
        {/* Search Panel */}
        <div className="glass-panel" style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <span className="text-mono" style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>SCORE LOOKUP</span>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type="number"
              min="1"
              max="120000"
              placeholder="Enter 1–120,000"
              value={scoreQuery}
              onChange={(e) => setScoreQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && lookupScore(scoreQuery)}
              style={{
                flex: 1,
                padding: '0.6rem 1rem',
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid var(--border-dim)',
                borderRadius: '6px',
                color: 'var(--text-main)',
                fontFamily: 'var(--font-mono)',
                fontSize: '1rem'
              }}
            />
            <button
              className="btn btn-primary"
              style={{ padding: '0.6rem 1.2rem' }}
              onClick={() => lookupScore(scoreQuery)}
              disabled={scoreLoading}
            >
              {scoreLoading ? '...' : '⚡ Eval'}
            </button>
          </div>

          {scoreResult && !scoreResult.error && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <span style={{ fontSize: '2.5rem', fontWeight: 'bold', color: 'var(--accent-primary)' }}>
                  {scoreResult.score.toFixed(2)}
                </span>
                <span className="text-mono" style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                  / 100
                </span>
              </div>
              {/* Score Bar */}
              <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.05)', borderRadius: '4px', overflow: 'hidden' }}>
                <div style={{
                  width: `${scoreResult.score}%`,
                  height: '100%',
                  background: scoreResult.score > 60 ? 'var(--accent-success)' : scoreResult.score > 40 ? 'var(--accent-primary)' : 'var(--accent-secondary)',
                  boxShadow: `0 0 15px ${scoreResult.score > 60 ? 'var(--accent-success)' : scoreResult.score > 40 ? 'var(--accent-primary)' : 'var(--accent-secondary)'}`,
                  borderRadius: '4px',
                  transition: 'width 0.4s ease'
                }} />
              </div>
              <div className="text-mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                n = {scoreResult.number.toLocaleString()}
              </div>
            </div>
          )}
          {scoreResult && scoreResult.error && (
            <div className="text-mono" style={{ color: 'var(--accent-secondary)', fontSize: '0.85rem' }}>
              {scoreResult.message}
            </div>
          )}

          {/* Quick Access Buttons */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
            {[1, 2, 7, 42, 127, 1024, 7919, 46368, 120000].map(n => (
              <button
                key={n}
                className="btn btn-outline"
                style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }}
                onClick={() => { setScoreQuery(String(n)); lookupScore(n); }}
              >
                {n.toLocaleString()}
              </button>
            ))}
          </div>

          {/* WASM Hyper-Eval Benchmark */}
          <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--accent-primary)', borderRadius: '6px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
              <span className="text-mono" style={{ fontSize: '0.8rem', color: 'var(--accent-primary)' }}>WASM SIMD ENGINE</span>
              <button className="btn btn-primary" style={{ padding: '0.3rem 0.6rem', fontSize: '0.75rem' }} onClick={runWasmHyperEval}>
                ⚡ Detonate 120K (Rust)
              </button>
            </div>
            {wasmBenchmark && (
              <div className="text-mono" style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                <div><span style={{ color: 'var(--accent-success)' }}>{wasmBenchmark.timeMs}ms</span> | {wasmBenchmark.total.toLocaleString()} Nodes</div>
                <div style={{ color: 'var(--accent-primary)', fontWeight: 'bold' }}>{(wasmBenchmark.opsPerSec / 1000000).toFixed(2)}M Ops/sec</div>
                <div>Score(42) = {wasmBenchmark.sampleScore}</div>
              </div>
            )}
            {!wasmBenchmark && (
              <div className="text-mono" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Eval 120K nodes in Native Rust WASM.
              </div>
            )}
          </div>
        </div>

        {/* Distribution Histogram */}
        <div className="glass-panel" style={{ padding: '2rem', gridColumn: 'span 2' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <span className="text-mono" style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>SCORE DISTRIBUTION (120,000 INTEGERS)</span>
            <span className="text-mono" style={{ fontSize: '0.8rem', color: 'var(--accent-success)' }}>
              {scoresData ? `avg: ${scoresData.metadata.stats.avg.toFixed(2)}` : 'LOAD TO VIEW'}
            </span>
          </div>

          {scoresData ? (
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: '4px', height: '180px' }}>
              {scoresData.metadata.histogram.map((count, i) => {
                const maxCount = Math.max(...scoresData.metadata.histogram);
                const heightPct = maxCount > 0 ? (count / maxCount) * 100 : 0;
                const lo = i * 10;
                const hi = lo + 10;
                return (
                  <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
                    <div
                      style={{
                        width: '100%',
                        height: `${heightPct}%`,
                        minHeight: count > 0 ? '4px' : '0',
                        background: `linear-gradient(to top, var(--accent-primary), var(--accent-success))`,
                        borderRadius: '3px 3px 0 0',
                        transition: 'height 0.5s ease',
                        opacity: heightPct > 50 ? 1 : 0.6 + (heightPct / 200)
                      }}
                      title={`${lo}–${hi}: ${count.toLocaleString()} numbers`}
                    />
                    <span className="text-mono" style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                      {lo}
                    </span>
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{ height: '180px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <button className="btn btn-outline" onClick={loadScores} disabled={scoreLoading}>
                {scoreLoading ? 'Loading 120K scores...' : '⚡ Load Distribution Data'}
              </button>
            </div>
          )}

          {scoresData && (
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '1rem', fontSize: '0.8rem' }}>
              <span className="text-mono" style={{ color: 'var(--accent-secondary)' }}>min: {scoresData.metadata.stats.min.toFixed(2)}</span>
              <span className="text-mono" style={{ color: 'var(--text-muted)' }}>{scoresData.metadata.totalScores.toLocaleString()} scored</span>
              <span className="text-mono" style={{ color: 'var(--accent-success)' }}>max: {scoresData.metadata.stats.max.toFixed(2)}</span>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
