import type { Metadata } from 'next';
import { OUROBOROS_FINDINGS } from '@/lib/findings';
import { auditEmitter } from '@/lib/audit-emitter';
import { CryptographicAnchor, CrossDomainCTA } from '@cortex/ui';

export const metadata: Metadata = {
  title: 'Sovereign Audit Ledger',
  alternates: { canonical: 'https://agents.archi' },
};

export default async function HomePage() {
  // Pre-anchor all findings for the static dashboard
  const anchoredFindings = await Promise.all(
    OUROBOROS_FINDINGS.map(async (f) => {
      // Catch errors if SDK fails during local build without API keys
      try {
        const result = await auditEmitter.finding(f);
        return {
          ...f,
          merkleRoot: result.merkleRoot || '0x0000000000000000000000000000000000000000000000000000000000000000',
          signature: result.signature || '0x0000000000000000000000000000000000000000000000000000000000000000',
          anchored: result.anchored || false,
          timestamp: result.timestamp || new Date().toISOString(),
        };
      } catch (err) {
        return {
          ...f,
          merkleRoot: 'PENDING_ANCHOR_STATE_AWAITING_CRON',
          signature: 'UNVERIFIED_SIGNATURE_WAITING_FOR_KEY',
          anchored: false,
          timestamp: new Date().toISOString(),
        };
      }
    })
  );

  return (
    <main
      style={{
        minHeight: '100vh',
        background: '#030303',
        color: '#e0e0e0',
        fontFamily: 'monospace',
        padding: '2rem',
      }}
    >
      <header style={{ marginBottom: '2rem', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '1rem' }}>
        <h1 style={{ fontSize: '1rem', fontWeight: 'bold', color: '#00ff88', letterSpacing: '0.1em' }}>
          AGENTS.ARCHI // SOVEREIGN AUDIT LEDGER
        </h1>
        <p style={{ color: '#555', fontSize: '0.75rem', marginTop: '0.25rem' }}>
          Anchored via CORTEX-Persist · Ω₂ Entropic Asymmetry · C5-REAL
        </p>
      </header>

      <section>
        <h2 style={{ fontSize: '0.8rem', color: '#444', marginBottom: '1rem', textTransform: 'uppercase', letterSpacing: '0.15em' }}>
          OUROBOROS Registry — {anchoredFindings.length} findings
        </h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {anchoredFindings.map(f => (
            <div
              key={f.id}
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem',
                borderLeft: `3px solid ${f.severity === 'critical' ? '#ff2244' : f.severity === 'high' ? '#ff6600' : '#ffcc00'}`,
                paddingLeft: '1rem'
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.25rem' }}>
                  <span style={{ color: '#aaa', fontSize: '1rem', fontWeight: 'bold' }}>{f.title}</span>
                  <span style={{ fontSize: '0.65rem', padding: '2px 6px', background: 'rgba(255,255,255,0.05)', color: f.severity === 'critical' ? '#ff2244' : '#ff6600', textTransform: 'uppercase' }}>
                    {f.severity}
                  </span>
                </div>
                <div style={{ color: '#666', fontSize: '0.75rem', marginBottom: '0.5rem' }}>Protocol: {f.protocol} · Auditor: {f.auditor}</div>
                {f.description && <div style={{ color: '#888', fontSize: '0.8rem', marginBottom: '1rem', maxWidth: '800px' }}>{f.description}</div>}
              </div>
              
              <CryptographicAnchor
                findingId={f.id}
                merkleRoot={f.merkleRoot}
                signature={f.signature}
                isVerified={f.anchored}
                timestamp={String(f.timestamp)}
              />
              
              <div>
                <CrossDomainCTA href={`https://cortexpersist.dev?ref=audit-${f.id}`}>
                  Verify live execution with SDK →
                </CrossDomainCTA>
              </div>
            </div>
          ))}
        </div>
      </section>

      <footer style={{ marginTop: '3rem', borderTop: '1px solid rgba(255,255,255,0.04)', paddingTop: '1rem', color: '#333', fontSize: '0.65rem' }}>
        <a href="https://cortexpersist.com?ref=agents-archi" style={{ color: '#555' }}>Protected by CORTEX Memory</a>
        {' · '}
        <a href="https://cortexpersist.com?ref=agents-archi" style={{ color: '#555' }}>cortexpersist.com</a>
      </footer>
    </main>
  );
}
