import React from 'react';
import { CalendarClock, ArrowRight, Play, Settings2 } from 'lucide-react';

export const ScheduledTasks: React.FC = () => {
  return (
    <div className="animate-fade-in">
      <div className="view-header">
        <div>
          <h1 className="view-title">Scheduled Jobs</h1>
          <p className="view-subtitle">Automated workflows chronologically executed and pushed to targets.</p>
        </div>
        <button className="btn-primary"><CalendarClock size={16} /> New Schedule</button>
      </div>

      <div className="glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Cron Schedule</th>
              <th>Task Directive</th>
              <th>Target / Push Result To</th>
              <th>Next Run</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={{ fontFamily: 'var(--font-mono)' }}>0 0 * * *</td>
              <td>Nightly Data Sync (Market DB)</td>
              <td>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <ArrowRight size={14} style={{ color: 'var(--accent)' }} /> 
                  <span className="badge blue">Webhook API</span>
                </div>
              </td>
              <td>In 3 hours</td>
              <td>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button className="btn-secondary" style={{ padding: '0.4rem' }}><Play size={14} /></button>
                  <button className="btn-secondary" style={{ padding: '0.4rem' }}><Settings2 size={14} /></button>
                </div>
              </td>
            </tr>
            <tr>
              <td style={{ fontFamily: 'var(--font-mono)' }}>*/15 * * * *</td>
              <td>Health Check / Ping Orchestrator</td>
              <td>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <ArrowRight size={14} style={{ color: 'var(--accent)' }} /> 
                  <span className="badge green">Slack Alert</span>
                </div>
              </td>
              <td>In 4 minutes</td>
              <td>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button className="btn-secondary" style={{ padding: '0.4rem' }}><Play size={14} /></button>
                  <button className="btn-secondary" style={{ padding: '0.4rem' }}><Settings2 size={14} /></button>
                </div>
              </td>
            </tr>
            <tr>
              <td style={{ fontFamily: 'var(--font-mono)' }}>0 12 * * 1</td>
              <td>Generate Weekly Yield Report</td>
              <td>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <ArrowRight size={14} style={{ color: 'var(--accent)' }} /> 
                  <span className="badge amber">Email PDF</span>
                </div>
              </td>
              <td>Monday, 12:00 PM</td>
              <td>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button className="btn-secondary" style={{ padding: '0.4rem' }}><Play size={14} /></button>
                  <button className="btn-secondary" style={{ padding: '0.4rem' }}><Settings2 size={14} /></button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};
