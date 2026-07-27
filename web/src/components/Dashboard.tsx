import React from 'react';
import { Activity, Server, Cpu, Database, AlertCircle, CheckCircle2 } from 'lucide-react';

export const Dashboard: React.FC = () => {
  return (
    <div className="animate-fade-in">
      <div className="view-header">
        <div>
          <h1 className="view-title">Command Center</h1>
          <p className="view-subtitle">Real-time telemetry and task orchestration overview.</p>
        </div>
        <div className="flex gap-4">
          <button className="btn-secondary"><Database size={16} /> Sync Logs</button>
          <button className="btn-primary"><Activity size={16} /> New Task</button>
        </div>
      </div>

      <div className="grid-4" style={{ marginBottom: '2rem' }}>
        <div className="glass-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Active Agents</span>
            <Server size={18} style={{ color: 'var(--accent)' }} />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 700 }}>24 / 32</div>
          <div className="progress-bg" style={{ marginTop: '1rem' }}>
            <div className="progress-fill" style={{ width: '75%' }}></div>
          </div>
        </div>
        <div className="glass-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>CPU Load</span>
            <Cpu size={18} style={{ color: 'var(--warning)' }} />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 700 }}>68%</div>
          <div className="progress-bg" style={{ marginTop: '1rem' }}>
            <div className="progress-fill" style={{ width: '68%', background: 'var(--warning)', boxShadow: '0 0 10px var(--warning)' }}></div>
          </div>
        </div>
        <div className="glass-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Tasks Completed</span>
            <CheckCircle2 size={18} style={{ color: 'var(--success)' }} />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 700 }}>1,492</div>
          <div style={{ fontSize: '0.875rem', color: 'var(--success)', marginTop: '0.5rem' }}>+12% vs last hour</div>
        </div>
        <div className="glass-panel">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>System Alerts</span>
            <AlertCircle size={18} style={{ color: 'var(--danger)' }} />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 700 }}>3</div>
          <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>2 warnings, 1 critical</div>
        </div>
      </div>

      <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>Active Tasks</h2>
      <div className="glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Task ID</th>
              <th>Assigned Agent</th>
              <th>Status</th>
              <th>Progress</th>
              <th>Runtime</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={{ fontFamily: 'var(--font-mono)' }}>TSK-0x1A4B</td>
              <td>Alpha-Swarm-1</td>
              <td><span className="badge blue">Processing</span></td>
              <td>
                <div className="progress-bg" style={{ width: '100px' }}>
                  <div className="progress-fill" style={{ width: '45%' }}></div>
                </div>
              </td>
              <td>14m 23s</td>
            </tr>
            <tr>
              <td style={{ fontFamily: 'var(--font-mono)' }}>TSK-0x1A4C</td>
              <td>Beta-Worker-2</td>
              <td><span className="badge amber">Yielded</span></td>
              <td>
                <div className="progress-bg" style={{ width: '100px' }}>
                  <div className="progress-fill" style={{ width: '89%', background: 'var(--warning)', boxShadow: 'none' }}></div>
                </div>
              </td>
              <td>03m 12s</td>
            </tr>
            <tr>
              <td style={{ fontFamily: 'var(--font-mono)' }}>TSK-0x1A4D</td>
              <td>Omega-Sync-1</td>
              <td><span className="badge green">Completed</span></td>
              <td>
                <div className="progress-bg" style={{ width: '100px' }}>
                  <div className="progress-fill" style={{ width: '100%', background: 'var(--success)', boxShadow: '0 0 10px var(--success-glow)' }}></div>
                </div>
              </td>
              <td>45m 01s</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};
