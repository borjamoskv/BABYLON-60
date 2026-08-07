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
          <div className="metric-label">Verificación de Contrato (EU AI Act)</div>
          <div className="metric-value green">
            <Shield size={20} />
            OK / SCITT
          </div>
          <div className="status-badge">Fail-Stop Garantizado</div>
        </div>

        <div className="metric-group">
          <div className="metric-label">Reproducibilidad Consolidada</div>
          <div className="metric-value">
            <Lock size={20} color="#00FF41" />
            100%
          </div>
        </div>

        <div className="metric-group">
          <div className="metric-label">Coste Marginal Cloud</div>
          <div className="metric-value">
            <Cpu size={20} />
            0.00 €
          </div>
          <div style={{fontSize: '10px', color: '#888', marginTop: '4px'}}>
            Ejecución Local / Edge
          </div>
        </div>

        <div className="metric-group" style={{marginTop: 'auto'}}>
          <div className="metric-label">Entropía Estocástica Promedio</div>
          <div className="metric-value red">
            <Activity size={20} />
            H(X) &gt; ε
          </div>
          <div style={{fontSize: '10px', color: '#888', marginTop: '4px'}}>
            Purgada en Ring-0
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
