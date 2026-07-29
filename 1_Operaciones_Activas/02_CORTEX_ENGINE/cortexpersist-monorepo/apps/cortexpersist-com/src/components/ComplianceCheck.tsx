// C5-REAL EXERGY CERTIFIED
import React, { useState } from 'react';

export default function ComplianceCheck() {
  const [q1, setQ1] = useState<boolean | null>(null); // Has tamper-evident ledger?
  const [q2, setQ2] = useState<boolean | null>(null); // Ed25519/SHA3-256 signed?
  const [q3, setQ3] = useState<boolean | null>(null); // Under <5ms latency?
  const [q4, setQ4] = useState<boolean | null>(null); // Zero-cloud audit local capability?

  const answers = [q1, q2, q3, q4];
  const answeredCount = answers.filter(a => a !== null).length;
  const passCount = answers.filter(a => a === true).length;
  const score = answeredCount === 0 ? 0 : Math.round((passCount / 4) * 100);

  const getScoreColor = () => {
    if (score >= 100) return '#00E676';
    if (score >= 50) return '#FF9F1C';
    return '#FF5252';
  };

  return (
    <div style={{
      maxWidth: '850px',
      margin: '0 auto',
      background: 'rgba(15, 15, 25, 0.85)',
      border: '1px solid rgba(255, 255, 255, 0.12)',
      borderRadius: '16px',
      padding: '2.5rem',
      boxShadow: '0 25px 60px rgba(0,0,0,0.6)',
      color: '#FFF'
    }}>
      <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
        <div style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: '0.8rem',
          color: '#FF9F1C',
          letterSpacing: '0.2em',
          textTransform: 'uppercase',
          marginBottom: '0.5rem'
        }}>
          🛡️ EU AI ACT ARTICLE 12 READINESS CALCULATOR
        </div>
        <h3 style={{ fontSize: '1.8rem', fontWeight: 800, margin: '0 0 0.5rem' }}>
          Evaluate Your AI Agent Audit-Trail Compliance
        </h3>
        <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.95rem' }}>
          By August 2026, non-compliant high-risk AI deployments face fines up to €30M or 6% of global turnover.
        </p>
      </div>

      {/* Score Gauge */}
      <div style={{
        background: 'rgba(0,0,0,0.4)',
        border: `2px solid ${getScoreColor()}`,
        borderRadius: '12px',
        padding: '1.5rem',
        textAlign: 'center',
        marginBottom: '2rem',
        transition: 'all 0.3s ease'
      }}>
        <div style={{ fontSize: '0.85rem', color: 'rgba(255,255,255,0.6)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          Compliance Readiness Score
        </div>
        <div style={{ fontSize: '3.5rem', fontWeight: 900, color: getScoreColor() }}>
          {score}%
        </div>
        <div style={{ fontSize: '0.9rem', color: '#E0E0E0', marginTop: '0.3rem' }}>
          {score === 100 ? '✅ 100% EU AI Act Compliant (BABYLON 60 Certified)' :
           score >= 50 ? '⚠️ Moderate Compliance Risk — Immutable Ledger Needed' :
           '🔴 High Regulatory Liability — Vulnerable to €30M Fine'}
        </div>
      </div>

      {/* Checklist Questions */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '2rem' }}>

        {/* Q1 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '8px' }}>
          <span style={{ fontSize: '0.95rem' }}>1. Does your AI memory log every decision with a tamper-evident hash chain?</span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={() => setQ1(true)} style={{ background: q1 === true ? '#00E676' : 'rgba(255,255,255,0.1)', color: q1 === true ? '#000' : '#FFF', border: 'none', padding: '0.4rem 1rem', borderRadius: '4px', cursor: 'pointer', fontWeight: 700 }}>YES</button>
            <button onClick={() => setQ1(false)} style={{ background: q1 === false ? '#FF5252' : 'rgba(255,255,255,0.1)', color: '#FFF', border: 'none', padding: '0.4rem 1rem', borderRadius: '4px', cursor: 'pointer', fontWeight: 700 }}>NO</button>
          </div>
        </div>

        {/* Q2 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '8px' }}>
          <span style={{ fontSize: '0.95rem' }}>2. Are events cryptographically signed with Ed25519/SHA3-256 signatures?</span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={() => setQ2(true)} style={{ background: q2 === true ? '#00E676' : 'rgba(255,255,255,0.1)', color: q2 === true ? '#000' : '#FFF', border: 'none', padding: '0.4rem 1rem', borderRadius: '4px', cursor: 'pointer', fontWeight: 700 }}>YES</button>
            <button onClick={() => setQ2(false)} style={{ background: q2 === false ? '#FF5252' : 'rgba(255,255,255,0.1)', color: '#FFF', border: 'none', padding: '0.4rem 1rem', borderRadius: '4px', cursor: 'pointer', fontWeight: 700 }}>NO</button>
          </div>
        </div>

        {/* Q3 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '8px' }}>
          <span style={{ fontSize: '0.95rem' }}>3. Can your audit trail verify history with sub-5ms latency in production?</span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={() => setQ3(true)} style={{ background: q3 === true ? '#00E676' : 'rgba(255,255,255,0.1)', color: q3 === true ? '#000' : '#FFF', border: 'none', padding: '0.4rem 1rem', borderRadius: '4px', cursor: 'pointer', fontWeight: 700 }}>YES</button>
            <button onClick={() => setQ3(false)} style={{ background: q3 === false ? '#FF5252' : 'rgba(255,255,255,0.1)', color: '#FFF', border: 'none', padding: '0.4rem 1rem', borderRadius: '4px', cursor: 'pointer', fontWeight: 700 }}>NO</button>
          </div>
        </div>

        {/* Q4 */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.03)', padding: '1rem', borderRadius: '8px' }}>
          <span style={{ fontSize: '0.95rem' }}>4. Is your audit engine local-first (0% third-party cloud lock-in)?</span>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={() => setQ4(true)} style={{ background: q4 === true ? '#00E676' : 'rgba(255,255,255,0.1)', color: q4 === true ? '#000' : '#FFF', border: 'none', padding: '0.4rem 1rem', borderRadius: '4px', cursor: 'pointer', fontWeight: 700 }}>YES</button>
            <button onClick={() => setQ4(false)} style={{ background: q4 === false ? '#FF5252' : 'rgba(255,255,255,0.1)', color: '#FFF', border: 'none', padding: '0.4rem 1rem', borderRadius: '4px', cursor: 'pointer', fontWeight: 700 }}>NO</button>
          </div>
        </div>
      </div>

      {/* Call to Action */}
      <div style={{ textAlign: 'center' }}>
        <a
          href="#pricing"
          style={{
            display: 'inline-block',
            background: '#2B3BE5',
            color: '#FFF',
            padding: '1rem 2.5rem',
            borderRadius: '8px',
            textDecoration: 'none',
            fontWeight: 800,
            fontSize: '1.05rem',
            boxShadow: '0 0 30px rgba(43,59,229,0.5)'
          }}
        >
          Fix Compliance with BABYLON 60 Enterprise ➔
        </a>
      </div>
    </div>
  );
}
