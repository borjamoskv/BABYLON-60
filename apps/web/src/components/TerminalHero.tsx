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
      command: 'babylon60-compliance --format html',
      type: 'compliance',
      output: `$ babylon60-compliance --bundle artifact_bundle_v3 --format html\n[+] Auditando Artículos 9, 10, 11, 12, 14 del EU AI Act...\n[+] Z3 SMT Risk Mitigation Check: 100% PASS\n[+] Generando Informe de Auto-Evaluación en: report.html (SHA256: 30512f6f...)`
    },
    {
      command: 'babylon60-license generate --owner Acme',
      type: 'license',
      output: `$ babylon60-license generate --owner "AcmeCorp" --tier enterprise\n==================================================\nBABYLON60_LICENSE_KEY GENERATED SUCCESSFULLY\n==================================================\nOwner:      AcmeCorp\nTier:       ENTERPRISE\nLicenseKey: acmecorp:enterprise:1807600000:a7063f41d9f8b916`
    },
    {
      command: 'babylon60-mcp --port 8080',
      type: 'mcp',
      output: `$ babylon60-mcp --port 8080\n[+] C5-REAL MCP Server listening on stdio & http://localhost:8080\n[+] Ledger WAL path resolved to: $BABYLON_HOME/mcp_ledger.db\n[+] Exposed Tools: [bft_append, verify_merkle_root]`
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
    <div className="border border-[#27272a] rounded-xl overflow-hidden font-mono bg-[#111111] shadow-2xl">
      {/* Terminal Header */}
      <div className="flex justify-between items-center px-4 py-3 bg-[#18181b] border-b border-[#27272a]">
        <div className="flex items-center gap-3">
          <div className="flex gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#3f3f46]" />
            <span className="w-2.5 h-2.5 rounded-full bg-[#3f3f46]" />
            <span className="w-2.5 h-2.5 rounded-full bg-[#3f3f46]" />
          </div>
          <span className="text-[10px] text-slate-500 uppercase tracking-widest">
            Agentic Console / babylon60
          </span>
        </div>
        <button
          onClick={copyToClipboard}
          className="text-slate-500 hover:text-slate-300 text-[10px] uppercase tracking-widest transition-colors"
        >
          [ COPY ]
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[#27272a] bg-[#111111] overflow-x-auto">
        {commands.map((c) => (
          <button
            key={c.command}
            onClick={() => handleCommandClick(c)}
            className={`px-4 py-2 text-[10px] uppercase tracking-widest whitespace-nowrap transition-colors border-r border-[#27272a] ${
              activeCmd === c.command
                ? 'text-cyan-400 bg-[#18181b] border-b-2 border-b-cyan-500'
                : 'text-slate-500 hover:text-slate-300 hover:bg-[#18181b] border-b-2 border-b-transparent'
            }`}
          >
            {c.type}
          </button>
        ))}
      </div>

      {/* Terminal Output */}
      <div className="p-6 bg-[#0a0a0a] text-[11px] text-slate-300 overflow-x-auto min-h-[160px]">
        <pre className="leading-loose whitespace-pre-wrap">{terminalOutput}</pre>
      </div>
    </div>
  );
};
