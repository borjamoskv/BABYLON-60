// C5-REAL EXERGY CERTIFIED
import React from 'react';

function App() {
  return (
    <>
      <nav style={{ padding: '2rem 0', borderBottom: '1px solid var(--border-dim)' }}>
        <div className="container flex-center" style={{ justifyContent: 'space-between' }}>
          <div className="text-mono" style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
            BABYLON<span style={{ color: 'var(--accent-primary)' }}>-60</span>
          </div>
          <div>
            <a href="#compliance" style={{ marginRight: '2rem', fontSize: '0.9rem' }}>EU AI Act Compliance</a>
            <a href="#infrastructure" style={{ marginRight: '2rem', fontSize: '0.9rem' }}>Trust Infrastructure</a>
            <button className="btn btn-primary" onClick={() => alert('Stripe Checkout Initiated')}>
              Deploy C5-REAL
            </button>
          </div>
        </div>
      </nav>

      <main className="container" style={{ paddingTop: '8rem', paddingBottom: '8rem' }}>
        <div className="flex-center" style={{ flexDirection: 'column', textAlign: 'center', gap: '2rem' }}>

          <div className="glass-panel animate-fade-in-up" style={{ padding: '0.5rem 1rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-success)' }}>
            <span style={{ width: '8px', height: '8px', backgroundColor: 'var(--accent-success)', borderRadius: '50%' }}></span>
            <span className="text-mono" style={{ fontSize: '0.8rem' }}>CORTEX ENGINE ONLINE — ZERO OPEX</span>
          </div>

          <h1 className="h1-hero animate-fade-in-up delay-100">
            The Trust Infrastructure <br />
            for <span style={{ color: 'var(--accent-primary)' }}>Autonomous AI</span>
          </h1>

          <p className="animate-fade-in-up delay-200" style={{ fontSize: '1.2rem', color: 'var(--text-muted)', maxWidth: '700px', margin: '0 auto' }}>
            Sovereign C5-REAL Substrate. The equivalent of SSL/TLS for AI memory.
            Cryptographic audit trails engineered for EU AI Act compliance.
            Zero cloud dependency.
          </p>

          <div className="animate-fade-in-up delay-300" style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
            <button className="btn btn-primary animate-pulse-glow" style={{ padding: '1rem 3rem', fontSize: '1.1rem' }}>
              Initialize Ledger (Pro)
            </button>
            <button className="btn btn-outline" style={{ padding: '1rem 3rem', fontSize: '1.1rem' }}>
              Read the Axioms
            </button>
          </div>
        </div>

        <section style={{ marginTop: '10rem' }}>
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
      </main>
    </>
  );
}

export default App;
