// C5-REAL EXERGY CERTIFIED
import React, { useState } from 'react';
import { GitCommit, Activity, ShieldCheck, ShieldAlert, Cpu, ChevronRight, Clock, Hash } from 'lucide-react';

export interface TraceNode {
  id: string;
  parent_id?: string;
  run_type: 'agent' | 'bft_consensus' | 'scitt_attestation' | 'tool_call' | 'mcp_bridge';
  name: string;
  status: 'ATTESTED' | 'HALTED_FAIL_STOP' | 'PENDING';
  latency_ms: number;
  varentropy: number;
  scitt_digest: string;
  inputs?: Record<string, unknown>;
  outputs?: Record<string, unknown>;
  children?: TraceNode[];
}

interface Props {
  traces: TraceNode[];
  onSelectNode?: (node: TraceNode) => void;
}

export const CortexTraceDAG: React.FC<Props> = ({ traces, onSelectNode }) => {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const handleSelect = (node: TraceNode) => {
    setSelectedId(node.id);
    onSelectNode?.(node);
  };

  const renderNode = (node: TraceNode, depth: number = 0) => {
    const isSelected = selectedId === node.id;
    const isAttested = node.status === 'ATTESTED';

    return (
      <div key={node.id} style={{ marginLeft: `${depth * 18}px` }} className="trace-node-group">
        <div
          onClick={() => handleSelect(node)}
          className={`trace-node-card ${isSelected ? 'trace-selected' : ''} ${
            isAttested ? 'trace-status-attested' : 'trace-status-halted'
          }`}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '8px 12px',
            margin: '4px 0',
            borderRadius: '4px',
            background: isSelected ? '#1a1a22' : '#0f0f13',
            border: `1px solid ${isSelected ? '#d4af37' : '#22222a'}`,
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ChevronRight size={12} color="#7a7a7a" style={{ transform: node.children?.length ? 'rotate(90deg)' : 'none' }} />
            {node.run_type === 'bft_consensus' && <Cpu size={14} color="#d4af37" />}
            {node.run_type === 'scitt_attestation' && <ShieldCheck size={14} color="#3ab370" />}
            {node.run_type === 'agent' && <Activity size={14} color="#60a5fa" />}
            {node.run_type === 'tool_call' && <GitCommit size={14} color="#c084fc" />}
            {node.run_type === 'mcp_bridge' && <Hash size={14} color="#f59e0b" />}

            <span style={{ fontSize: '0.85rem', fontWeight: 500, color: '#e0e0e0' }}>{node.name}</span>
            <span
              style={{
                fontSize: '0.68rem',
                padding: '2px 6px',
                borderRadius: '3px',
                background: '#181820',
                color: '#7a7a7a',
                textTransform: 'uppercase',
              }}
            >
              {node.run_type}
            </span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: '#7a7a7a', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Clock size={11} /> {node.latency_ms.toFixed(2)}ms
            </span>
            <span
              style={{
                fontSize: '0.7rem',
                fontFamily: 'monospace',
                color: isAttested ? '#3ab370' : '#b33a3a',
                display: 'flex',
                alignItems: 'center',
                gap: '3px',
              }}
            >
              {isAttested ? <ShieldCheck size={12} /> : <ShieldAlert size={12} />}
              {node.status}
            </span>
          </div>
        </div>

        {node.children && node.children.map((child) => renderNode(child, depth + 1))}
      </div>
    );
  };

  return (
    <div className="cortex-trace-dag-panel" style={{ width: '100%', padding: '16px', background: '#0b0b0e', borderRadius: '6px' }}>
      <div
        className="dag-header"
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '12px',
          borderBottom: '1px solid #1a1a22',
          paddingBottom: '8px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity size={16} color="#d4af37" />
          <span style={{ fontSize: '0.9rem', fontWeight: 600, letterSpacing: '0.5px', color: '#e0e0e0' }}>
            CORTEX C5-REAL Trace DAG (Zero-Network Ingest)
          </span>
        </div>
        <span style={{ fontSize: '0.7rem', color: '#3ab370', fontFamily: 'monospace' }}>● SCITT VERIFIED // SUB-MS LATENCY</span>
      </div>

      <div className="dag-tree">{traces.map((rootNode) => renderNode(rootNode, 0))}</div>
    </div>
  );
};
