// C5-REAL EXERGY CERTIFIED
import React from 'react';

export function IRPMembrane({ kernelState, applyStress, resetMembrane }) {
  const currentStateName = kernelState.cases()[kernelState.tag];
  let stateColor = 'var(--accent-primary)';
  let stateBg = 'rgba(43, 59, 229, 0.1)';

  if (currentStateName === 'Stable') {
    stateColor = 'var(--accent-success)';
    stateBg = 'rgba(0, 255, 102, 0.1)';
  } else if (currentStateName === 'Apoptosis') {
    stateColor = 'var(--accent-secondary)';
    stateBg = 'rgba(255, 0, 85, 0.2)';
  } else if (currentStateName === 'Rollback') {
    stateColor = 'var(--accent-primary)';
    stateBg = 'rgba(43, 59, 229, 0.2)';
  } else {
    stateColor = 'var(--text-main)';
    stateBg = 'rgba(255, 255, 255, 0.1)';
  }

  return (
    <div className="glass-panel animate-fade-in-up" style={{ padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span className="text-mono" style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>MEMBRANE STATE</span>
        <span className="text-mono" style={{
          padding: '0.2rem 0.6rem',
          borderRadius: '4px',
          fontSize: '0.8rem',
          backgroundColor: stateBg,
          color: stateColor,
          border: `1px solid ${stateColor}`,
          boxShadow: `0 0 10px ${stateBg}`
        }}>
          {currentStateName}
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
          <span>Entropy Level (e):</span>
          <span className="text-mono">{currentStateName === 'Stable' ? kernelState.fields[0].toFixed(4) : '0.0000'}</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
          <span>Variance (v):</span>
          <span className="text-mono">{currentStateName === 'Smoothing' ? kernelState.fields[0].toFixed(4) : '0.0000'}</span>
        </div>
        {currentStateName === 'Rollback' && (
          <div className="animate-fade-in-up" style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--accent-primary)' }}>
            <span>Target Hash:</span>
            <span className="text-mono">{kernelState.fields[0]}</span>
          </div>
        )}
        {currentStateName === 'Apoptosis' && (
          <div className="animate-fade-in-up" style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--accent-secondary)' }}>
            <span>Taint Log:</span>
            <span className="text-mono">{kernelState.fields[0]}</span>
          </div>
        )}
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '1rem' }}>
        <button className="btn btn-outline" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }} onClick={() => applyStress('C2_FriccionComputacional')}>
          + C2 Fricción
        </button>
        <button className="btn btn-outline" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }} onClick={() => applyStress('C3_FluctuacionTermica')}>
          + C3 Fluctuación
        </button>
        <button className="btn btn-outline" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', borderColor: 'var(--accent-primary)' }} onClick={() => applyStress('C4_DegradacionGeometrica')}>
          ⚡ C4 Rollback
        </button>
        <button className="btn btn-outline" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', borderColor: 'var(--accent-secondary)', color: 'var(--accent-secondary)' }} onClick={() => applyStress('C5_ColapsoOntologico')}>
          💥 C5 Colapso
        </button>
        <button className="btn btn-outline" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem', marginTop: '0.5rem', width: '100%' }} onClick={resetMembrane}>
          ↺ Reset Membrane
        </button>
      </div>
    </div>
  );
}
