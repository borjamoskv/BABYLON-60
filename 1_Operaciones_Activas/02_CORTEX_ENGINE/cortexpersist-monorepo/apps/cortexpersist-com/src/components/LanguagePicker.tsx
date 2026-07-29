import React, { useState, useEffect } from 'react';
import { Locale, translations, detectLocale } from '../lib/i18n';

export default function LanguagePicker({ onLocaleChange }: { onLocaleChange?: (locale: Locale) => void }) {
  const [currentLocale, setCurrentLocale] = useState<Locale>('en');

  useEffect(() => {
    const detected = detectLocale();
    setCurrentLocale(detected);
    if (onLocaleChange) onLocaleChange(detected);
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newLoc = e.target.value as Locale;
    setCurrentLocale(newLoc);
    if (onLocaleChange) onLocaleChange(newLoc);
  };

  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '6px',
      background: 'rgba(255, 255, 255, 0.05)',
      border: '1px solid rgba(255, 255, 255, 0.15)',
      borderRadius: '6px',
      padding: '2px 8px',
      fontFamily: 'monospace',
      fontSize: '0.75rem',
      color: '#FFF'
    }}>
      <span>🌐</span>
      <select
        value={currentLocale}
        onChange={handleChange}
        style={{
          background: 'transparent',
          color: '#FFF',
          border: 'none',
          outline: 'none',
          cursor: 'pointer',
          fontFamily: 'monospace',
          fontSize: '0.75rem',
          fontWeight: 600
        }}
      >
        <option value="en" style={{ background: '#0A0A10', color: '#FFF' }}>English (US/Global)</option>
        <option value="es" style={{ background: '#0A0A10', color: '#FFF' }}>Español (ES/LATAM)</option>
        <option value="pt" style={{ background: '#0A0A10', color: '#FFF' }}>Português (BR/PT)</option>
        <option value="de" style={{ background: '#0A0A10', color: '#FFF' }}>Deutsch (DE)</option>
        <option value="fr" style={{ background: '#0A0A10', color: '#FFF' }}>Français (FR)</option>
        <option value="ja" style={{ background: '#0A0A10', color: '#FFF' }}>日本語 (JA)</option>
      </select>
    </div>
  );
}
