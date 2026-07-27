"use client";

import React, { useState } from 'react';

export interface CrossDomainCTAProps {
  href: string;
  target?: '_blank' | '_self';
  children: React.ReactNode;
}

export function CrossDomainCTA({ href, target = '_blank', children }: CrossDomainCTAProps) {
  const [hovered, setHovered] = useState(false);

  return (
    <a
      href={href}
      target={target}
      rel={target === '_blank' ? 'noopener noreferrer' : undefined}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.75rem',
        padding: '0.6rem 1.2rem',
        background: hovered ? '#2B3BE5' : '#0A0A0A',
        color: hovered ? '#000' : '#2B3BE5',
        border: hovered ? '1px solid #2B3BE5' : '1px solid rgba(43, 59, 229, 0.5)',
        borderRadius: '3px',
        textDecoration: 'none',
        fontFamily: 'monospace',
        fontSize: '0.75rem',
        fontWeight: 'bold',
        textTransform: 'uppercase',
        letterSpacing: '0.1em',
        boxShadow: hovered ? '0 0 20px rgba(43, 59, 229, 0.3)' : 'none',
        transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
        cursor: 'pointer',
        boxSizing: 'border-box',
        transform: hovered ? 'scale(1.02)' : 'scale(1)'
      }}
    >
      <span>{children}</span>
      <svg
        width="12"
        height="12"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        style={{
          transform: hovered ? 'translateX(3px)' : 'translateX(0)',
          transition: 'transform 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
          flexShrink: 0
        }}
      >
        <line x1="5" y1="12" x2="19" y2="12" />
        <polyline points="12 5 19 12 12 19" />
      </svg>
    </a>
  );
}
