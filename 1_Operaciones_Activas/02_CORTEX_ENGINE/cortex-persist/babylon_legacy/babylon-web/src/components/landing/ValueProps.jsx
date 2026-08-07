// C5-REAL EXERGY CERTIFIED
import React from 'react';

export function ValueProps() {
  return (
    <section style={{ marginTop: '8rem' }}>
      <div className="grid-3">
        <div className="glass-panel" style={{ padding: '2rem' }}>
          <h3 className="text-mono" style={{ color: 'var(--accent-primary)', marginBottom: '1rem' }}>01. Local-First</h3>
          <p style={{ color: 'var(--text-muted)' }}>
            Your agents run locally. All embeddings and memory reside in your SQLite database. BABYLON-60 never reads your raw data.
          </p>
        </div>

        <div className="glass-panel" style={{ padding: '2rem' }}>
          <h3 className="text-mono" style={{ color: 'var(--accent-secondary)', marginBottom: '1rem' }}>02. Independent Notary</h3>
          <p style={{ color: 'var(--text-muted)' }}>
            Your node silently syncs cryptographic hashes (Merkle Roots) to our Cloudflare BFT Ledger, creating an immutable timeline.
          </p>
        </div>

        <div className="glass-panel" style={{ padding: '2rem' }}>
          <h3 className="text-mono" style={{ color: 'var(--accent-success)', marginBottom: '1rem' }}>03. Legal Compliance</h3>
          <p style={{ color: 'var(--text-muted)' }}>
            Generate mathematically irrefutable cryptographic receipts. Shield your enterprise from EU AI Act audits and liabilities.
          </p>
        </div>
      </div>
    </section>
  );
}
