// C5-REAL EXERGY CERTIFIED
import React from 'react';

export function Hero() {
  return (
    <div className="flex-center" style={{ flexDirection: 'column', textAlign: 'center', gap: '2rem' }}>
      <div className="glass-panel animate-fade-in-up" style={{ padding: '0.5rem 1rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-success)' }}>
        <span style={{ width: '8px', height: '8px', backgroundColor: 'var(--accent-success)', borderRadius: '50%' }}></span>
        <span className="text-mono" style={{ fontSize: '0.8rem' }}>BABYLON60 OPERATIONAL — RING-0 KERNEL ONLINE</span>
      </div>

      <h1 className="h1-hero animate-fade-in-up delay-100">
        BABYLON<span style={{ color: 'var(--accent-primary)' }}>60</span> <br />
        <span style={{ fontSize: '0.7em', color: 'var(--text-main)' }}>The Trust Infrastructure for Enterprise AI</span>
      </h1>

      <p className="animate-fade-in-up delay-200" style={{ fontSize: '1.2rem', color: 'var(--text-muted)', maxWidth: '750px', margin: '0 auto' }}>
        Sovereign C5-REAL Substrate. The deterministic equivalent of TLS for Autonomous Agents.
        Fail-Stop containment, zero marginal COGS (~95%+ Gross Margin), and immutable cryptographic audit trails engineered for EU AI Act compliance.
      </p>

      <div className="animate-fade-in-up delay-300" style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
        <a href="#kernel-sim" className="btn btn-primary animate-pulse-glow" style={{ padding: '1rem 3rem', fontSize: '1.1rem' }}>
          Inspect IRP Kernel
        </a>
        <button className="btn btn-outline" style={{ padding: '1rem 3rem', fontSize: '1.1rem' }} onClick={() => window.open('https://github.com/borjamoskv/Teorema-Robinson-Moskv', '_blank')}>
          Read the Axioms
        </button>
      </div>
    </div>
  );
}
