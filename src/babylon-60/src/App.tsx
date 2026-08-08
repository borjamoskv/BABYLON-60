// C5-REAL EXERGY CERTIFIED - MINIMALIST EDITION
import { useState, useEffect } from 'react';
import { sound } from './components/AudioSynthesizer';
import { ChatWindow } from './components/ChatWindow';
import { IdeaValuator } from './components/IdeaValuator';
import {
  Shield,
  Activity,
  Cpu,
  Volume2,
  VolumeX,
  Layers,
} from 'lucide-react';

function App() {
  const [soundEnabled, setSoundEnabled] = useState(false);
  const [isConnectedToKernel, setIsConnectedToKernel] = useState(false);
  const [liveTEff, setLiveTEff] = useState(1.84);

  // Live WebSocket Telemetry Connector (Mocked for minimalist mode)
  useEffect(() => {
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket('ws://127.0.0.1:8765');
      ws.onopen = () => setIsConnectedToKernel(true);
      ws.onerror = () => setIsConnectedToKernel(false);
      ws.onclose = () => setIsConnectedToKernel(false);
    } catch {
      setIsConnectedToKernel(false);
    }

    // Simulate slight fluctuations in T_eff
    const interval = setInterval(() => {
      setLiveTEff(1.8 + Math.random() * 0.1);
    }, 2000);

    return () => {
      if (ws) ws.close();
      clearInterval(interval);
    };
  }, []);

  const toggleSound = () => {
    sound.enabled = !soundEnabled;
    setSoundEnabled(!soundEnabled);
  };

  return (
    <div className="app-container minimalist-mode">
      {/* Sidebar Metrics */}
      <aside className="sidebar">
        <div className="brand-header">
          <div className="brand-badge">RING-0 VERIFIED</div>
          <h1>BABYLON-60</h1>
          <p className="brand-sub">C5-REAL Minimalist IDE</p>
        </div>

        <div className="metric-group">
          <div className="metric-label">Status</div>
          <div className="metric-value green">
            <Shield size={20} />
            ONLINE
          </div>
        </div>

        <div className="metric-group">
          <div className="metric-label">Marginal Cloud Cost</div>
          <div className="metric-value">
            <Cpu size={20} />
            $0.00
          </div>
          <div className="metric-sub">Local Sovereign AI</div>
        </div>

        <div className="sidebar-footer" style={{ marginTop: 'auto' }}>
          <button onClick={toggleSound} className="btn-icon">
            {soundEnabled ? <Volume2 size={16} color="#00FF41" /> : <VolumeX size={16} color="#888" />}
            <span>{soundEnabled ? 'Audio: ON' : 'Audio: OFF'}</span>
          </button>
        </div>
      </aside>

      {/* Main Center: HUD + Minimalist Tools */}
      <main className="main-content">
        {/* Top HUD */}
        <div className="header-hud">
          <div className="hud-left">
            <span className="hud-tag">
              <Layers size={14} color="#00FF41" />
              <span>MOSKV-1 KERNEL</span>
            </span>
            <span className="hud-latency">
              <Activity size={14} />
              <span>T_eff: {liveTEff.toFixed(2)} ms</span>
            </span>
            <span className={`hud-tag ${isConnectedToKernel ? 'tag-live-silicon' : ''}`}>
              <span>{isConnectedToKernel ? '● LIVE (8765)' : '○ STANDALONE'}</span>
            </span>
          </div>
        </div>

        {/* Workspace Area */}
        <div className="workspace-grid">
          {/* Idea Valuator Panel */}
          <div className="panel-container">
             <IdeaValuator />
          </div>

          {/* Chat Window Panel */}
          <div className="panel-container">
             <ChatWindow />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
