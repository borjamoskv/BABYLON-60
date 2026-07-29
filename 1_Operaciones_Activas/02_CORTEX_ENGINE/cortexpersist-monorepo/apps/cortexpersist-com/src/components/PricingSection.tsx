import React, { useState, useEffect } from 'react';
import { Locale, translations, detectLocale } from '../lib/i18n';

export default function PricingSection({ locale }: { locale?: Locale }) {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('annual');
  const [activeLocale, setActiveLocale] = useState<Locale>('en');

  useEffect(() => {
    setActiveLocale(locale || detectLocale());
  }, [locale]);

  const t = translations[activeLocale] || translations.en;

  const openCheckout = (planName: string, price: string) => {
    if (typeof window !== 'undefined') {
      if (planName.includes('Enterprise')) {
        window.location.href = `mailto:borja@babylon60.com?subject=Enterprise%20Sovereign%20License%20Request%20BABYLON%2060&body=Hi%20Borja,%20we%20are%20interested%20in%20the%20Enterprise%20Sovereign%20tier%20($${price}/mo).`;
        return;
      }
      window.dispatchEvent(
        new CustomEvent('open-checkout', {
          detail: { plan: planName, price: price }
        })
      );
    }
  };

  return (
    <section id="pricing" style={{ padding: '100px 20px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ textAlign: 'center', marginBottom: '60px' }}>
        <div style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: '0.8rem',
          color: '#2B3BE5',
          letterSpacing: '0.2em',
          textTransform: 'uppercase',
          marginBottom: '1rem'
        }}>
          ⚡ COMMERCIAL EXERGY TRANSDUCTION
        </div>
        <h2 style={{ fontSize: 'clamp(2.2rem, 5vw, 3.5rem)', fontWeight: 800, color: '#FFF', margin: '0 0 1rem' }}>
          {t.pricingTitle}
        </h2>
        <p style={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: '1.1rem', maxWidth: '650px', margin: '0 auto' }}>
          {t.pricingSub}
        </p>

        {/* Toggle billing cycle */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          background: 'rgba(255, 255, 255, 0.05)',
          padding: '4px',
          borderRadius: '999px',
          marginTop: '2rem',
          border: '1px solid rgba(255, 255, 255, 0.1)'
        }}>
          <button
            onClick={() => setBillingCycle('monthly')}
            style={{
              background: billingCycle === 'monthly' ? '#2B3BE5' : 'transparent',
              color: '#FFF',
              border: 'none',
              padding: '0.5rem 1.2rem',
              borderRadius: '999px',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.85rem'
            }}
          >
            {t.monthly}
          </button>
          <button
            onClick={() => setBillingCycle('annual')}
            style={{
              background: billingCycle === 'annual' ? '#2B3BE5' : 'transparent',
              color: '#FFF',
              border: 'none',
              padding: '0.5rem 1.2rem',
              borderRadius: '999px',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '0.85rem'
            }}
          >
            {t.annual}
          </button>
        </div>
      </div>

      {/* Pricing Cards Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '30px',
        alignItems: 'stretch'
      }}>
        {/* Tier 1: Community */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: '16px',
          padding: '2.5rem',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between'
        }}>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#00E676', fontFamily: 'monospace', fontWeight: 700, marginBottom: '0.5rem' }}>
              SOVEREIGN OPEN SOURCE
            </div>
            <h3 style={{ fontSize: '1.8rem', color: '#FFF', margin: '0 0 1rem' }}>{t.communityTitle}</h3>
            <div style={{ fontSize: '3rem', fontWeight: 900, color: '#FFF', marginBottom: '1.5rem' }}>
              $0 <span style={{ fontSize: '1rem', color: 'rgba(255,255,255,0.5)', fontWeight: 400 }}>/ forever</span>
            </div>
            <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.9rem', lineHeight: '1.5', marginBottom: '2rem' }}>
              {t.communityDesc}
            </p>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, color: 'rgba(255,255,255,0.8)', fontSize: '0.9rem', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <li>✓ Individual Free License</li>
              <li>✓ Local SQLite + WAL Engine</li>
              <li>✓ BFT Idempotency Invariant</li>
              <li>✓ Community Support</li>
            </ul>
          </div>
          <a
            href="https://github.com/borjamoskv/Cortex-Persist"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'block',
              textAlign: 'center',
              background: 'rgba(255, 255, 255, 0.08)',
              color: '#FFF',
              padding: '1rem',
              borderRadius: '8px',
              textDecoration: 'none',
              fontWeight: 700,
              marginTop: '2.5rem'
            }}
          >
            {t.communityCta}
          </a>
        </div>

        {/* Tier 2: Pro Agent Team (Featured) */}
        <div style={{
          background: 'linear-gradient(180deg, rgba(43, 59, 229, 0.15) 0%, rgba(10, 10, 20, 0.9) 100%)',
          border: '2px solid #2B3BE5',
          borderRadius: '16px',
          padding: '2.5rem',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          position: 'relative',
          boxShadow: '0 0 40px rgba(43, 59, 229, 0.3)'
        }}>
          <div style={{
            position: 'absolute',
            top: '-14px',
            left: '50%',
            transform: 'translateX(-50%)',
            background: '#2B3BE5',
            color: '#FFF',
            padding: '4px 16px',
            borderRadius: '999px',
            fontSize: '0.75rem',
            fontWeight: 800,
            letterSpacing: '0.1em'
          }}>
            {t.mostPopular}
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#2B3BE5', fontFamily: 'monospace', fontWeight: 700, marginBottom: '0.5rem' }}>
              COMMERCIAL AGENT TEAMS
            </div>
            <h3 style={{ fontSize: '1.8rem', color: '#FFF', margin: '0 0 1rem' }}>{t.proTitle}</h3>
            <div style={{ fontSize: '3rem', fontWeight: 900, color: '#FFF', marginBottom: '1.5rem' }}>
              {billingCycle === 'annual' ? '$39' : '$49'} <span style={{ fontSize: '1rem', color: 'rgba(255,255,255,0.5)', fontWeight: 400 }}>/ mo / agent</span>
            </div>
            <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.9rem', lineHeight: '1.5', marginBottom: '2rem' }}>
              {t.proDesc}
            </p>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, color: '#FFF', fontSize: '0.9rem', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <li>✓ Up to 10 Autonomous Agents</li>
              <li>✓ 1,000,000 Signed Events / mo</li>
              <li>✓ Guaranteed Latency &lt;5ms</li>
              <li>✓ Real-Time Telemetry (C5-REAL)</li>
              <li>✓ 24/7 Priority Support</li>
            </ul>
          </div>
          <button
            onClick={() => openCheckout('Pro Team', billingCycle === 'annual' ? '39' : '49')}
            style={{
              width: '100%',
              background: '#2B3BE5',
              color: '#FFF',
              border: 'none',
              padding: '1rem',
              borderRadius: '8px',
              fontWeight: 700,
              fontSize: '1rem',
              cursor: 'pointer',
              marginTop: '2.5rem',
              boxShadow: '0 0 20px rgba(43, 59, 229, 0.5)'
            }}
          >
            {t.proCta}
          </button>
        </div>

        {/* Tier 3: Enterprise Sovereign */}
        <div style={{
          background: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '16px',
          padding: '2.5rem',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between'
        }}>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#FF9F1C', fontFamily: 'monospace', fontWeight: 700, marginBottom: '0.5rem' }}>
              EU AI ACT COMPLIANCE
            </div>
            <h3 style={{ fontSize: '1.8rem', color: '#FFF', margin: '0 0 1rem' }}>{t.enterpriseTitle}</h3>
            <div style={{ fontSize: '3rem', fontWeight: 900, color: '#FFF', marginBottom: '1.5rem' }}>
              $1,499 <span style={{ fontSize: '1rem', color: 'rgba(255,255,255,0.5)', fontWeight: 400 }}>/ mo</span>
            </div>
            <p style={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.9rem', lineHeight: '1.5', marginBottom: '2rem' }}>
              {t.enterpriseDesc}
            </p>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, color: 'rgba(255,255,255,0.8)', fontSize: '0.9rem', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <li>✓ Dedicated GCP / WIF Allocation</li>
              <li>✓ EU AI Act Audit-Trail Certificate (Art. 12)</li>
              <li>✓ Unlimited Agents &amp; Events</li>
              <li>✓ Contractual 99.99% SLA Guarantee</li>
              <li>✓ Dedicated Account Manager &amp; 24/7 Support</li>
            </ul>
          </div>
          <button
            onClick={() => openCheckout('Enterprise Sovereign', '1499')}
            style={{
              width: '100%',
              background: 'rgba(255, 255, 255, 0.1)',
              color: '#FFF',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              padding: '1rem',
              borderRadius: '8px',
              fontWeight: 700,
              fontSize: '1rem',
              cursor: 'pointer',
              marginTop: '2.5rem'
            }}
          >
            {t.enterpriseCta}
          </button>
        </div>
      </div>
    </section>
  );
}
