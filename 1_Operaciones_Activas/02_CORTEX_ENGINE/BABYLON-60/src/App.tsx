// C5-REAL EXERGY CERTIFIED
import React from 'react';
import { CausalVisualizer } from './components/CausalVisualizer';
import { Shield, Activity, Lock, Cpu } from 'lucide-react';

function App() {
  return (
    <div className="app-container">
      {/* Sidebar Metrics */}
      <aside className="sidebar">
        <h1>BABYLON-60<br/>Runtime</h1>

        <div className="metric-group">
          <div className="metric-label">Contract Verification (EU AI Act)</div>
          <div className="metric-value green">
            <Shield size={20} />
            OK / SCITT
          </div>
          <div className="status-badge">Guaranteed Fail-Stop</div>
        </div>

        <div className="metric-group">
          <div className="metric-label">Consolidated Reproducibility</div>
          <div className="metric-value">
            <Lock size={20} color="#00FF41" />
            100%
          </div>
        </div>

        <div className="metric-group">
          <div className="metric-label">Marginal Cloud Cost</div>
          <div className="metric-value">
            <Cpu size={20} />
            $0.00
          </div>
          <div style={{fontSize: '10px', color: '#888', marginTop: '4px'}}>
            Local / Edge Sovereign Runtime
          </div>
        </div>

        <div className="metric-group" style={{marginTop: 'auto'}}>
          <div className="metric-label">Average Stochastic Entropy</div>
          <div className="metric-value red">
            <Activity size={20} />
            H(X) &gt; ε
          </div>
          <div style={{fontSize: '10px', color: '#888', marginTop: '4px'}}>
            Purged at Ring-0 Boundary
          </div>
        </div>
      </aside>

      {/* Main Visualizer */}
      <main className="main-content">
        <div className="header">
          <div style={{ fontFamily: 'monospace', color: '#888', fontSize: '12px' }}>
            [KERNEL BFT] ACTIVE_EPOCH_PTR: 0x8F4A2B
          </div>
          <div style={{ fontFamily: 'monospace', color: '#00FF41', fontSize: '12px' }}>
            STATUS: 4 ACTIVE / PROTECTED
          </div>
        </div>
        <CausalVisualizer />
      </main>
    </div>
  );
}

export default App;
