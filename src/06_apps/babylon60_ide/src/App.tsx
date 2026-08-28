// C5-REAL EXERGY CERTIFIED - NATIVE ADHD / TDAH UNIFIED EDITION
import { useState, useEffect } from 'react';
import { sound } from './components/AudioSynthesizer';
import { ChatWindow } from './components/ChatWindow';
import { IdeaValuator } from './components/IdeaValuator';
import { CausalVisualizer } from './components/CausalVisualizer';
import { RingBufferVisualizer, EpochSlot } from './components/RingBufferVisualizer';
import { ReceiptStream, ScittReceipt } from './components/ReceiptStream';
import { CortexTraceDAG, TraceNode } from './components/CortexTraceDAG';
import {
  Shield,
  Activity,
  Cpu,
  Volume2,
  VolumeX,
  Layers,
  Zap,
  Clock,
  Sparkles,
  Focus,
} from 'lucide-react';

function App() {
  const [soundEnabled, setSoundEnabled] = useState(false);
  const [isConnectedToKernel, setIsConnectedToKernel] = useState(false);
  const [liveTEff, setLiveTEff] = useState(1.84);
  const [isAttackActive, setIsAttackActive] = useState(false);
  const [isFailStopActive, setIsFailStopActive] = useState(false);

  // TDAH / ADHD is the NON-NEGOTIABLE UNIFIED DEFAULT MODE
  const [bionicReading, setBionicReading] = useState(true);
  const [focusTimer, setFocusTimer] = useState(1500); // 25 min Pomodoro Sprint
  const [timerRunning, setTimerRunning] = useState(false);
  const [activeTab, setActiveTab] = useState<'workspace' | 'kernel' | 'traces'>('workspace');

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

  const [mockReceipts] = useState<ScittReceipt[]>([
    { id: 'REC-1042', timestamp: new Date().toISOString(), epoch: 1042, digest: '0x8899aabbccddeeff...', status: 'ATTESTED', latencyMs: 1.84, varentropy: 0.012 },
    { id: 'REC-1041', timestamp: new Date().toISOString(), epoch: 1041, digest: '0xdef4567890abcdef...', status: 'ATTESTED', latencyMs: 1.91, varentropy: 0.015 },
    { id: 'REC-1040', timestamp: new Date().toISOString(), epoch: 1040, digest: '0xabc1234567890abc...', status: 'HALTED_FAIL_STOP', latencyMs: 4.12, varentropy: 0.089 },
  ]);

  const [mockTraces] = useState<TraceNode[]>([
    {
      id: 'trace-root-1',
      run_type: 'bft_consensus',
      name: 'CORTEX_BFT_Cycle_500',
      status: 'ATTESTED',
      latency_ms: 0.84,
      varentropy: 0.004,
      scitt_digest: 'sha3:9f8e7d...',
      children: [
        {
          id: 'trace-agent-1',
          parent_id: 'trace-root-1',
          run_type: 'agent',
          name: 'ActiveInferencePolicyNode',
          status: 'ATTESTED',
          latency_ms: 0.32,
          varentropy: 0.001,
          scitt_digest: 'sha3:1a2b3c...',
          children: [
            {
              id: 'trace-tool-1',
              parent_id: 'trace-agent-1',
              run_type: 'mcp_bridge',
              name: 'FFI_RingBuffer_Commit',
              status: 'ATTESTED',
              latency_ms: 0.12,
              varentropy: 0.0,
              scitt_digest: 'sha3:4d5e6f...',
            },
            {
              id: 'trace-tool-2',
              parent_id: 'trace-agent-1',
              run_type: 'scitt_attestation',
              name: 'Emit_SCITT_Merkle_Receipt',
              status: 'ATTESTED',
              latency_ms: 0.18,
              varentropy: 0.0,
              scitt_digest: 'sha3:7890ab...',
            },
          ],
        },
      ],
    },
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

  // ADHD Focus Sprint Timer
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (timerRunning && focusTimer > 0) {
      interval = setInterval(() => {
        setFocusTimer((prev) => prev - 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [timerRunning, focusTimer]);

  const toggleSound = () => {
    sound.enabled = !soundEnabled;
    setSoundEnabled(!soundEnabled);
  };

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div
      className={`app-container adhd-hyperfocus-mode ${isFailStopActive ? 'fail-stop-alert' : ''} ${
        bionicReading ? 'bionic-typography' : ''
      }`}
    >
      {/* Sidebar Metrics (Minimalist ADHD Layout) */}
      <aside className="sidebar">
        <div className="brand-header">
          <div className="brand-badge">TDAH NATIVE UI</div>
          <h1>BABYLON-60</h1>
          <p className="brand-sub">Entorno de Foco Exergético</p>
        </div>

        {/* TDAH / ADHD Neuro-Focus Suite */}
        <div className="adhd-suite-card">
          <div className="adhd-suite-header">
            <Focus size={16} className="text-green" />
            <span>INTERFAZ TDAH UNIFICADA</span>
          </div>
          <p className="adhd-suite-desc">
            Cero ruido. Cero distracción. Diseñado para hiperfoco cognitivo continuo.
          </p>

          <div className="adhd-toggle-row">
            <button
              className={`btn-adhd-toggle ${bionicReading ? 'active' : ''}`}
              onClick={() => setBionicReading(!bionicReading)}
              title="Tipografía de anclaje de alta atención"
            >
              <Sparkles size={14} />
              <span>{bionicReading ? 'Lectura Biónica: ON' : 'Lectura Biónica: OFF'}</span>
            </button>
          </div>

          {/* Pomodoro Focus Sprint counter for time blindness */}
          <div className="focus-sprint-widget">
            <div className="sprint-timer-display">
              <Clock size={14} color="#00FF41" />
              <span className="timer-text">{formatTimer(focusTimer)}</span>
              <span className="sprint-label">Sprint Atencional</span>
            </div>
            <div className="sprint-controls">
              <button
                className="btn-sprint"
                onClick={() => setTimerRunning(!timerRunning)}
              >
                {timerRunning ? 'Pausar' : 'Iniciar'}
              </button>
              <button
                className="btn-sprint-reset"
                onClick={() => {
                  setTimerRunning(false);
                  setFocusTimer(1500);
                }}
              >
                Reset
              </button>
            </div>
          </div>
        </div>

        <div className="metric-group">
          <div className="metric-label">Status Kernel</div>
          <div className={`metric-value ${isFailStopActive ? 'red' : 'green'}`}>
            <Shield size={20} />
            {isFailStopActive ? 'QUARANTINE' : 'ONLINE'}
          </div>
        </div>

        <div className="metric-group">
          <div className="metric-label">Cómputo Local</div>
          <div className="metric-value">
            <Cpu size={20} />
            $0.00
          </div>
          <div className="metric-sub">Soberanía de Silicio</div>
        </div>

        <div className="metric-group" style={{ marginTop: '10px' }}>
          <div className="metric-label">Controles Causalidad</div>
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
        {/* Top HUD with Focus Tabs for ADHD single-tasking */}
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

          {/* Tab Selector for ADHD Cognitive Chunking */}
          <div className="adhd-task-tabs">
            <button
              className={`adhd-tab ${activeTab === 'workspace' ? 'active' : ''}`}
              onClick={() => setActiveTab('workspace')}
            >
              Lienzo Trabajo
            </button>
            <button
              className={`adhd-tab ${activeTab === 'kernel' ? 'active' : ''}`}
              onClick={() => setActiveTab('kernel')}
            >
              Grafo Causal
            </button>
            <button
              className={`adhd-tab ${activeTab === 'traces' ? 'active' : ''}`}
              onClick={() => setActiveTab('traces')}
            >
              Trazas & Registros
            </button>
          </div>
        </div>

        {/* View switching based on active Tab (Single-Tasking ADHD Paradigm) */}
        {activeTab === 'kernel' && (
          <div
            className="canvas-wrapper-outer"
            style={{ flex: '1', borderBottom: '1px solid rgba(255,255,255,0.08)' }}
          >
            <CausalVisualizer
              isAttackActive={isAttackActive}
              isFailStopActive={isFailStopActive}
              onParticlePurged={() => {}}
              onParticleValidated={() => {}}
            />
          </div>
        )}

        {/* Workspace Area: Focused Lienzo in ADHD Single Mode */}
        {activeTab === 'workspace' && (
          <div
            className="workspace-grid"
            style={{ height: 'calc(100% - 50px)' }}
          >
            <div className="panel-container focus-ring-target">
              <IdeaValuator />
            </div>

            <div className="panel-container focus-ring-target">
              <ChatWindow />
            </div>
          </div>
        )}

        {/* Dedicated Traces view when selected explicitly in ADHD Single Mode */}
        {activeTab === 'traces' && (
          <div className="adhd-full-traces-view" style={{ padding: '20px', overflowY: 'auto' }}>
            <CortexTraceDAG traces={mockTraces} />
            <RingBufferVisualizer slots={mockSlots} activeEpochPtr={3} fallbackEpochPtr={2} />
            <ReceiptStream receipts={mockReceipts} />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;


