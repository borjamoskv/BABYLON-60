"use client";

import React, { useState } from 'react';

type OuroborosBadgeProps = {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  protocol: string;
};

const severityColors = {
  critical: '#ff2244',
  high: '#ff6600',
  medium: '#ffcc00',
  low: '#44bbff',
  info: '#aaaaaa',
} as const;

export function OuroborosBadge({ id, severity, protocol }: OuroborosBadgeProps) {
  const [hovered, setHovered] = useState(false);
  const color = severityColors[severity];

  return (
    <>
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes ouroboros-rotate {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}} />
      <div 
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '12px',
          padding: '8px 14px',
          borderLeft: `3px solid ${color}`,
          background: hovered ? 'rgba(10,10,10,0.95)' : 'rgba(0,0,0,0.8)',
          borderTop: '1px solid rgba(255,255,255,0.02)',
          borderRight: '1px solid rgba(255,255,255,0.02)',
          borderBottom: '1px solid rgba(255,255,255,0.02)',
          boxShadow: hovered 
            ? `0 0 20px ${color}1c, inset 0 0 10px rgba(255,255,255,0.01)` 
            : '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          fontFamily: 'monospace',
          fontSize: '11px',
          transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
          cursor: 'default'
        }}
      >
        {/* Dynamic Ouroboros Loop SVG */}
        <svg 
          width="20" 
          height="20" 
          viewBox="0 0 24 24" 
          fill="none" 
          style={{
            transformOrigin: 'center',
            animation: hovered ? 'ouroboros-rotate 4s linear infinite' : 'none',
            transition: 'transform 0.5s ease',
            flexShrink: 0
          }}
        >
          <circle 
            cx="12" 
            cy="12" 
            r="9" 
            stroke="rgba(255,255,255,0.05)" 
            strokeWidth="1.5" 
          />
          <path 
            d="M12 3 A9 9 0 1 1 5.6 18.4" 
            stroke={color} 
            strokeWidth="1.8" 
            strokeLinecap="round"
          />
          <path 
            d="M6 18.5 L4.5 21 L8.5 20.5 Z" 
            fill={color} 
          />
        </svg>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <span style={{ color: color, fontWeight: 'bold', letterSpacing: '0.05em' }}>
            OUROBOROS // {severity.toUpperCase()}
          </span>
          <span style={{ color: '#888', fontSize: '10px' }}>{id}</span>
          <span style={{ color: '#555', fontSize: '9px' }}>{protocol}</span>
        </div>
      </div>
    </>
  );
}
