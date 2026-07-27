"use client";

import React, { useState } from 'react';

type CortexBadgeProps = {
  status: 'verified' | 'pending' | 'anchored';
  hash?: string;
  className?: string;
};

const statusColors = {
  verified: '#00ff88',
  pending: '#ffaa00',
  anchored: '#0088ff',
} as const;

export function CortexBadge({ status, hash, className }: CortexBadgeProps) {
  const [hovered, setHovered] = useState(false);
  const color = statusColors[status];
  
  return (
    <>
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes cortex-pulse {
          0% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.4); opacity: 0.4; }
          100% { transform: scale(1); opacity: 1; }
        }
      `}} />
      <div
        className={className}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '4px 12px',
          borderRadius: '3px',
          border: `1px solid ${color}`,
          background: hovered ? 'rgba(0,0,0,0.95)' : 'rgba(0,0,0,0.6)',
          boxShadow: hovered ? `0 0 12px ${color}33` : 'none',
          fontFamily: 'monospace',
          fontSize: '11px',
          color: color,
          cursor: 'default',
          transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
        }}
      >
        <div style={{ position: 'relative', width: 6, height: 6, display: 'inline-block' }}>
          <span style={{ 
            position: 'absolute',
            width: '100%', 
            height: '100%', 
            borderRadius: '50%', 
            background: color, 
            display: 'inline-block',
            animation: 'cortex-pulse 2s infinite ease-in-out'
          }} />
        </div>
        <span>CORTEX::{status.toUpperCase()}</span>
        {hash && <span style={{ opacity: 0.5, borderLeft: '1px solid rgba(255,255,255,0.1)', paddingLeft: '6px', fontSize: '10px' }}>{hash.slice(0, 8)}…</span>}
      </div>
    </>
  );
}
