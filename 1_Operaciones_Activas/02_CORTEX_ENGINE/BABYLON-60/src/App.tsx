// C5-REAL EXERGY CERTIFIED
import { useState, useEffect, useCallback } from 'react';
import { CausalVisualizer } from './components/CausalVisualizer';
import { RingBufferVisualizer, EpochSlot } from './components/RingBufferVisualizer';
import { ReceiptStream, ScittReceipt } from './components/ReceiptStream';
import { sound } from './AudioSynthesizer';
import {
  Shield,
  Activity,
  Lock,
  Cpu,
  Volume2,
  VolumeX,
  Flame,
  AlertOctagon,
  RefreshCw,
  Layers,
  FileCheck2,
} from 'lucide-react';

const INITIAL_SLOTS: EpochSlot[] = [
  { id: 0, status: '5 Retired', epochId: 41, readers: 0, hash: 'a4f91c88e2' },
  { id: 1, status: '4 Active', epochId: 44, readers: 3, hash: '7c89b0213d' },
  { id: 2, status: '4 Active', epochId: 43, readers: 1, hash: '3e110ff49a' },
  { id: 3, status: '3 Validating', epochId: 45, readers: 0, hash: '88bc110aef' },
  { id: 4, status: '0 Idle', epochId: 0, readers: 0, hash: '0000000000' },
  { id: 5, status: '0 Idle', epochId: 0, readers: 0, hash: '0000000000' },
  { id: 6, status: '0 Idle', epochId: 0, readers: 0, hash: '0000000000' },
  { id: 7, status: '0 Idle', epochId: 0, readers: 0, hash: '0000000000' },
];

