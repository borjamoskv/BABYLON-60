"use client";

import React, { useState, useEffect } from 'react';

export interface CryptographicAnchorProps {
  findingId: string;
  merkleRoot: string;
  signature: string;
  isVerified: boolean;
  timestamp: string;
}

export function CryptographicAnchor({
  findingId,
  merkleRoot,
  signature,
  isVerified,
  timestamp,
}: CryptographicAnchorProps) {
  const [hovered, setHovered] = useState(false);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [glitch, setGlitch] = useState(false);

  useEffect(() => {
    if (!hovered) return;
    const interval = setInterval(() => {
      setGlitch(true);
      setTimeout(() => setGlitch(false), 50);
    }, 2000);
    return () => clearInterval(interval);
  }, [hovered]);

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 1500);
  };

  const renderIdenticon = () => {
    const pixels = [];
    const sigStr = signature || "default_signature_anchor_seed_string";
    for (let i = 0; i < 64; i++) {
      const charCode = sigStr.charCodeAt(i % sigStr.length);
      const isBlue = (charCode * (i + 7)) % 7 === 0;
      const isGreen = (charCode * (i + 13)) % 11 === 0 && isVerified;
      const opacity = ((charCode * (i + 3)) % 10) / 10 * 0.7 + 0.3;
      
      let color = '#1a1a1a';
      let shadow = 'none';
      if (isGreen) {
        color = '#00ff88';
        shadow = hovered ? '0 0 5px #00ff88' : 'none';
      } else if (isBlue) {
        color = '#2B3BE5';
        shadow = hovered ? '0 0 5px #2B3BE5' : 'none';
      }

      pixels.push(
        <div
          key={i}
          style={{
            width: hovered ? '5px' : '4px',
            height: hovered ? '5px' : '4px',
            background: color,
            opacity: opacity,
            borderRadius: hovered ? '0px' : '1px',
            boxShadow: shadow,
            transition: 'all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)'
          }}
        />
      );
    }
    return (
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(8, 1fr)',
        gap: '2px',
        padding: '6px',
        background: '#030303',
        border: '1px solid rgba(255,255,255,0.05)',
        width: '50px',
        height: '50px',
        alignItems: 'center',
        justifyItems: 'center'
      }}>
        {pixels}
      </div>
    );
  };

  return (
    <>
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes scanline {
          0% { transform: translateY(-100%); }
          100% { transform: translateY(100%); }
        }
        @keyframes pulse-glow {
          0% { box-shadow: 0 0 10px rgba(43, 59, 229, 0.1); }
          50% { box-shadow: 0 0 20px rgba(43, 59, 229, 0.3); }
          100% { box-shadow: 0 0 10px rgba(43, 59, 229, 0.1); }
        }
      `}} />
      <div 
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
        style={{
          width: '100%',
          border: hovered ? '1px solid rgba(43, 59, 229, 0.6)' : '1px solid rgba(255,255,255,0.1)',
          background: '#0A0A0A',
          padding: '1.5rem',
          color: '#fff',
          fontFamily: 'monospace',
          position: 'relative',
          overflow: 'hidden',
          boxSizing: 'border-box',
          transition: 'all 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
          transform: glitch ? 'translate(2px, -2px)' : 'none',
          animation: hovered && isVerified ? 'pulse-glow 2s infinite' : 'none',
        }}
      >
        {/* Animated Scanline Overlay */}
        <div style={{
          position: 'absolute',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'linear-gradient(to bottom, transparent, rgba(43, 59, 229, 0.05), transparent)',
          animation: 'scanline 4s linear infinite',
          pointerEvents: 'none',
          opacity: hovered ? 1 : 0
        }} />
        
        {/* Left Edge Neon Accent */}
        <div style={{
          position: 'absolute',
          top: 0, left: 0,
          width: '3px',
          height: '100%',
          background: isVerified ? '#00ff88' : '#2B3BE5',
          boxShadow: hovered ? `0 0 15px ${isVerified ? '#00ff88' : '#2B3BE5'}` : 'none',
          transition: 'all 0.4s ease'
        }} />

        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
          paddingBottom: '1rem',
          marginBottom: '1rem',
          position: 'relative',
          zIndex: 2
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {renderIdenticon()}
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <h3 style={{
                fontSize: '0.85rem',
                fontWeight: 700,
                letterSpacing: '0.15em',
                color: hovered ? '#ffffff' : '#a3a3a3',
                textTransform: 'uppercase',
                margin: 0,
                transition: 'color 0.3s ease'
              }}>
                Cortex Anchor
              </h3>
              <span style={{ fontSize: '0.65rem', color: '#555', letterSpacing: '0.1em', marginTop: '4px' }}>
                C5-REAL DATA SUBSTRATE
              </span>
            </div>
          </div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            fontSize: '0.7rem',
            fontWeight: 800,
            letterSpacing: '0.1em',
            padding: '0.35rem 0.75rem',
            background: isVerified ? 'rgba(0, 255, 136, 0.05)' : 'rgba(239, 68, 68, 0.05)',
            color: isVerified ? '#00ff88' : '#f87171',
            border: `1px solid ${isVerified ? 'rgba(0, 255, 136, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
            textShadow: isVerified && hovered ? '0 0 10px rgba(0,255,136,0.5)' : 'none',
            transition: 'all 0.3s ease'
          }}>
            {isVerified ? 'VERIFIED_ON_CHAIN' : 'UNVERIFIED_STATE'}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', fontSize: '0.75rem', position: 'relative', zIndex: 2 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <span style={{ color: '#555', display: 'block', marginBottom: '0.35rem', letterSpacing: '0.1em' }}>[ FINDING ID ]</span>
              <span style={{ color: '#e5e5e5', fontWeight: 600 }}>{findingId}</span>
            </div>
            <div>
              <span style={{ color: '#555', display: 'block', marginBottom: '0.35rem', letterSpacing: '0.1em' }}>[ TIMESTAMP UTC ]</span>
              <span style={{ color: '#e5e5e5', fontWeight: 600 }}>{timestamp}</span>
            </div>
          </div>
          
          <div 
            onClick={() => handleCopy(merkleRoot, 'merkle')}
            style={{ cursor: 'pointer', padding: '0.5rem', background: 'rgba(255,255,255,0.02)', border: '1px dashed rgba(255,255,255,0.1)' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
              <span style={{ color: '#555', letterSpacing: '0.1em' }}>[ MERKLE ROOT ]</span>
              {copiedKey === 'merkle' && <span style={{ color: '#00ff88', fontWeight: 'bold' }}>COPIED_TO_CLIPBOARD</span>}
            </div>
            <span style={{ 
              color: '#2B3BE5', 
              wordBreak: 'break-all',
              textShadow: hovered ? '0 0 8px rgba(43, 59, 229, 0.4)' : 'none',
              transition: 'all 0.3s ease'
            }}>{merkleRoot}</span>
          </div>

          <div 
            onClick={() => handleCopy(signature, 'sig')}
            style={{ cursor: 'pointer', padding: '0.5rem', background: 'rgba(255,255,255,0.02)', border: '1px dashed rgba(255,255,255,0.1)' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
              <span style={{ color: '#555', letterSpacing: '0.1em' }}>[ ED25519 SIGNATURE ]</span>
              {copiedKey === 'sig' && <span style={{ color: '#00ff88', fontWeight: 'bold' }}>COPIED_TO_CLIPBOARD</span>}
            </div>
            <span style={{ 
              color: '#a3a3a3', 
              wordBreak: 'break-all',
              transition: 'all 0.3s ease'
            }}>{signature}</span>
          </div>
        </div>
      </div>
    </>
  );
}
