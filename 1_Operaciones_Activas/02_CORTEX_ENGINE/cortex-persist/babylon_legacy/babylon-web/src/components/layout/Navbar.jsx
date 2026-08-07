// C5-REAL EXERGY CERTIFIED
import React from 'react';

export function Navbar() {
  return (
    <nav style={{ padding: '2rem 0', borderBottom: '1px solid var(--border-dim)' }}>
      <div className="container flex-center" style={{ justifyContent: 'space-between' }}>
        <div className="text-mono" style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>
          BABYLON<span style={{ color: 'var(--accent-primary)' }}>60</span>
        </div>
        <div>
          <a href="#kernel-sim" style={{ marginRight: '2rem', fontSize: '0.9rem' }}>Kernel Simulator</a>
          <a href="#score-explorer" style={{ marginRight: '2rem', fontSize: '0.9rem' }}>Score Explorer</a>
          <a href="#compliance" style={{ marginRight: '2rem', fontSize: '0.9rem' }}>EU AI Act Compliance</a>
          <button className="btn btn-primary" onClick={() => alert('C5-REAL Substrate Deployment Requested — Initializing Node Credentials.')}>
            Deploy C5-REAL
          </button>
        </div>
      </div>
    </nav>
  );
}
