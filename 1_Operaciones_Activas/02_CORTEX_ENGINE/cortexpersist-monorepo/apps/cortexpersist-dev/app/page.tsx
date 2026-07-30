import type { Metadata } from 'next';
import { CrossDomainCTA } from '@cortex/ui';

export const metadata: Metadata = {
  title: 'CORTEX-Persist Dev Hub — SDK & Integration',
  alternates: { canonical: 'https://cortexpersist.dev' },
};

export default function HomePage() {
  return (
    <main
      style={{
        minHeight: '100vh',
        background: '#0A0A0A',
        color: '#e0e0e0',
        fontFamily: "'Inter', 'Outfit', system-ui, sans-serif",
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem',
      }}
    >
      <h1
        style={{
          fontSize: 'clamp(2rem, 5vw, 4rem)',
          fontWeight: 800,
          letterSpacing: '-0.03em',
          background: 'linear-gradient(135deg, #2B3BE5 0%, #00ff88 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          textAlign: 'center',
        }}
      >
        Developer Hub
      </h1>
      <p
        style={{
          color: '#666',
          fontSize: '1.1rem',
          marginTop: '1rem',
          maxWidth: '600px',
          textAlign: 'center',
          lineHeight: 1.6,
        }}
      >
        Integrate CORTEX-Persist directly in your agent swarms. High-performance JS/TS/Rust bindings.
      </p>
      <div style={{ marginTop: '2.5rem', marginBottom: '1.5rem' }}>
        <CrossDomainCTA href="https://agents.archi?ref=cortexpersist-dev">
          Live audit examples →
        </CrossDomainCTA>
      </div>
      <nav
        style={{
          display: 'flex',
          gap: '1.5rem',
          fontSize: '0.85rem',
        }}
      >
        <a href="https://cortexpersist.com" style={{ color: '#2B3BE5', textDecoration: 'none' }}>
          ← Main Substrate
        </a>
        <a href="https://cortexpersist.org" style={{ color: '#2B3BE5', textDecoration: 'none' }}>
          Community →
        </a>
      </nav>
    </main>
  );
}