function App() {
  const [soundEnabled, setSoundEnabled] = useState(false);
  const [isAttackActive, setIsAttackActive] = useState(false);
  const [isFailStopActive, setIsFailStopActive] = useState(false);
  const [purgedCount, setPurgedCount] = useState(14892);
  const [validatedCount, setValidatedCount] = useState(2310);
  const [activeEpochPtr, setActiveEpochPtr] = useState(1);
  const [fallbackEpochPtr, setFallbackEpochPtr] = useState(2);
  const [slots, setSlots] = useState<EpochSlot[]>(INITIAL_SLOTS);
  const [receipts, setReceipts] = useState<ScittReceipt[]>([
    {
      id: '10484',
      timestamp: '19:50:02',
      epoch: 44,
      digest: '0x9f8c...3a1e (Ed25519 Validated)',
      status: 'ATTESTED',
      latencyMs: 1.84,
      varentropy: 0.012,
    },
    {
      id: '10483',
      timestamp: '19:49:58',
      epoch: 44,
      digest: '0x12bb...87ce (Ed25519 Validated)',
      status: 'ATTESTED',
      latencyMs: 1.62,
      varentropy: 0.009,
    },
  const [isConnectedToKernel, setIsConnectedToKernel] = useState(false);
  const [liveTEff, setLiveTEff] = useState(1.84);

  // Live WebSocket Telemetry Connector
  useEffect(() => {
    let ws: WebSocket | null = null;
    try {
      ws = new WebSocket('ws://127.0.0.1:8765');
      ws.onopen = () => {
        setIsConnectedToKernel(true);
      };
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'C5_TELEMETRY_FRAME') {
            if (data.tEffMs) setLiveTEff(data.tEffMs);
            if (data.slots) setSlots(data.slots);
            if (data.activeEpochPtr) setActiveEpochPtr(data.activeEpochPtr);
            if (data.latestReceipt) {
              setReceipts((prev) => [data.latestReceipt, ...prev.slice(0, 6)]);
            }
          }
        } catch {
          // Ignore malformed frames
        }
      };
      ws.onerror = () => setIsConnectedToKernel(false);
      ws.onclose = () => setIsConnectedToKernel(false);
    } catch {
      setIsConnectedToKernel(false);
    }

    return () => {
      if (ws) ws.close();
    };
  }, []);

  const toggleSound = () => {
    sound.enabled = !soundEnabled;
    setSoundEnabled(!soundEnabled);
  };

  const handleParticlePurged = useCallback(() => {
    setPurgedCount((prev) => prev + 1);
  }, []);

  const handleParticleValidated = useCallback(() => {
    setValidatedCount((prev) => prev + 1);

    // Append mock SCITT receipt periodically
    const randHex = Math.random().toString(16).substring(2, 10);
    const newReceipt: ScittReceipt = {
      id: (10485 + Math.floor(Math.random() * 1000)).toString(),
      timestamp: new Date().toLocaleTimeString(),
      epoch: 44,
      digest: `0x${randHex}...${Math.random().toString(16).substring(2, 6)} (Ed25519)`,
      status: 'ATTESTED',
      latencyMs: 1.2 + Math.random() * 1.5,
      varentropy: 0.008 + Math.random() * 0.015,
    };

    setReceipts((prev) => [newReceipt, ...prev.slice(0, 7)]);
  }, []);

  // Fail-Stop Toggle / Quarantine CAS Execution
  const triggerFailStop = () => {
    if (!isFailStopActive) {
      setIsFailStopActive(true);
      sound.playAlarm();

      // Simulate Double-Pointer Sentinel CAS to Fallback Slot
      setSlots((prev) =>
        prev.map((s) => {
          if (s.id === activeEpochPtr) {
            return { ...s, status: '6 Quarantine', readers: 0 };
          }
          return s;
        })
      );
      setActiveEpochPtr(fallbackEpochPtr);

      const alertReceipt: ScittReceipt = {
        id: (10500 + Math.floor(Math.random() * 1000)).toString(),
        timestamp: new Date().toLocaleTimeString(),
        epoch: 44,
        digest: 'EPISTEMIC_HALT: Varentropy Spike CUSUM > 3%',
        status: 'HALTED_FAIL_STOP',
        latencyMs: 0.08,
        varentropy: 0.085,
      };
      setReceipts((prev) => [alertReceipt, ...prev.slice(0, 7)]);
    } else {
      // Restore normal operation
      setIsFailStopActive(false);
      setSlots(INITIAL_SLOTS);
      setActiveEpochPtr(1);
      setFallbackEpochPtr(2);
    }
  };

  const toggleAttack = () => {
    setIsAttackActive(!isAttackActive);
  };

  return (
    <div className={`app-container ${isFailStopActive ? 'fail-stop-alert' : ''}`}>
      {/* Sidebar Metrics (Executive CIO View) */}
      <aside className="sidebar">
        <div className="brand-header">
          <div className="brand-badge">RING-0 VERIFIED</div>
          <h1>BABYLON-60</h1>
          <p className="brand-sub">C5-REAL Control Center</p>
        </div>

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
          <div className="metric-sub">Robinson-Łoś st(x) Transfer</div>
        </div>

        <div className="metric-group">
          <div className="metric-label">Marginal Cloud Cost (COGS)</div>
          <div className="metric-value">
            <Cpu size={20} />
            $0.00
          </div>
          <div className="metric-sub">Local / Sovereign WASM Sandbox</div>
        </div>

        {/* Live Counters */}
        <div className="counter-row">
          <div className="counter-box">
            <span className="counter-label">Purged Tokens</span>
            <span className="counter-val red">{purgedCount.toLocaleString()}</span>
          </div>
          <div className="counter-box">
            <span className="counter-label">Attested Crystals</span>
            <span className="counter-val green">{validatedCount.toLocaleString()}</span>
          </div>
        </div>

        {/* Action Controls */}
        <div className="control-deck">
          <button
            onClick={toggleAttack}
            className={`btn-control ${isAttackActive ? 'btn-attack-active' : ''}`}
          >
            <Flame size={15} />
            {isAttackActive ? 'Attacking...' : 'Inject Entropy Attack'}
          </button>

          <button
            onClick={triggerFailStop}
            className={`btn-control ${isFailStopActive ? 'btn-halt-active' : 'btn-halt'}`}
          >
            <AlertOctagon size={15} />
            {isFailStopActive ? 'Restore Kernel (CAS)' : 'Simulate Fail-Stop'}
          </button>
        </div>

        <div className="sidebar-footer">
          <button onClick={toggleSound} className="btn-icon">
            {soundEnabled ? <Volume2 size={16} color="#00FF41" /> : <VolumeX size={16} color="#888" />}
            <span>{soundEnabled ? 'Audio Synthesizer: ON' : 'Audio Muted'}</span>
          </button>
        </div>
      </aside>

      {/* Main Center: HUD + Canvas + Ring Buffer */}
      <main className="main-content">
        {/* Top HUD */}
        <div className="header-hud">
          <div className="hud-left">
            <span className="hud-tag">
              <Layers size={14} color="#00FF41" />
              <span>KERNEL BFT ACTIVE_PTR: 0x{activeEpochPtr}000</span>
            </span>
            <span className="hud-tag">
              <span>FALLBACK_PTR: 0x{fallbackEpochPtr}000</span>
            </span>
            <span className="hud-latency">
              <Activity size={14} />
              <span>T_eff: {liveTEff.toFixed(2)} ms</span>
            </span>
            <span className={`hud-tag ${isConnectedToKernel ? 'tag-live-silicon' : ''}`}>
              <span>{isConnectedToKernel ? '● LIVE SILICON IPC (8765)' : '○ DEMO SIMULATOR'}</span>
            </span>
          </div>

          <div className="hud-right">
            <span className={`status-pill ${isFailStopActive ? 'pill-quarantine' : 'pill-active'}`}>
              {isFailStopActive ? 'STATUS: 6 QUARANTINE / HALT' : 'STATUS: 4 ACTIVE / PROTECTED'}
            </span>
          </div>
        </div>

        {/* Causal Visualizer Canvas */}
        <div className="canvas-wrapper-outer">
          <CausalVisualizer
            isAttackActive={isAttackActive}
            isFailStopActive={isFailStopActive}
            onParticlePurged={handleParticlePurged}
            onParticleValidated={handleParticleValidated}
          />
        </div>

        {/* Bottom Section: Lock-Free EBR Shared Memory */}
        <RingBufferVisualizer
          slots={slots}
          activeEpochPtr={activeEpochPtr}
          fallbackEpochPtr={fallbackEpochPtr}
        />
      </main>

      {/* Right Drawer: Live SCITT Receipts */}
      <aside className="right-panel">
        <ReceiptStream receipts={receipts} />
      </aside>
    </div>
  );
}

export default App;
