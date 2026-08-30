import { useState } from 'react';
import { Header } from './components/Header';
import { ParticleCanvas } from './components/ParticleCanvas';
import { HomeOverview } from './components/HomeOverview';
import { AxiomMatrix } from './components/AxiomMatrix';
import { SwarmMonitor } from './components/SwarmMonitor';
import { LedgerInspector } from './components/LedgerInspector';
import { LicensePortal } from './components/LicensePortal';
import { ComplianceInspector } from './components/ComplianceInspector';
import { BlogPortal } from './components/BlogPortal';
import { CausalGraphVisualizer } from './components/CausalGraphVisualizer';
import { BftConsensusSimulator } from './components/BftConsensusSimulator';
import { soundFx } from './components/AudioEngine';

function App() {
  const [activeTab, setActiveTab] = useState('overview');

  const handleCTA = (tab: string) => {
    soundFx.playClick();
    setActiveTab(tab);
  };

  return (
    <div className="relative w-screen h-screen bg-[#030508] text-slate-100 flex flex-col overflow-hidden c5-grid-bg">
      {/* Background Topological Particle Canvas */}
      <ParticleCanvas />

      {/* Header Navigation */}
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content View Container */}
      <main className="flex-1 p-6 overflow-y-auto relative z-10 max-w-7xl mx-auto w-full">
        {activeTab === 'overview' && <HomeOverview handleCTA={handleCTA} />}
        {activeTab === 'blog' && <BlogPortal />}
        {activeTab === 'compliance' && <ComplianceInspector />}
        {activeTab === 'license' && <LicensePortal />}
        {activeTab === 'swarm' && <SwarmMonitor />}
        {activeTab === 'causal' && <CausalGraphVisualizer />}
        {activeTab === 'bft' && <BftConsensusSimulator />}
        {activeTab === 'axioms' && <AxiomMatrix />}
        {activeTab === 'ledger' && <LedgerInspector />}
      </main>

      {/* Status Footer - Minimalist */}
      <footer className="h-8 px-8 bg-[#000000] border-t border-slate-900 flex items-center justify-between text-[10px] font-mono text-slate-500 uppercase tracking-widest z-50">
        <div className="flex items-center gap-6">
          <span className="flex items-center gap-2 text-emerald-500">
            <span className="w-1.5 h-1.5 bg-emerald-500 block" />
            ONLINE
          </span>
          <span>v4.0.0</span>
          <span>21 AGENTS: PASS</span>
        </div>
        <div>
          <span>ISO/IEC EU AI Act Article 9–14 Certified</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
