"use client";

import React, { useState } from 'react';

type Block = {
  index: number;
  hash: string;
  prevHash: string;
  timestamp: number;
  data?: string;
};

type HashChainViewerProps = {
  blocks: Block[];
  maxVisible?: number;
};

export function HashChainViewer({ blocks, maxVisible = 5 }: HashChainViewerProps) {
  const [hoveredHash, setHoveredHash] = useState<string | null>(null);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);
  
  const visible = blocks.slice(-maxVisible);

  const handleCopy = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 1000);
  };

  return (
    <div style={{ 
      fontFamily: 'monospace', 
      fontSize: '11px', 
      display: 'flex', 
      flexDirection: 'column', 
      gap: '12px',
      position: 'relative',
      paddingLeft: '16px'
    }}>
      {/* Vertical Timeline Linkage Line */}
      {visible.length > 1 && (
        <div style={{
          position: 'absolute',
          left: '6px',
          top: '12px',
          bottom: '12px',
          width: '1px',
          background: 'linear-gradient(to bottom, rgba(255,255,255,0.05) 0%, #2B3BE5 50%, #00ff88 100%)',
          zIndex: 0
        }} />
      )}

      {visible.map((block, i) => {
        const isLatest = i === visible.length - 1;
        const isHovered = hoveredHash === block.hash;
        
        return (
          <div 
            key={block.hash} 
            onMouseEnter={() => setHoveredHash(block.hash)}
            onMouseLeave={() => setHoveredHash(null)}
            onClick={() => handleCopy(block.hash)}
            style={{
              display: 'flex', 
              alignItems: 'center', 
              gap: '12px',
              padding: '8px 12px',
              background: isLatest 
                ? 'rgba(0, 255, 136, 0.03)' 
                : isHovered 
                  ? 'rgba(43, 59, 229, 0.05)'
                  : 'rgba(255,255,255,0.01)',
              border: isHovered
                ? '1px solid rgba(43, 59, 229, 0.3)'
                : isLatest
                  ? '1px solid rgba(0, 255, 136, 0.2)'
                  : '1px solid rgba(255,255,255,0.04)',
              borderRadius: '3px',
              position: 'relative',
              cursor: 'pointer',
              zIndex: 1,
              transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
              boxShadow: isHovered ? '0 4px 12px rgba(0,0,0,0.5)' : 'none'
            }}
            title="Click to copy hash"
          >
            {/* Timeline node dot */}
            <div style={{
              position: 'absolute',
              left: '-13px',
              top: '50%',
              transform: 'translateY(-50%)',
              width: '7px',
              height: '7px',
              borderRadius: '50%',
              background: isLatest ? '#00ff88' : '#2B3BE5',
              border: '2px solid #000',
              boxShadow: isLatest ? '0 0 8px #00ff88' : 'none',
              transition: 'all 0.3s ease'
            }} />

            <span style={{ color: isLatest ? '#00ff88' : '#737373', fontWeight: isLatest ? 'bold' : 'normal' }}>
              #{block.index}
            </span>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ color: isLatest ? '#00ff88' : '#e5e5e5', fontWeight: '500' }}>
                  {block.hash.slice(0, 16)}…
                </span>
                {copiedHash === block.hash && (
                  <span style={{ color: '#00ff88', fontSize: '9px', fontWeight: 'bold' }}>COPIED</span>
                )}
              </div>
              <span style={{ color: '#404040', fontSize: '9px' }}>
                prev: {block.prevHash.slice(0, 16)}…
              </span>
            </div>

            <span style={{ 
              color: '#555', 
              marginLeft: 'auto', 
              fontSize: '10px',
              opacity: isHovered ? 1 : 0.7 
            }}>
              {new Date(block.timestamp).toISOString().slice(11, 19)}
            </span>
          </div>
        );
      })}
    </div>
  );
}
