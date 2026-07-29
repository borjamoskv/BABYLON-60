// C5-REAL EXERGY CERTIFIED
import React, { useState } from 'react';

export default function QuickstartSnippet() {
  const [activeTab, setActiveTab] = useState<'cli' | 'python'>('python');
  const [copied, setCopied] = useState(false);

  const pythonCode = `import asyncio
from babylon60.bft import BFTLedgerActor, LedgerEvent

async function main():
    # 1. Initialize BFT Ledger Actor (<5ms latency)
    actor = BFTLedgerActor("apex_ledger.db")
    await actor.start()

    # 2. Append tamper-evident event with causal taint
    future = actor.append(LedgerEvent(
        stream="autonomous_decisions",
        entity_id="agent_01",
        event_type="DECISION_SEALED",
        payload={"action": "REBALANCED_PORTFOLIO", "confidence": "C5"},
        cortex_taint="[CORTEX-TAINT:borjamoskv:bft_loop]",
        source_db="prod_db", source_table="agents", source_pk="ag_01"
    ))

    res = await future
    print("Proof Hash:", res["entry_hash"])

asyncio.run(main())`;

  const cliCode = `# 1. Install BABYLON 60 Sovereign SDK
pip install babylon60

# 2. Initialize local WAL ledger with EU AI Act compliance
babylon60 init --wal --busy-timeout=5000

# 3. Verify ledger integrity
babylon60 verify --db apex_ledger.db`;

  const currentCode = activeTab === 'python' ? pythonCode : cliCode;

  const handleCopy = () => {
    navigator.clipboard.writeText(currentCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{
      maxWidth: '800px',
      margin: '0 auto',
      background: 'rgba(10, 10, 15, 0.8)',
      border: '1px solid rgba(43, 59, 229, 0.3)',
      borderRadius: '12px',
      overflow: 'hidden',
      boxShadow: '0 20px 50px rgba(0, 0, 0, 0.5)',
      fontFamily: "'JetBrains Mono', monospace"
    }}>
      {/* Header Bar */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '0.8rem 1.2rem',
        background: 'rgba(255, 255, 255, 0.03)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.06)'
      }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => setActiveTab('python')}
            style={{
              background: activeTab === 'python' ? '#2B3BE5' : 'transparent',
              color: '#fff',
              border: 'none',
              padding: '0.4rem 0.8rem',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.8rem',
              fontWeight: 600
            }}
          >
            Python SDK
          </button>
          <button
            onClick={() => setActiveTab('cli')}
            style={{
              background: activeTab === 'cli' ? '#2B3BE5' : 'transparent',
              color: '#fff',
              border: 'none',
              padding: '0.4rem 0.8rem',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '0.8rem',
              fontWeight: 600
            }}
          >
            CLI Quickstart
          </button>
        </div>
        <button
          onClick={handleCopy}
          style={{
            background: copied ? '#00E676' : 'rgba(255, 255, 255, 0.08)',
            color: copied ? '#000' : '#fff',
            border: 'none',
            padding: '0.4rem 0.9rem',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '0.75rem',
            fontWeight: 600,
            transition: 'all 0.2s ease'
          }}
        >
          {copied ? '✓ Copied' : 'Copy Code'}
        </button>
      </div>

      {/* Code Area */}
      <pre style={{
        padding: '1.2rem',
        margin: 0,
        fontSize: '0.85rem',
        lineHeight: '1.6',
        color: '#E0E0E0',
        overflowX: 'auto'
      }}>
        <code>{currentCode}</code>
      </pre>
    </div>
  );
}
