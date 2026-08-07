// C5-REAL EXERGY CERTIFIED
import React, { useState } from 'react';

export function DeployModal({ isOpen, onClose }) {
  const [copied, setCopied] = useState(false);
  const deployCmd = "curl -fsSL https://babylon60.com/install.sh | sh";

  if (!isOpen) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(deployCmd);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(5, 7, 12, 0.85)',
      backdropFilter: 'blur(16px)',
      WebkitBackdropFilter: 'blur(16px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: '1rem'
    }} onClick={onClose}>
      <div className="glass-panel animate-fade-in-up" style={{
        maxWidth: '550px',
        width: '100%',
        padding: '2.5rem',
        borderColor: 'var(--accent-primary)',
        boxShadow: '0 0 40px rgba(0, 240, 255, 0.25)',
        position: 'relative'
      }} onClick={(e) => e.stopPropagation()}>

        <button onClick={onClose} style={{
          position: 'absolute',
          top: '1.2rem',
          right: '1.5rem',
          background: 'none',
          border: 'none',
          color: 'var(--text-muted)',
          fontSize: '1.5rem',
          cursor: 'pointer'
        }}>×</button>

        <div className="text-mono" style={{ fontSize: '0.8rem', color: 'var(--accent-success)', marginBottom: '0.5rem' }}>
          ● C5-REAL NODE PROVISIONER
        </div>

        <h3 className="h1-hero" style={{ fontSize: '1.8rem', marginBottom: '1rem' }}>
          Deploy BABYLON<span style={{ color: 'var(--accent-primary)' }}>60</span> Node
        </h3>

        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', marginBottom: '1.5rem' }}>
          Instantiate a zero-trust, local Ring-0 kernel node with lock-free EBR memory management and automated OpenTimestamps L5 anchoring.
        </p>

        <div style={{
          background: 'rgba(0, 0, 0, 0.6)',
          border: '1px solid var(--border-dim)',
          borderRadius: '8px',
          padding: '1rem',
          marginBottom: '1.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <code className="text-mono" style={{ fontSize: '0.85rem', color: 'var(--accent-primary)' }}>
            {deployCmd}
          </code>
          <button className="btn btn-outline" style={{ padding: '0.4rem 0.8rem', fontSize: '0.75rem' }} onClick={handleCopy}>
            {copied ? '✓ Copied' : 'Copy'}
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.5rem', fontSize: '0.85rem' }}>
          <div style={{ background: 'rgba(255,255,255,0.02)', padding: '0.8rem', borderRadius: '6px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Target Architecture:</span>
            <div className="text-mono" style={{ color: 'var(--text-main)', marginTop: '0.2rem' }}>ARM64 / Apple Silicon</div>
          </div>
          <div style={{ background: 'rgba(255,255,255,0.02)', padding: '0.8rem', borderRadius: '6px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Marginal COGS:</span>
            <div className="text-mono" style={{ color: 'var(--accent-success)', marginTop: '0.2rem' }}>$0.00 / Zero-OpEx</div>
          </div>
        </div>

        <button className="btn btn-primary" style={{ width: '100%', padding: '0.9rem' }} onClick={onClose}>
          Acknowledge & Return to Dashboard
        </button>
      </div>
    </div>
  );
}
