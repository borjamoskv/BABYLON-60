import React, { useState } from 'react';
import { soundFx } from './AudioEngine';

interface CommandOutput {
  command: string;
  output: string;
  type: 'python' | 'compliance' | 'license' | 'mcp';
}

export const TerminalHero: React.FC = () => {
  const [activeCmd, setActiveCmd] = useState<string>('pip install babylon60');
  const [terminalOutput, setTerminalOutput] = useState<string>(
    `$ pip install babylon60\n[+] Downloading babylon60-1.0.2-py3-none-any.whl (1.4 MB)\n[+] Verifying SHA256 package hash: PASS\n[+] Installed babylon60-1.0.2 successfully.`
  );

  const commands: CommandOutput[] = [
    {
      command: 'pip install babylon60',
      type: 'python',
      output: `$ pip install babylon60\n[+] Downloading babylon60-1.0.2-py3-none-any.whl (1.4 MB)\n[+] Verifying SHA256 package hash: PASS\n[+] Installed babylon60-1.0.2 successfully.`
    },
    {
      command: 'babylon60-compliance --bundle artifact_bundle_v3 --format html',
      type: 'compliance',
      output: `$ babylon60-compliance --bundle artifact_bundle_v3 --format html --output report.html\n[+] Auditando Artículos 9, 10, 11, 12, 14 del EU AI Act...\n[+] Z3 SMT Risk Mitigation Check: 100% PASS\n[+] Generando Informe de Auto-Evaluación en: report.html (SHA256: 30512f6f4a4b...)`
    },
    {
      command: 'babylon60-license generate --owner "AcmeCorp" --tier enterprise',
      type: 'license',
      output: `$ babylon60-license generate --owner "AcmeCorp" --tier enterprise --days 365\n==================================================\nBABYLON60_LICENSE_KEY GENERATED SUCCESSFULLY\n==================================================\nOwner:      AcmeCorp\nTier:       ENTERPRISE\nExpires:    2027-08-13 (365 days)\nLicenseKey: acmecorp:enterprise:1807600000:a7063f41d9f8b916`
    },
    {
      command: 'babylon60-mcp --port 8080',
      type: 'mcp',
      output: `$ babylon60-mcp --port 8080\n[+] C5-REAL MCP Server listening on stdio & http://localhost:8080\n[+] Ledger WAL path resolved to: $BABYLON_HOME/mcp_ledger.db\n[+] Exposed Tools: [bft_append, verify_merkle_root, generate_compliance_report, validate_license_key]`
    }
  ];

  const handleCommandClick = (cmdObj: CommandOutput) => {
    soundFx.playClick();
    setActiveCmd(cmdObj.command);
    setTerminalOutput(cmdObj.output);
  };

  const copyToClipboard = () => {
    soundFx.playSuccess();
    navigator.clipboard.writeText(activeCmd);
  };

  return (
    <div className="glass-panel p-6 space-y-4 font-mono">
      <div className="flex justify-between items-center text-xs text-slate-400 border-b border-slate-800 pb-3">
        <span className="flex items-center gap-2 text-slate-200 font-bold">
          <span className="w-3 h-3 rounded-full bg-cyan-400 animate-pulse" />
          PLAYGROUND CLI DE COMANDOS CANÓNICOS — BABYLON-60 v4.0.0
        </span>
        <div className="flex items-center gap-2">
          <button
            onClick={copyToClipboard}
            className="px-3 py-1 bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 rounded text-cyan-300 text-[11px] font-bold transition-all"
          >
            📋 COPIAR COMANDO
          </button>
        </div>
      </div>

      {/* Command Selector Buttons */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2">
        {commands.map((c) => (
          <button
            key={c.command}
            onClick={() => handleCommandClick(c)}
            className={`p-2.5 rounded border text-left transition-all text-xs truncate ${
              activeCmd === c.command
                ? 'bg-cyan-950/40 border-cyan-500/60 text-cyan-300 font-bold shadow-[0_0_12px_rgba(0,240,255,0.2)]'
                : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
            }`}
          >
            ${c.command.slice(0, 24)}...
          </button>
        ))}
      </div>

      {/* Terminal Screen */}
      <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg text-xs text-cyan-300 overflow-x-auto shadow-inner relative font-mono">
        <pre className="leading-relaxed whitespace-pre-wrap">{terminalOutput}</pre>
      </div>
    </div>
  );
};
