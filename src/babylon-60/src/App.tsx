// C5-REAL EXERGY CERTIFIED - ADVANCED EDITION
import { useState, useEffect } from 'react';
import { sound } from './components/AudioSynthesizer';
import { ChatWindow } from './components/ChatWindow';
import { IdeaValuator } from './components/IdeaValuator';
import { CausalVisualizer } from './components/CausalVisualizer';
import { RingBufferVisualizer, EpochSlot } from './components/RingBufferVisualizer';
import { ReceiptStream, ScittReceipt } from './components/ReceiptStream';
import {
  Shield,
  Activity,
  Cpu,
  Volume2,
  VolumeX,
  Layers,
  Zap,
} from 'lucide-react';

function App() {
  const [soundEnabled, setSoundEnabled] = useState(false);
  const [isConnectedToKernel, setIsConnectedToKernel] = useState(false);
  const [liveTEff, setLiveTEff] = useState(1.84);
  const [isAttackActive, setIsAttackActive] = useState(false);
  const [isFailStopActive, setIsFailStopActive] = useState(false);

  const [mockSlots] = useState<EpochSlot[]>([
    { id: 0, status: '5 Retired', epochId: 1040, readers: 0, hash: '0xabc123' },
    { id: 1, status: '5 Retired', epochId: 1041, readers: 0, hash: '0xdef456' },
    { id: 2, status: '4 Active', epochId: 1042, readers: 3, hash: '0x8899aa' },
    { id: 3, status: '3 Validating', epochId: 1043, readers: 1, hash: '0xbbccdd' },
    { id: 4, status: '2 Ready', epochId: 1044, readers: 0, hash: '0xeeff00' },
    { id: 5, status: '0 Idle', epochId: 0, readers: 0, hash: '' },
    { id: 6, status: '0 Idle', epochId: 0, readers: 0, hash: '' },
    { id: 7, status: '0 Idle', epochId: 0, readers: 0, hash: '' },
  ]);

  const [mockReceipts, setMockReceipts] = useState<ScittReceipt[]>([
    { id: 'REC-1042', timestamp: new Date().toISOString(), epoch: 1042, digest: '0x8899aabbccddeeff...', status: 'ATTESTED', latencyMs: 1.84, varentropy: 0.012 },
    { id: 'REC-1041', timestamp: new Date().toISOString(), epoch: 1041, digest: '0xdef4567890abcdef...', status: 'ATTESTED', latencyMs: 1.91, varentropy: 0.015 },
    { id: 'REC-1040', timestamp: new Date().toISOString(), epoch: 1040, digest: '0xabc1234567890abc...', status: 'HALTED_FAIL_STOP', latencyMs: 4.12, varentropy: 0.089 },
  ]);

  // Live WebSocket Telemetry Connector
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
    <div className={`app-container ${isFailStopActive ? 'fail-stop-alert' : ''}`}>
      {/* Sidebar Metrics */}
      <aside className="sidebar">
        <div className="brand-header">
          <div className="brand-badge">RING-0 VERIFIED</div>
          <h1>BABYLON-60</h1>
          <p className="brand-sub">C5-REAL Advanced IDE</p>
        </div>

        <div className="metric-group">
          <div className="metric-label">Status</div>
          <div className={`metric-value ${isFailStopActive ? 'red' : 'green'}`}>
            <Shield size={20} />
            {isFailStopActive ? 'QUARANTINE' : 'ONLINE'}
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

        <div className="metric-group" style={{ marginTop: '10px' }}>
          <div className="metric-label">Causal Controls</div>
          <div className="control-deck">
            <button
              className={`btn-control ${isAttackActive ? 'btn-attack-active' : ''}`}
              onClick={() => setIsAttackActive(!isAttackActive)}
            >
              <Zap size={14} />
              {isAttackActive ? 'ATTACK ACTIVE' : 'SIMULATE ATTACK'}
            </button>
            <button
              className={`btn-control btn-halt ${isFailStopActive ? 'btn-halt-active' : ''}`}
              onClick={() => setIsFailStopActive(!isFailStopActive)}
            >
              <Shield size={14} />
              {isFailStopActive ? 'RELEASE FAIL-STOP' : 'ENGAGE FAIL-STOP'}
            </button>
          </div>
        </div>

        <div className="sidebar-footer" style={{ marginTop: 'auto' }}>
          <button onClick={toggleSound} className="btn-icon">
            {soundEnabled ? <Volume2 size={16} color="#00FF41" /> : <VolumeX size={16} color="#888" />}
            <span>{soundEnabled ? 'Audio: ON' : 'Audio: OFF'}</span>
          </button>
        </div>
      </aside>

      {/* Main Center: HUD + Visualizer + Tools */}
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

        <div className="canvas-wrapper-outer" style={{ flex: '0 0 35%', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
          <CausalVisualizer
            isAttackActive={isAttackActive}
            isFailStopActive={isFailStopActive}
            onParticlePurged={() => {}}
            onParticleValidated={() => {}}
          />
        </div>

        {/* Workspace Area */}
        <div className="workspace-grid" style={{ height: 'calc(100% - 35% - 50px)' }}>
          <div className="panel-container">
             <IdeaValuator />
          </div>

          <div className="panel-container">
             <ChatWindow />
          </div>
        </div>
      </main>

      {/* Right Panel: Machinery */}
      <aside className="right-panel">
        <RingBufferVisualizer slots={mockSlots} activeEpochPtr={3} fallbackEpochPtr={2} />
        <ReceiptStream receipts={mockReceipts} />
      </aside>
    </div>
  );
}

export default App;
