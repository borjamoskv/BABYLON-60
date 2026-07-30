"use client";

import React, { useState } from 'react';

type AuditEventCardProps = {
  id: string;
  type: string;
  auditor: string;
  timestamp: number;
  anchored: boolean;
  merkleRoot?: string;
  onClick?: () => void;
};

export function AuditEventCard({ id, type, auditor, timestamp, anchored, merkleRoot, onClick }: AuditEventCardProps) {
  const [hovered, setHovered] = useState(false);

  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        cursor: onClick ? 'pointer' : 'default',
        padding: '12px 16px',
        border: hovered
          ? `1px solid ${anchored ? '#00ff88' : '#2B3BE5'}`
          : `1px solid ${anchored ? 'rgba(0,255,136,0.2)' : 'rgba(255,255,255,0.08)'}`,
        borderRadius: '4px',
        background: hovered ? 'rgba(10,10,10,0.95)' : 'rgba(0,0,0,0.7)',
        boxShadow: hovered 
          ? `0 4px 20px ${anchored ? 'rgba(0,255,136,0.1)' : 'rgba(43,59,229,0.1)'}`
          : 'none',
        fontFamily: 'monospace',
        fontSize: '12px',
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
        transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
        transform: hovered ? 'translateY(-2px)' : 'none'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ color: anchored ? '#00ff88' : '#e5e5e5', fontWeight: 'bold' }}>{type}</span>
        {anchored && (
          <span style={{ 
            color: '#0088ff', 
            fontSize: '10px', 
            fontWeight: 'bold',
            display: 'flex',
            alignItems: 'center',
            gap: '4px'
          }}>
            <span style={{ display: 'inline-block', transform: hovered ? 'rotate(15deg)' : 'none', transition: 'transform 0.3s ease' }}>⚓</span>
            ANCHORED
          </span>
        )}
      </div>
      <span style={{ color: '#888' }}>{id}</span>
      <div style={{ display: 'flex', justifyContent: 'space-between', color: '#555', fontSize: '10px' }}>
        <span>by {auditor}</span>
        <span>{new Date(timestamp).toISOString()}</span>
      </div>
      {merkleRoot && (
        <span style={{ 
          color: hovered ? '#a3a3a3' : '#333', 
          fontSize: '10px', 
          borderTop: '1px solid rgba(255,255,255,0.04)', 
          paddingTop: '4px', 
          marginTop: '2px',
          transition: 'color 0.3s ease'
        }}>
          merkle: {merkleRoot.slice(0, 20)}…
        </span>
      )}
    </div>
  );
}
