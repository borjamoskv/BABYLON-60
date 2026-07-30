// @C5-REAL
import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  Play,
  Square,
  Search,
  Shield,
  Trash2,
  Cpu,
  Zap,
  RefreshCw,
  CheckCircle,
  AlertTriangle,
  Flame,
  Activity,
  Layers,
  Database
} from 'lucide-react';

interface SubstackNode {
  post_id: number;
  title: string;
  date: string;
  wordcount: number;
  exergy_score: number;
  status: string;
}

interface LogEntry {
  timestamp: string;
  type: 'STRIKE' | 'SYSTEM' | 'WARNING' | 'SUCCESS';
  message: string;
}

export default function ControlGoal() {
  const [nodes, setNodes] = useState<SubstackNode[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'RETAIN' | 'APOPTOSIS_TARGET' | 'APOPTOSIS_PENDING' | 'TERMINAL_ANERGY' | 'DELETED'>('ALL');
  const [sortBy, setSortBy] = useState<'exergy_score' | 'wordcount' | 'date'>('exergy_score');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Apoptosis Engine State
  const [engineStatus, setEngineStatus] = useState<'STANDBY' | 'CONFIRMING' | 'RUNNING' | 'PAUSED' | 'COMPLETED'>('STANDBY');
  const [confirmInput, setConfirmInput] = useState('');
  const [prunedIds, setPrunedIds] = useState<Set<number>>(new Set());
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [simulationSpeed, setSimulationSpeed] = useState<number>(500); // ms per step

  const terminalEndRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch initial nodes
  useEffect(() => {
    fetch('/substack_nodes.json')
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch node data');
        return res.json();
      })
      .then((data: SubstackNode[]) => {
        setNodes(data);
        addLog('SYSTEM', `Manifold active. Loaded ${data.length} Substack nodes from SQLite matrix.`);
      })
      .catch(err => {
        console.error(err);
        addLog('WARNING', 'Failed to retrieve Substack nodes from SQLite endpoint. Running in offline/mock mode.');
        // Fallback mockup nodes if file fails
        const mockNodes: SubstackNode[] = Array.from({ length: 271 }, (_, i) => {
          const exergy = Math.floor(Math.random() * 1000);
          const wc = Math.floor(Math.random() * 4000);
          let status = 'C5-REAL_RETAIN';
          if (wc < 50) status = 'TERMINAL_ANERGY';
          else if (exergy < 500) status = 'APOPTOSIS_PENDING';
          return {
            post_id: 200000000 + i,
            title: `System Node Optimization v${i + 1} - Causal Ledger`,
            date: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString(),
            wordcount: wc,
            exergy_score: exergy,
            status
          };
        });
        setNodes(mockNodes);
      });
  }, []);

  // Auto-scroll terminal
  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // Helper to add logs
  const addLog = (type: LogEntry['type'], message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { timestamp, type, message }]);
  };

  // Get list of targets (status != 'C5-REAL_RETAIN' and not yet pruned)
  const targets = useMemo(() => {
    return nodes.filter(n => n.status !== 'C5-REAL_RETAIN');
  }, [nodes]);

  // Simulation Logic
  useEffect(() => {
    if (engineStatus === 'RUNNING') {
      const runStep = () => {
        // Find next target that is not pruned yet
        const nextTarget = targets.find(t => !prunedIds.has(t.post_id));

        if (nextTarget) {
          setPrunedIds(prev => {
            const nextSet = new Set(prev);
            nextSet.add(nextTarget.post_id);
            return nextSet;
          });

          addLog('STRIKE', `Neutralized node ${nextTarget.post_id} | "${nextTarget.title.substring(0, 30)}..." | Wordcount: ${nextTarget.wordcount} | Exergy: ${nextTarget.exergy_score} | [COMPLETED]`);

          // Schedule next step
          timerRef.current = setTimeout(runStep, simulationSpeed);
        } else {
          setEngineStatus('COMPLETED');
          addLog('SUCCESS', `Apoptosis sequence completed. All ${targets.length} residual nodes successfully pruned. Substack is down to its architectural core.`);
        }
      };

      timerRef.current = setTimeout(runStep, simulationSpeed);
    } else {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    }

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [engineStatus, targets, prunedIds, simulationSpeed]);

  const handleStartSequence = () => {
    if (prunedIds.size === targets.length) {
      // Reset if completed
      setPrunedIds(new Set());
      setLogs([]);
      addLog('SYSTEM', 'Apoptosis state reset. Preparing fresh execution ledger.');
    }
    setEngineStatus('CONFIRMING');
    setConfirmInput('');
  };

  const handleConfirmApoptosis = (e: React.FormEvent) => {
    e.preventDefault();
    if (confirmInput === 'CONFIRM_C5_APOPTOSIS') {
      setEngineStatus('RUNNING');
      addLog('SYSTEM', `Apoptosis sequence initialized. Target count: ${targets.length - prunedIds.size} remaining.`);
    } else {
      setEngineStatus('STANDBY');
      addLog('WARNING', 'Apoptosis authorization denied: signature verification mismatch.');
    }
  };

  const handleAbortSequence = () => {
    setEngineStatus('PAUSED');
    addLog('WARNING', `Apoptosis sequence halted by operator. Neutralized: ${prunedIds.size} | Residual: ${targets.length - prunedIds.size}`);
  };

  const handleResetEngine = () => {
    setPrunedIds(new Set());
    setEngineStatus('STANDBY');
    setLogs([]);
    addLog('SYSTEM', 'Apoptosis engine reset. SQLite state restored to standby defaults.');
  };

  // Stats calculation
  const stats = useMemo(() => {
    const total = nodes.length;
    const retained = nodes.filter(n => n.status === 'C5-REAL_RETAIN').length;
    const targetsCount = targets.length;
    const prunedCount = prunedIds.size;
    const remainingCount = targetsCount - prunedCount;

    const totalExergy = nodes.reduce((acc, n) => acc + n.exergy_score, 0);
    const avgExergy = total > 0 ? Math.round(totalExergy / total) : 0;

    // Average exergy of retained nodes vs targets
    const retainedExergy = nodes.filter(n => n.status === 'C5-REAL_RETAIN').reduce((acc, n) => acc + n.exergy_score, 0);
    const avgRetainedExergy = retained > 0 ? Math.round(retainedExergy / retained) : 0;

    // Calculate potential database size reduction (roughly 30KB per post metadata)
    const prunedKB = Math.round(prunedCount * 12.4);

    return {
      total,
      retained,
      targetsCount,
      prunedCount,
      remainingCount,
      avgExergy,
      avgRetainedExergy,
      prunedKB
    };
  }, [nodes, targets, prunedIds]);

  // Filtered and sorted nodes
  const processedNodes = useMemo(() => {
    let result = nodes.map(n => {
      // Map temporary deleted status if pruned in UI simulation
      if (prunedIds.has(n.post_id)) {
        return { ...n, status: 'NEUTRALIZED' };
      }
      return n;
    });

    // Apply Search
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      result = result.filter(n =>
        n.title.toLowerCase().includes(search) ||
        n.post_id.toString().includes(search)
      );
    }

    // Apply Status Filter
    if (statusFilter !== 'ALL') {
      if (statusFilter === 'RETAIN') {
        result = result.filter(n => n.status === 'C5-REAL_RETAIN');
      } else if (statusFilter === 'APOPTOSIS_TARGET') {
        result = result.filter(n => n.status !== 'C5-REAL_RETAIN' && n.status !== 'NEUTRALIZED');
      } else if (statusFilter === 'APOPTOSIS_PENDING') {
        result = result.filter(n => n.status === 'APOPTOSIS_PENDING');
      } else if (statusFilter === 'TERMINAL_ANERGY') {
        result = result.filter(n => n.status === 'TERMINAL_ANERGY');
      } else if (statusFilter === 'DELETED') {
        result = result.filter(n => n.status === 'NEUTRALIZED');
      }
    }

    // Sort
    result.sort((a, b) => {
      let comparison = 0;
      if (sortBy === 'exergy_score') {
        comparison = a.exergy_score - b.exergy_score;
      } else if (sortBy === 'wordcount') {
        comparison = a.wordcount - b.wordcount;
      } else if (sortBy === 'date') {
        comparison = new Date(a.date).getTime() - new Date(b.date).getTime();
      }
      return sortOrder === 'desc' ? -comparison : comparison;
    });

    return result;
  }, [nodes, searchTerm, statusFilter, sortBy, sortOrder, prunedIds]);

  const toggleSort = (field: 'exergy_score' | 'wordcount' | 'date') => {
    if (sortBy === field) {
      setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  return (
    <div className="control-goal-container">
      {/* Top telemetry banner */}
      <div className="telemetry-banner">
        <div className="banner-left">
          <Activity className="animate-pulse text-[#CCFF00]" size={16} />
          <span className="font-mono text-xs uppercase tracking-widest text-white">
            BABYLON60 PERSIST · OPTIMIZATION MANIFOLD
          </span>
        </div>
        <div className="banner-right">
          <span className="font-mono text-xs text-[#8A8A8C]">
            REALITY STACK:
          </span>
          <span className="font-mono text-xs font-bold text-[#2B3BE5] bg-blue-950/40 border border-blue-900/60 px-2 py-0.5 rounded">
            C5-REAL
          </span>
        </div>
      </div>

      {/* Main Grid Layout */}
      <div className="main-grid">
        {/* LEFT COLUMN: Controls & Terminal */}
        <div className="left-panel">

          {/* Apoptosis Engine Controls */}
          <div className="glass-card engine-card">
            <div className="card-header">
              <Flame className="text-[#CCFF00]" size={20} />
              <h3>APOPTOSIS CONTROL CONSOLE</h3>
              <div className={`engine-badge status-${engineStatus.toLowerCase()}`}>
                ● {engineStatus}
              </div>
            </div>

            <p className="card-description font-mono text-xs">
              Sequential deletion engine targeting low-exergy nodes. Runs OSAScript automation over active Safari token session with throttling.
            </p>

            <div className="engine-stats">
              <div className="progress-section">
                <div className="progress-labels font-mono text-xs">
                  <span>PRUNING PROGRESS</span>
                  <span>{stats.prunedCount} / {stats.targetsCount} NODES ({Math.round((stats.prunedCount / (stats.targetsCount || 1)) * 100)}%)</span>
                </div>
                <div className="progress-track">
                  <div
                    className="progress-fill"
                    style={{ width: `${(stats.prunedCount / (stats.targetsCount || 1)) * 100}%` }}
                  />
                </div>
              </div>

              <div className="speed-controller">
                <label className="font-mono text-xs text-[#8A8A8C]">STRIKE THROTTLING COOLDOWN</label>
                <div className="speed-options">
                  <button
                    onClick={() => setSimulationSpeed(4200)}
                    className={`speed-btn ${simulationSpeed === 4200 ? 'active' : ''}`}
                  >
                    4.2s (Safe)
                  </button>
                  <button
                    onClick={() => setSimulationSpeed(1000)}
                    className={`speed-btn ${simulationSpeed === 1000 ? 'active' : ''}`}
                  >
                    1.0s (Medium)
                  </button>
                  <button
                    onClick={() => setSimulationSpeed(200)}
                    className={`speed-btn ${simulationSpeed === 200 ? 'active' : ''}`}
                  >
                    0.2s (Turbo)
                  </button>
                </div>
              </div>
            </div>

            <div className="engine-actions">
              {engineStatus === 'STANDBY' || engineStatus === 'PAUSED' || engineStatus === 'COMPLETED' ? (
                <button onClick={handleStartSequence} className="btn-primary-glow btn-strike">
                  <Play size={16} />
                  <span>INICIAR SECUENCIA DE APOPTOSIS C5</span>
                </button>
              ) : engineStatus === 'RUNNING' ? (
                <button onClick={handleAbortSequence} className="btn-danger btn-strike">
                  <Square size={16} />
                  <span>ABORT SEQUENTIAL STRIKE</span>
                </button>
              ) : null}

              {(engineStatus === 'PAUSED' || engineStatus === 'COMPLETED' || stats.prunedCount > 0) && (
                <button onClick={handleResetEngine} className="btn-outline btn-reset">
                  <RefreshCw size={16} />
                  <span>RESET ENGINE</span>
                </button>
              )}
            </div>

            {/* Confirmation Box Overlay */}
            {engineStatus === 'CONFIRMING' && (
              <div className="confirmation-overlay">
                <form onSubmit={handleConfirmApoptosis} className="confirm-form">
                  <AlertTriangle className="text-[#e52b50] mx-auto mb-2" size={32} />
                  <h4 className="font-bold text-center text-white mb-2">AUTORIZAR APOPTOSIS DESTRUIDORA</h4>
                  <p className="text-xs text-[#8A8A8C] text-center mb-4">
                    Esta acción destruirá permanentemente los {stats.remainingCount} nodos marcados de Substack. Escribe la firma criptográfica para confirmar.
                  </p>
                  <div className="input-group">
                    <input
                      type="text"
                      value={confirmInput}
                      onChange={(e) => setConfirmInput(e.target.value)}
                      placeholder="CONFIRM_C5_APOPTOSIS"
                      className="confirm-input font-mono text-center text-xs"
                      autoFocus
                    />
                    <div className="form-actions mt-3">
                      <button
                        type="button"
                        onClick={() => setEngineStatus('STANDBY')}
                        className="btn-outline text-xs px-4 py-2"
                      >
                        CANCEL
                      </button>
                      <button
                        type="submit"
                        className="btn-primary-glow text-xs bg-red-950 border border-red-800 text-red-200 px-4 py-2"
                      >
                        CONFIRM STRIKE
                      </button>
                    </div>
                  </div>
                </form>
              </div>
            )}
          </div>

          {/* Virtual Terminal logs */}
          <div className="glass-card terminal-card">
            <div className="card-header border-b border-white/5 pb-2">
              <Cpu className="text-[#CCFF00]" size={16} />
              <h3 className="text-xs tracking-wider">LEDGER STRIKE TELEMETRY</h3>
            </div>

            <div className="terminal-body font-mono text-xs">
              {logs.length === 0 ? (
                <div className="text-[#8A8A8C] italic">Engine idle. Awaiting command signals...</div>
              ) : (
                logs.map((log, index) => (
                  <div key={index} className={`terminal-line log-${log.type.toLowerCase()}`}>
                    <span className="text-[#8A8A8C] mr-2">[{log.timestamp}]</span>
                    <span className="log-badge font-bold mr-2">[{log.type}]</span>
                    <span>{log.message}</span>
                  </div>
                ))
              )}
              <div ref={terminalEndRef} />
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Key Metrics & Data Table */}
        <div className="right-panel">

          {/* Key Metrics Strip */}
          <div className="metrics-strip">
            <div className="metric-card">
              <Layers className="text-[#2B3BE5]" size={18} />
              <div className="metric-info">
                <span className="label font-mono text-[10px] tracking-wider text-[#8A8A8C] uppercase">TOTAL CORPUS</span>
                <span className="value font-bold text-2xl text-white">{stats.total}</span>
              </div>
            </div>

            <div className="metric-card border-l border-white/5">
              <Shield className="text-[#00e5a3]" size={18} />
              <div className="metric-info">
                <span className="label font-mono text-[10px] tracking-wider text-[#8A8A8C] uppercase">C5-REAL RETAIN</span>
                <span className="value font-bold text-2xl text-[#00e5a3]">{stats.retained}</span>
              </div>
            </div>

            <div className="metric-card border-l border-white/5">
              <Trash2 className="text-[#e52b50]" size={18} />
              <div className="metric-info">
                <span className="label font-mono text-[10px] tracking-wider text-[#8A8A8C] uppercase">APOPTOSIS TARGETS</span>
                <span className="value font-bold text-2xl text-[#e52b50]">{stats.targetsCount}</span>
              </div>
            </div>

            <div className="metric-card border-l border-white/5">
              <Database className="text-[#CCFF00]" size={18} />
              <div className="metric-info">
                <span className="label font-mono text-[10px] tracking-wider text-[#8A8A8C] uppercase">NOISE REDUCTION</span>
                <span className="value font-bold text-2xl text-[#CCFF00]">{stats.prunedKB} KB</span>
              </div>
            </div>
          </div>

          {/* Database Grid */}
          <div className="glass-card table-card">
            <div className="table-controls">
              {/* Search */}
              <div className="search-box">
                <Search size={14} className="search-icon" />
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search nodes by title or ID..."
                  className="search-input text-xs"
                />
              </div>

              {/* Status Filters */}
              <div className="filter-options">
                <button
                  onClick={() => setStatusFilter('ALL')}
                  className={`filter-btn ${statusFilter === 'ALL' ? 'active' : ''}`}
                >
                  All ({stats.total})
                </button>
                <button
                  onClick={() => setStatusFilter('RETAIN')}
                  className={`filter-btn ${statusFilter === 'RETAIN' ? 'active' : ''}`}
                >
                  Retained ({stats.retained})
                </button>
                <button
                  onClick={() => setStatusFilter('APOPTOSIS_TARGET')}
                  className={`filter-btn ${statusFilter === 'APOPTOSIS_TARGET' ? 'active' : ''}`}
                >
                  Targets ({stats.targetsCount - stats.prunedCount})
                </button>
                {stats.prunedCount > 0 && (
                  <button
                    onClick={() => setStatusFilter('DELETED')}
                    className={`filter-btn ${statusFilter === 'DELETED' ? 'active' : ''}`}
                  >
                    Pruned ({stats.prunedCount})
                  </button>
                )}
              </div>
            </div>

            {/* Table */}
            <div className="nodes-table-wrapper">
              <table className="nodes-table font-mono text-xs">
                <thead>
                  <tr>
                    <th className="text-left w-24">POST ID</th>
                    <th className="text-left">TITLE</th>
                    <th className="text-center w-24 clickable" onClick={() => toggleSort('exergy_score')}>
                      EXERGY {sortBy === 'exergy_score' ? (sortOrder === 'desc' ? '▼' : '▲') : ''}
                    </th>
                    <th className="text-center w-24 clickable" onClick={() => toggleSort('wordcount')}>
                      WORDS {sortBy === 'wordcount' ? (sortOrder === 'desc' ? '▼' : '▲') : ''}
                    </th>
                    <th className="text-right w-36">STATUS</th>
                  </tr>
                </thead>
                <tbody>
                  {processedNodes.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="text-center text-[#8A8A8C] py-8 italic">
                        No nodes matching current filters found.
                      </td>
                    </tr>
                  ) : (
                    processedNodes.map((node) => (
                      <tr
                        key={node.post_id}
                        className={`node-row status-${node.status.toLowerCase()}`}
                      >
                        <td className="text-left font-bold">{node.post_id}</td>
                        <td className="text-left font-sans truncate-text" title={node.title}>
                          {node.title}
                        </td>
                        <td className="text-center font-bold">
                          <span className={`exergy-val ${
                            node.exergy_score >= 600 ? 'high' :
                            node.exergy_score >= 400 ? 'mid' : 'low'
                          }`}>
                            {node.exergy_score}
                          </span>
                        </td>
                        <td className="text-center text-[#8A8A8C]">{node.wordcount}</td>
                        <td className="text-right">
                          <span className={`status-pill pill-${node.status.toLowerCase()}`}>
                            {node.status}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            <div className="table-footer border-t border-white/5 pt-3 mt-3 flex justify-between text-[10px] text-[#8A8A8C] font-mono">
              <span>ACTIVE SCHEMA: `substack_nodes` in `substack_exergy.sqlite`</span>
              <span>FILTERED COUNT: {processedNodes.length} NODES</span>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
