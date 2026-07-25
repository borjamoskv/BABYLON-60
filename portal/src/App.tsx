import React, { useState } from 'react';
import {
  Terminal,
  Activity,
  Cpu,
  Network,
  BookOpen,
  Zap,
  ShieldCheck,
  Code
} from 'lucide-react';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="brand">
          <Terminal size={32} className="brand-icon" />
          <span className="brand-text">MOSKV-1</span>
        </div>

        <nav className="nav-menu">
          <div
            className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <Activity size={20} />
            Dashboard FISR
          </div>
          <div
            className={`nav-item ${activeTab === 'primitives' ? 'active' : ''}`}
            onClick={() => setActiveTab('primitives')}
          >
            <Code size={20} />
            Explorador 896
          </div>
          <div
            className={`nav-item ${activeTab === 'isomorphism' ? 'active' : ''}`}
            onClick={() => setActiveTab('isomorphism')}
          >
            <Cpu size={20} />
            Isomorfismo Bio-Silicon
          </div>
          <div
            className={`nav-item ${activeTab === 'resolution' ? 'active' : ''}`}
            onClick={() => setActiveTab('resolution')}
          >
            <Network size={20} />
            Robinson Resolution
          </div>
          <div
            className={`nav-item ${activeTab === 'glossary' ? 'active' : ''}`}
            onClick={() => setActiveTab('glossary')}
          >
            <BookOpen size={20} />
            Glosario Soberano
          </div>
        </nav>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">

        {activeTab === 'dashboard' && (
          <div className="animate-fade-in">
            <header className="hero">
              <div className="hero-badge">
                <ShieldCheck size={16} />
                C5-REAL EXERGY CERTIFIED
              </div>
              <h1 className="hero-title">Teorema Robinson-Moskv</h1>
              <p className="hero-description">
                Portal interactivo de visualización del complejo simplicial Compat(Ω),
                métrica de Lawvere y transducción de fricción cognitiva en exergía física.
              </p>
            </header>

            <div className="dashboard-grid">
              <div className="card glass-panel">
                <div className="card-header">
                  <Activity size={24} />
                  <h3 className="card-title">Entropía de Shannon (S)</h3>
                </div>
                <p className="metric-label">Incertidumbre Causal</p>
                <div className="metric-value" style={{ color: 'var(--status-error)' }}>
                  H(X) = 2.4 bits
                </div>
              </div>

              <div className="card glass-panel">
                <div className="card-header">
                  <Zap size={24} />
                  <h3 className="card-title">Eficiencia Epistémica (ηD)</h3>
                </div>
                <p className="metric-label">Fricción Vencida / Trabajo</p>
                <div className="metric-value" style={{ color: 'var(--status-exergy)' }}>
                  ηD = 0.982
                </div>
              </div>

              <div className="card glass-panel">
                <div className="card-header">
                  <Network size={24} />
                  <h3 className="card-title">Primitivas Categóricas</h3>
                </div>
                <p className="metric-label">Espacio Base</p>
                <div className="metric-value" style={{ color: 'var(--text-primary)' }}>
                  896 Nodos
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'primitives' && (
          <div className="animate-fade-in">
            <h2 className="hero-title" style={{ fontSize: '3rem', marginBottom: '2rem' }}>
              Explorador 896
            </h2>
            <div className="glass-panel" style={{ padding: '2rem' }}>
              <p style={{ color: 'var(--text-secondary)' }}>
                [ Módulo en construcción. Conexión IPC con categorical_896_engine.py requerida para renderizado AST... ]
              </p>
            </div>
          </div>
        )}

        {/* Other tabs remain placeholders for now */}
        {(activeTab !== 'dashboard' && activeTab !== 'primitives') && (
          <div className="animate-fade-in">
            <h2 className="hero-title" style={{ fontSize: '3rem', marginBottom: '2rem' }}>
              {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
            </h2>
            <div className="glass-panel" style={{ padding: '2rem' }}>
              <p style={{ color: 'var(--text-secondary)' }}>
                Iniciando colapso de onda. Fricción latente en proceso de transducción.
              </p>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}

export default App;
