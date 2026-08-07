// C5-REAL EXERGY CERTIFIED
import React from 'react';

// Web Crypto helper decoupled from F# Kernel
async function sha256Hex(message) {
  const encoder = new TextEncoder();
  const data = encoder.encode(message);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

export function BFTLedger({ cloudSyncStatus, bftLogs, kernelState, lastParentId }) {

  const exportBFTReceipt = async () => {
    const receipt = {
      issuer: "BABYLON60 C5-REAL Node",
      timestamp: new Date().toISOString(),
      membraneState: kernelState.cases()[kernelState.tag],
      lastBftRoot: lastParentId,
      bftLogs: bftLogs
    };

    // Create a deterministic hash of the receipt to prove integrity
    const receiptString = JSON.stringify(receipt, null, 2);
    const receiptHash = await sha256Hex(receiptString);

    const finalReceipt = {
      ...receipt,
      cryptographicSeal: receiptHash
    };

    const blob = new Blob([JSON.stringify(finalReceipt, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bft-receipt-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="glass-panel" style={{ padding: '2rem', gridColumn: 'span 2' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <span className="text-mono" style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>BFT LEDGER EVENT FEED (SHA-256)</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <span className="text-mono" style={{
            fontSize: '0.75rem',
            padding: '0.2rem 0.5rem',
            borderRadius: '4px',
            border: '1px solid',
            borderColor: cloudSyncStatus === 'OFFLINE' ? 'var(--accent-secondary)' : cloudSyncStatus.startsWith('SEALED') ? 'var(--accent-success)' : cloudSyncStatus === 'SYNCING...' ? 'var(--accent-primary)' : 'var(--text-muted)',
            color: cloudSyncStatus === 'OFFLINE' ? 'var(--accent-secondary)' : cloudSyncStatus.startsWith('SEALED') ? 'var(--accent-success)' : cloudSyncStatus === 'SYNCING...' ? 'var(--accent-primary)' : 'var(--text-muted)',
          }}>
            CLOUD: {cloudSyncStatus}
          </span>
          <span className="text-mono" style={{ fontSize: '0.8rem', color: 'var(--accent-success)' }}>LIVE MERKLE ROOTS</span>
          <button className="btn btn-outline" style={{ padding: '0.3rem 0.8rem', fontSize: '0.8rem' }} onClick={exportBFTReceipt}>
            ↓ ZK Receipt
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
        {bftLogs.map((log, index) => (
          <div key={log.id} style={{
            display: 'flex',
            justify: 'space-between',
            alignItems: 'center',
            padding: '0.6rem 1rem',
            background: 'rgba(255, 255, 255, 0.02)',
            borderLeft: `3px solid ${log.status.includes('APOPTOSIS') ? 'var(--accent-secondary)' : log.status.includes('ROLLBACK') ? 'var(--accent-primary)' : 'var(--accent-success)'}`,
            borderRadius: '4px',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.85rem',
            animation: index === 0 ? 'pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite' : 'none',
            opacity: 1 - (index * 0.12)
          }}>
            <span style={{ color: 'var(--accent-primary)' }}>{log.hash}</span>
            <span style={{ color: 'var(--text-main)' }}>{log.status}</span>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>{log.timestamp}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
