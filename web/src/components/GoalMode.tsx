import React from 'react';
import { Target, Zap, Clock, Code } from 'lucide-react';

export const GoalMode: React.FC = () => {
  return (
    <div className="animate-fade-in">
      <div className="view-header">
        <div>
          <h1 className="view-title">Goal Mode</h1>
          <p className="view-subtitle">Autonomous agents working tirelessly until objective completion.</p>
        </div>
        <button className="btn-primary" style={{ background: '#ec4899', boxShadow: '0 4px 15px rgba(236, 72, 153, 0.4)' }}>
          <Zap size={16} /> Ignite Goal
        </button>
      </div>

      <div className="grid-2">
        <div className="glass-panel">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem', color: '#ec4899' }}>
            <Target size={20} /> Current Directive
          </h3>
          <div style={{ padding: '1rem', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', border: '1px solid var(--border)', fontFamily: 'var(--font-mono)', marginBottom: '1.5rem' }}>
            &gt; Refactor BFT consensus logic in babylon60.rs to ensure zero memory leaks during high-load swarm operations.
          </div>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            <span>Progress: Code Analysis Phase</span>
            <span>45%</span>
          </div>
          <div className="progress-bg" style={{ height: '8px', marginBottom: '2rem' }}>
            <div className="progress-fill" style={{ width: '45%', background: 'linear-gradient(90deg, #ec4899, #8b5cf6)', boxShadow: '0 0 15px rgba(236, 72, 153, 0.5)' }}></div>
          </div>

          <div style={{ display: 'flex', gap: '1rem' }}>
            <div style={{ flex: 1, padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Time Elapsed</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Clock size={16} /> 02:45:12
              </div>
            </div>
            <div style={{ flex: 1, padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Lines Changed</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Code size={16} /> +412 / -105
              </div>
            </div>
          </div>
        </div>

        <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ marginBottom: '1.5rem' }}>Agent Log Stream</h3>
          <div style={{ 
            flex: 1, 
            background: '#000', 
            borderRadius: '8px', 
            padding: '1rem', 
            fontFamily: 'var(--font-mono)', 
            fontSize: '0.875rem',
            color: '#a1a1aa',
            overflowY: 'auto',
            border: '1px solid var(--border)',
            display: 'flex',
            flexDirection: 'column',
            gap: '0.5rem'
          }}>
            <div><span style={{ color: '#ec4899' }}>[SYSTEM]</span> Goal mode activated. Spawned agent Alpha.</div>
            <div><span style={{ color: '#3b82f6' }}>[Alpha]</span> Reading babylon60.rs...</div>
            <div><span style={{ color: '#3b82f6' }}>[Alpha]</span> Identified BFT logic at L245-L310.</div>
            <div><span style={{ color: '#3b82f6' }}>[Alpha]</span> Spawning Subagent Beta for memory profiling.</div>
            <div><span style={{ color: '#10b981' }}>[Beta]</span> Profiling complete. Leak detected in queue loop.</div>
            <div><span style={{ color: '#3b82f6' }}>[Alpha]</span> Applying fix... running `cargo check`.</div>
            <div style={{ color: '#f59e0b' }}>[Alpha] Cargo check failed. Compilation error on L280.</div>
            <div><span style={{ color: '#3b82f6' }}>[Alpha]</span> Iterating on fix for L280... <span className="status-dot active" style={{ marginLeft: '4px' }}></span></div>
          </div>
        </div>
      </div>
    </div>
  );
};
