import React from 'react';
import { Network, Users, ArrowUpRight, Cpu } from 'lucide-react';

export const SwarmOverview: React.FC = () => {
  return (
    <div className="animate-fade-in">
      <div className="view-header">
        <div>
          <h1 className="view-title">Swarm Intelligence</h1>
          <p className="view-subtitle">Multiplied productivity through concurrent multi-agent architecture.</p>
        </div>
        <button className="btn-secondary"><Users size={16} /> Manage Swarm</button>
      </div>

      <div className="grid-3" style={{ marginBottom: '2rem' }}>
        <div className="glass-panel" style={{ background: 'linear-gradient(135deg, rgba(79, 70, 229, 0.1) 0%, rgba(20, 20, 22, 0.6) 100%)' }}>
          <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Swarm Multiplier</div>
          <div style={{ fontSize: '3rem', fontWeight: 800, color: '#818cf8', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            14.2x <ArrowUpRight size={24} />
          </div>
          <div style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>Productivity equivalent vs single agent</div>
        </div>
        <div className="glass-panel">
          <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Network Topology</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, margin: '0.5rem 0' }}>Hierarchical</div>
          <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
            <div><span className="status-dot"></span> 1 Overlord</div>
            <div><span className="status-dot" style={{ background: '#3b82f6', boxShadow: 'none' }}></span> 8 Workers</div>
          </div>
        </div>
        <div className="glass-panel">
          <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Compute Allocation</div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, margin: '0.5rem 0' }}>Dynamic</div>
          <div className="progress-bg" style={{ height: '8px', marginTop: '1rem' }}>
            <div className="progress-fill" style={{ width: '82%', background: '#818cf8' }}></div>
          </div>
        </div>
      </div>

      <div className="glass-panel">
        <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
          <Network size={20} /> Active Swarm Nodes
        </h3>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {[
            { id: 'Node-Alpha-01', role: 'Orchestrator', status: 'Active', load: 45, color: 'blue' },
            { id: 'Node-Beta-12', role: 'Code Generator', status: 'Active', load: 92, color: 'amber' },
            { id: 'Node-Beta-13', role: 'Code Generator', status: 'Active', load: 88, color: 'amber' },
            { id: 'Node-Gamma-04', role: 'Test Runner', status: 'Idle', load: 5, color: 'green' },
            { id: 'Node-Delta-01', role: 'Reviewer', status: 'Active', load: 34, color: 'blue' }
          ].map((node) => (
            <div key={node.id} style={{ display: 'flex', alignItems: 'center', padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px solid var(--border)' }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{node.id}</div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>{node.role}</div>
              </div>
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span className={`badge ${node.color}`}>{node.status}</span>
              </div>
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <Cpu size={16} style={{ color: 'var(--text-muted)' }} />
                <div className="progress-bg" style={{ flex: 1, height: '6px' }}>
                  <div className="progress-fill" style={{ width: `${node.load}%`, background: node.load > 80 ? 'var(--warning)' : 'var(--accent)' }}></div>
                </div>
                <span style={{ fontSize: '0.875rem', width: '40px', textAlign: 'right' }}>{node.load}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
