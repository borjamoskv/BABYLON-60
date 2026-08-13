import React, { useState } from 'react';

export const HeroCodeSnippet: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'python' | 'rust' | 'cli'>('python');
  const [copied, setCopied] = useState(false);

  const snippets = {
    python: `# 1. Instalación: pip install babylon60
from babylon60 import CausalLedger, EUAIActGuard

# Instanciar Ledger Causal Local (SQLite WAL + SHA3-256)
ledger = CausalLedger("audit.db")

# Registrar evento de agente con prueba Z3
receipt = ledger.commit(
    agent_id="agent-i-kernel",
    action="EXECUTE_TOOL",
    payload={"tool": "code_interpreter", "status": "PASS"}
)

print(f"Hash Causal Verificado: {receipt.hash}")`,
    rust: `// 1. Cargo.toml: babylon60-core = "4.0"
use babylon60_core::kernel::{SeqlockEngine, CausalLedger};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let ledger = CausalLedger::open("audit.db")?;
    let block = ledger.commit_block(b"AGENT_ACTION_PAYLOAD")?;
    println!("Bloque SHA3-256: {:x}", block.hash);
    Ok(())
}`,
    cli: `# Integración instantánea desde CLI / CI Pipeline
$ pip install babylon60

# Exportar evidencia de autoevaluación del EU AI Act (Artículos 9–14)
$ babylon60-compliance --bundle ./artifacts --format html --output report.html

# Verificar validez de clave de licencia offline
$ babylon60-license verify --key "AcmeCorp:enterprise:1818172862:10b551ec00ca40c5"`
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(snippets[activeTab]);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="glass-panel p-6 space-y-4 font-mono">
      <div className="flex flex-wrap justify-between items-center border-b border-slate-800 pb-3 gap-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-300">INTEGRACIÓN RÁPIDA (SDK 5 LÍNEAS)</span>
          <div className="flex gap-1 bg-slate-900/80 p-1 rounded border border-slate-800 text-xs">
            <button
              onClick={() => setActiveTab('python')}
              className={`px-3 py-1 rounded transition-all ${
                activeTab === 'python' ? 'bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/40' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              🐍 Python
            </button>
            <button
              onClick={() => setActiveTab('rust')}
              className={`px-3 py-1 rounded transition-all ${
                activeTab === 'rust' ? 'bg-amber-500/20 text-amber-300 font-bold border border-amber-500/40' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              🦀 Rust
            </button>
            <button
              onClick={() => setActiveTab('cli')}
              className={`px-3 py-1 rounded transition-all ${
                activeTab === 'cli' ? 'bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/40' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              💻 CLI / CI
            </button>
          </div>
        </div>
        <button
          onClick={handleCopy}
          className="px-3 py-1 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded text-slate-300 text-xs font-bold transition-all"
        >
          {copied ? '✅ COPIADO' : '📋 COPIAR CÓDIGO'}
        </button>
      </div>

      <pre className="text-xs text-cyan-300 bg-black/80 p-4 rounded-lg overflow-x-auto leading-relaxed border border-slate-900">
        <code>{snippets[activeTab]}</code>
      </pre>
    </div>
  );
};
