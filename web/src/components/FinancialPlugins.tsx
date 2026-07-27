import React from 'react';
import { Blocks, LineChart, TrendingUp, DollarSign } from 'lucide-react';
import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const mockData = [
  { time: '09:00', price: 42100 },
  { time: '10:00', price: 42400 },
  { time: '11:00', price: 42250 },
  { time: '12:00', price: 42800 },
  { time: '13:00', price: 43100 },
  { time: '14:00', price: 42900 },
  { time: '15:00', price: 43500 },
];

export const FinancialPlugins: React.FC = () => {
  return (
    <div className="animate-fade-in">
      <div className="view-header">
        <div>
          <h1 className="view-title">Economic Intelligence</h1>
          <p className="view-subtitle">Professional financial data plugins and market telemetry.</p>
        </div>
        <button className="btn-primary"><Blocks size={16} /> Add Plugin</button>
      </div>

      <div className="grid-3" style={{ marginBottom: '2rem' }}>
        <div className="glass-panel" style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <div style={{ padding: '1rem', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '12px', color: '#10b981' }}>
            <TrendingUp size={32} />
          </div>
          <div>
            <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Bloomberg Feed</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              Connected <span className="status-dot"></span>
            </div>
          </div>
        </div>
        <div className="glass-panel" style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <div style={{ padding: '1rem', background: 'rgba(59, 130, 246, 0.1)', borderRadius: '12px', color: '#3b82f6' }}>
            <LineChart size={32} />
          </div>
          <div>
            <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Refinitiv API</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              Syncing <span className="status-dot warning"></span>
            </div>
          </div>
        </div>
        <div className="glass-panel" style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '12px', color: '#ef4444' }}>
            <DollarSign size={32} />
          </div>
          <div>
            <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Custom Defi Node</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              Offline <span className="status-dot danger"></span>
            </div>
          </div>
        </div>
      </div>

      <div className="glass-panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h3 style={{ fontSize: '1.25rem' }}>BTC/USD Market Structure</h3>
          <span className="badge blue">Live Data via Bloomberg Plugin</span>
        </div>
        <div style={{ height: '300px', width: '100%' }}>
          <ResponsiveContainer width="100%" height="100%">
            <RechartsLineChart data={mockData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
              <XAxis dataKey="time" stroke="rgba(255,255,255,0.5)" tick={{fill: 'rgba(255,255,255,0.5)'}} />
              <YAxis domain={['auto', 'auto']} stroke="rgba(255,255,255,0.5)" tick={{fill: 'rgba(255,255,255,0.5)'}} tickFormatter={(value) => `$${value}`} />
              <Tooltip 
                contentStyle={{ background: 'rgba(20,20,22,0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                itemStyle={{ color: '#818cf8', fontWeight: 600 }}
              />
              <Line type="monotone" dataKey="price" stroke="#818cf8" strokeWidth={3} dot={{ fill: '#818cf8', r: 4 }} activeDot={{ r: 8 }} />
            </RechartsLineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
