import React, { useState } from 'react';
import { soundFx } from './AudioEngine';

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, setActiveTab }) => {
  const [soundEnabled, setSoundEnabled] = useState(false);

  const handleTabClick = (tabId: string) => {
    soundFx.playClick();
    setActiveTab(tabId);
  };

  const handleSoundToggle = () => {
    const newState = soundFx.toggleSound();
    setSoundEnabled(newState);
  };

  return (
    <header className="h-16 px-6 border-b border-[var(--border-cyan)] bg-[rgba(3,5,8,0.88)] backdrop-blur-md flex items-center justify-between z-50 relative">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-500/10 border border-cyan-400/40 flex items-center justify-center font-mono font-bold text-cyan-400 text-lg shadow-[0_0_15px_rgba(0,240,255,0.3)]">
            B60
          </div>
          <div>
            <h1 className="text-base font-bold tracking-wider text-white font-mono flex items-center gap-2">
              BABYLON60.COM <span className="text-xs text-cyan-400 font-normal">v4.0.0</span>
            </h1>
            <p className="text-[10px] text-slate-400 font-mono">Sovereign Layer 0 Hardened Substrate</p>
          </div>
        </div>

        <div className="hidden md:block h-5 w-[1px] bg-slate-800 mx-2" />

        <div className="hidden lg:flex items-center gap-2">
          <span className="c5-badge badge-emerald">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            EU AI ACT: CERTIFIED
          </span>
          <span className="c5-badge badge-cyan">
            21 AGENTS: PASS
          </span>
          <span className="c5-badge badge-amber">
            RELEASE: v4.0.0
          </span>
        </div>
      </div>

      {/* Navigation Tabs & Sound Toggle */}
      <div className="flex items-center gap-3">
        <nav className="flex items-center gap-1 bg-slate-900/60 p-1 rounded-lg border border-slate-800">
          {[
            { id: 'overview', label: '📊 INICIO' },
            { id: 'compliance', label: '🛡️ EU AI ACT' },
            { id: 'license', label: '🔑 LICENCIAS' },
            { id: 'swarm', label: '🐝 ENJAMBRE 21' },
            { id: 'axioms', label: '📐 AXIOMAS Z3' },
            { id: 'ledger', label: '🔗 LEDGER WAL' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleTabClick(tab.id)}
              className={`px-3 py-1.5 rounded-md text-xs font-mono transition-all ${
                activeTab === tab.id
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_10px_rgba(0,240,255,0.2)] font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        <button
          onClick={handleSoundToggle}
          className={`p-2 rounded-lg border font-mono text-xs transition-all ${
            soundEnabled
              ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 shadow-[0_0_10px_rgba(16,185,129,0.3)]'
              : 'bg-slate-900 text-slate-500 border-slate-800 hover:text-slate-300'
          }`}
          title="Alternar Sonido UI"
        >
          {soundEnabled ? '🔊 SONIDO ON' : '🔇 SONIDO OFF'}
        </button>
      </div>
    </header>
  );
};
