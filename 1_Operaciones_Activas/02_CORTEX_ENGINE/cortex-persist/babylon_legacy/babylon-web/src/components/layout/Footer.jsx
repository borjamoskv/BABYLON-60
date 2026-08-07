// C5-REAL EXERGY CERTIFIED
import React from 'react';

export function Footer() {
  return (
    <footer style={{
      borderTop: '1px solid var(--border-dim)',
      padding: '4rem 0 2rem 0',
      marginTop: '8rem',
      background: 'rgba(9, 10, 15, 0.95)'
    }}>
      <div className="container" style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr', gap: '3rem', marginBottom: '3rem' }}>
        <div>
          <div className="text-mono" style={{ fontSize: '1.4rem', fontWeight: 'bold', marginBottom: '1rem' }}>
            BABYLON<span style={{ color: 'var(--accent-primary)' }}>60</span>
          </div>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: '360px', lineHeight: '1.6' }}>
            The Trust Infrastructure for Enterprise Autonomous AI. Deterministic Ring-0 Kernel & Cryptographic Audit Trails.
          </p>
          <div className="text-mono" style={{ fontSize: '0.75rem', color: 'var(--accent-success)', marginTop: '1.2rem' }}>
            ● C5-REAL EXERGY CERTIFIED — ZERO OPEX
          </div>
        </div>

        <div>
          <h4 className="text-mono" style={{ fontSize: '0.85rem', color: 'var(--text-main)', marginBottom: '1.2rem' }}>Architecture</h4>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.6rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            <li><a href="#kernel-sim">IRP Membrane</a></li>
            <li><a href="#kernel-sim">Page CUSUM Sentinel</a></li>
            <li><a href="#kernel-sim">Lock-Free EBR Engine</a></li>
            <li><a href="#score-explorer">WASM SIMD Benchmark</a></li>
          </ul>
        </div>

        <div>
          <h4 className="text-mono" style={{ fontSize: '0.85rem', color: 'var(--text-main)', marginBottom: '1.2rem' }}>Compliance</h4>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.6rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            <li><a href="#compliance">EU AI Act (Art. 14)</a></li>
            <li><a href="#compliance">SOC 2 Type II Notary</a></li>
            <li><a href="#compliance">Landauer Energy Bound</a></li>
            <li><a href="#compliance">SCITT Receipts</a></li>
          </ul>
        </div>

        <div>
          <h4 className="text-mono" style={{ fontSize: '0.85rem', color: 'var(--text-main)', marginBottom: '1.2rem' }}>Legal & IP</h4>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.6rem', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            <li><span>Privacy Policy</span></li>
            <li><span>Terms of Service</span></li>
            <li><span>Sovereign Cap Contract</span></li>
            <li><span>OpenTimestamps Proof</span></li>
          </ul>
        </div>
      </div>

      <div className="container" style={{
        borderTop: '1px solid var(--border-dim)',
        paddingTop: '2rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontSize: '0.8rem',
        color: 'var(--text-muted)'
      }}>
        <div>
          © {new Date().getFullYear()} BABYLON60. All rights reserved. Teorema Robinson-Moskv Substrate.
        </div>
        <div className="text-mono" style={{ fontSize: '0.75rem' }}>
          SHA-256 PROVENANCE: <span style={{ color: 'var(--accent-primary)' }}>de92a9e2...3ca36a1f</span>
        </div>
      </div>
    </footer>
  );
}
