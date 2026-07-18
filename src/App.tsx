import { useState, useEffect, useRef } from 'react';

// SOTA Minimalist Awwwards Theme (YInMn Blue Palette based on v1.1.0)
interface Theme {
  id: string;
  name: string;
  bg: string;
  surface: string;
  border: string;
  accent: string;
  text: string;
  muted: string;
  lapis: string;
  gold: string;
  verify: string;
  breakColor: string;
}

const THEMES: Record<string, Theme> = {
  awwwards: {
    id: 'awwwards',
    name: 'YInMn Noir',
    bg: '#090B19', // --bitumen
    surface: '#0F1226', // --kiln
    border: '#2E3866', // --edge
    accent: '#3B4DFF', // --lapis
    text: '#FFFFFF', // --dust
    muted: '#B4B9DF', // --dust-dim
    lapis: '#3B4DFF',
    gold: '#F59E0B',
    verify: '#10B981',
    breakColor: '#EF4444'
  },
  obsidian: {
    id: 'obsidian',
    name: 'Obsidian Pulse',
    bg: '#000000',
    surface: '#111111',
    border: '#2a2a2a',
    accent: '#FF3366',
    text: '#F0F0F0',
    muted: '#888888',
    lapis: '#FF3366',
    gold: '#F59E0B',
    verify: '#10B981',
    breakColor: '#EF4444'
  }
};

interface FileItem {
  name: string;
  path: string;
  lang: string;
  content: string;
  moduleColor: string; // ADHD Color Tagging
  moduleName: string;
  prediction?: string;
  trigger?: string;
}

interface SkillItem {
  id: string;
  name: string;
  type: string;
  exergy: string;
  desc: string;
  status: 'active' | 'idle' | 'locked';
}

interface DatabaseTable {
  name: string;
  rows: number;
  columns: { name: string; type: string; pk: boolean }[];
}

const PROJECT_FILES: FileItem[] = [
  {
    name: 'active_inference.py',
    path: 'cortex/active_inference.py',
    lang: 'python',
    moduleColor: '#F59E0B', // Gold
    moduleName: 'CORTEX',
    content: `"""
C5-REAL Active Inference Engine.
Minimizes Free Energy (Entropy) across the Swarm.
"""
import numpy as np

def compute_free_energy(observations, predictions):
    # D_{KL}(Q || P) + Expected Surprise
    divergence = np.sum(observations * np.log(observations / predictions))
    return divergence
`,
    trigger: 'def',
    prediction: ' minimize_entropy(state):\n    return compute_free_energy(state.obs, state.pred)'
  },
  {
    name: 'bft_orchestrator.py',
    path: 'cortex/bft_orchestrator.py',
    lang: 'python',
    moduleColor: '#F59E0B', // Gold
    moduleName: 'CORTEX',
    content: `"""
Byzantine Fault Tolerance Orchestrator.
Maintains state consistency across N>=3 agents.
"""
from typing import Any

class BFTOrchestrator:
    def __init__(self, num_nodes: int):
        if num_nodes < 3:
            raise ValueError("BFT requires N>=3")
        self.nodes = num_nodes
`,
    trigger: 'class',
    prediction: ' BFTNode:\n    def validate_hash(self, tx_hash: str) -> bool:\n        pass'
  },
  {
    name: 'robinson.pl',
    path: 'axioms/robinson.pl',
    lang: 'prolog',
    moduleColor: '#10B981', // Verify Green
    moduleName: 'AXIOMS',
    content: `% TEOREMA DE ROBINSON - C5-REAL
% Unificación Martelli-Montanari

unify(X, Y) :- X == Y, !.
unify(X, Y) :- var(X), !, occurs_check(X, Y), X = Y.
unify(X, Y) :- var(Y), !, occurs_check(Y, X), Y = X.
`,
    trigger: 'unify',
    prediction: '(f(A), f(B)) :- unify(A, B).'
  },
  {
    name: 'c5_deploy.yml',
    path: '.github/workflows/c5_deploy.yml',
    lang: 'yaml',
    moduleColor: '#3B4DFF', // Lapis Blue
    moduleName: 'INFRA',
    content: `name: C5-REAL Deploy
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy Swarm
        run: terraform apply -auto-approve
`
  }
];

const PREDEFINED_SKILLS: SkillItem[] = [
  { id: 'S1', name: 'DOM_CSS_Transducer', type: 'Visual', exergy: 'Max', desc: 'Awwwards UI Engine', status: 'active' },
  { id: 'S2', name: 'MCTS_Budget_Forcer', type: 'Logic', exergy: 'Ultra', desc: 'Thermodynamic bounds', status: 'idle' },
  { id: 'S3', name: 'Swarm_Dispatcher', type: 'Orchestrator', exergy: 'High', desc: 'BFT parallelization', status: 'active' },
  { id: 'S4', name: 'OBLITERATOR', type: 'Destructive', exergy: 'Max', desc: 'Entropy vector purge', status: 'locked' }
];

const MOCK_TABLES: DatabaseTable[] = [
  {
    name: 'ledger_entries',
    rows: 14502,
    columns: [
      { name: 'seq', type: 'INTEGER', pk: true },
      { name: 'entry_hash', type: 'VARCHAR(64)', pk: false },
      { name: 'lamport_t', type: 'INTEGER', pk: false },
      { name: 'created_at', type: 'TIMESTAMP', pk: false },
      { name: 'payload', type: 'TEXT', pk: false }
    ]
  },
  {
    name: 'swarm_nodes',
    rows: 5,
    columns: [
      { name: 'node_id', type: 'VARCHAR(36)', pk: true },
      { name: 'role', type: 'VARCHAR(50)', pk: false },
      { name: 'status', type: 'VARCHAR(20)', pk: false },
      { name: 'last_seen', type: 'TIMESTAMP', pk: false }
    ]
  }
];

export default function BabylonCompleteIDE() {
  const [theme, setTheme] = useState<Theme>(THEMES.awwwards);
  const [cognitiveMode, setCognitiveMode] = useState<'NT' | '2E'>('2E'); 
  const [activeFile, setActiveFile] = useState<FileItem>(PROJECT_FILES[0]);
  const [editorContent, setEditorContent] = useState(activeFile.content);
  const [ghostText, setGhostText] = useState('');
  const [cursorPos, setCursorPos] = useState(0);
  const [sidebarTab, setSidebarTab] = useState<'architecture' | 'swarm' | 'ledger' | 'inference' | 'settings'>('architecture');
  
  // State indicators for Tachometer
  const [agentState, setAgentState] = useState<'idle' | 'indexing' | 'working' | 'done'>('idle');

  // UI state variables
  const [isLoaded, setIsLoaded] = useState(false);
  const [activeSkillId, setActiveSkillId] = useState<string | null>(null);
  const [isHypervigilant, setIsHypervigilant] = useState(false);

  // Local Inference Console
  const [promptInput, setPromptInput] = useState('');
  const [inferenceOutput, setInferenceOutput] = useState('');
  const [tokensPerSecond, setTokensPerSecond] = useState(0);
  const [latencyMs, setLatencyMs] = useState(0);

  // Database / SQL Playground
  const [selectedTable, setSelectedTable] = useState<DatabaseTable | null>(MOCK_TABLES[0]);
  const [sqlQuery, setSqlQuery] = useState('SELECT * FROM ledger_entries LIMIT 5;');
  const [queryResults, setQueryResults] = useState<any[]>([]);

  // Ecosystem integrations status
  const [cortexSync, setCortexSync] = useState(true);
  const [moskv1Core, setMoskv1Core] = useState(true);

  // Dictation State & Audio SOTA Waveform Canvas
  const [isDictating, setIsDictating] = useState(false);
  const recognitionRef = useRef<any>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationRef = useRef<number | null>(null);

  // Keyboard Event Listeners for ⌘⇧E & ⌘8
  useEffect(() => {
    setIsLoaded(true);

    const handleKeyDownGlobal = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key.toLowerCase() === 'e') {
        e.preventDefault();
        setCognitiveMode(prev => (prev === 'NT' ? '2E' : 'NT'));
      }
      if ((e.metaKey || e.ctrlKey) && e.key === '8') {
        e.preventDefault();
        setSidebarTab('inference');
      }
    };

    window.addEventListener('keydown', handleKeyDownGlobal);
    return () => {
      window.removeEventListener('keydown', handleKeyDownGlobal);
      if (recognitionRef.current) recognitionRef.current.stop();
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, []);

  // SOTA Canvas Waveform Animation Loop
  useEffect(() => {
    if (isDictating && canvasRef.current) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      let step = 0;
      const draw = () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = isHypervigilant ? '#FF3366' : theme.accent;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        
        // Multi-sine wave calculation for Awwwards level organic voice response
        for (let i = 0; i < canvas.width; i++) {
          const amplitude1 = Math.sin(step * 0.05 + i * 0.03) * 15;
          const amplitude2 = Math.cos(step * 0.08 + i * 0.01) * 8;
          const y = (canvas.height / 2) + amplitude1 + amplitude2;
          if (i === 0) ctx.moveTo(i, y);
          else ctx.lineTo(i, y);
        }
        ctx.stroke();
        step += 1;
        animationRef.current = requestAnimationFrame(draw);
      };
      draw();
    } else {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
        animationRef.current = null;
      }
    }
  }, [isDictating, theme, isHypervigilant]);

  useEffect(() => {
    setEditorContent(activeFile.content);
    setGhostText('');
  }, [activeFile]);

  // Dictation Handler (Web Speech API Wrapper)
  const toggleDictation = () => {
    if (isDictating) {
      recognitionRef.current?.stop();
      setIsDictating(false);
    } else {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (!SpeechRecognition) return alert("Speech API no soportada.");
      
      const recognition = new SpeechRecognition();
      recognition.lang = 'es-ES';
      recognition.continuous = true;
      recognition.interimResults = false;
      recognition.onresult = (event: any) => {
        let text = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) text += event.results[i][0].transcript;
        }
        if (text) {
          // Voice commands processing C5-REAL
          const command = text.trim().toLowerCase();
          if (command.includes('crear archivo')) {
            alert('[VOICE CMD] Crear archivo trigger.');
          } else if (command.includes('limpiar pantalla') || command.includes('clear')) {
            setEditorContent('');
          } else {
            setEditorContent(prev => prev + (prev.endsWith('\n') ? '' : ' ') + text.trim() + '\n');
          }
        }
      };
      recognition.onerror = () => setIsDictating(false);
      recognition.onend = () => isDictating && recognition.start();
      
      try {
        recognition.start();
        recognitionRef.current = recognition;
        setIsDictating(true);
      } catch (err) {}
    }
  };

  // Editor Input
  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setEditorContent(val);
    setCursorPos(e.target.selectionStart);
    if (activeFile.prediction && val.endsWith(activeFile.trigger || '')) {
      setGhostText(activeFile.prediction);
    } else {
      setGhostText('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab' && ghostText) {
      e.preventDefault();
      setEditorContent(editorContent + ghostText);
      setGhostText('');
    }
  };

  // Local Inference Console Action
  const runInference = (promptText = promptInput) => {
    if (!promptText.trim()) return;
    setAgentState('working');
    setInferenceOutput('C5-REAL Silicon Model Attestation Initialized...\n');
    setTokensPerSecond(0);
    setLatencyMs(0);

    let currentTokens = 0;
    const start = performance.now();
    const interval = setInterval(() => {
      currentTokens += 8;
      const progress = Math.min(100, currentTokens);
      const elapsed = performance.now() - start;
      setTokensPerSecond(Math.round((currentTokens / elapsed) * 1000));
      setLatencyMs(Math.round(elapsed));

      setInferenceOutput(prev => prev + `[Node Sync] Generating token stream - segment ${progress/8}...\n`);

      if (currentTokens >= 80) {
        clearInterval(interval);
        setAgentState('done');
        setInferenceOutput(prev => prev + `\n[VERIFIED] Resolution path computed under Mamba layer.\nExecution successful. Code verified to Ledger chain.`);
        setTimeout(() => setAgentState('idle'), 3000);
      }
    }, 200);
  };

  // SQL query executor
  const runSQLQuery = () => {
    if (!sqlQuery.trim()) return;
    setAgentState('indexing');
    setTimeout(() => {
      if (sqlQuery.toLowerCase().includes('ledger_entries')) {
        setQueryResults([
          { seq: 1, entry_hash: '9a339ceb0565c1918c...', lamport_t: 104, created_at: '2026-07-18T04:14:09Z' },
          { seq: 2, entry_hash: 'f62f1cba31f1d0b3a3...', lamport_t: 105, created_at: '2026-07-18T05:01:22Z' },
          { seq: 3, entry_hash: 'e493a30c5ba9d19a3b...', lamport_t: 106, created_at: '2026-07-18T08:21:28Z' }
        ]);
      } else {
        setQueryResults([
          { node_id: 'Alpha', role: 'Consensus Coordinator', status: 'ACTIVE', last_seen: 'Just now' },
          { node_id: 'Beta', role: 'Memory Shield Core', status: 'ACTIVE', last_seen: 'Just now' }
        ]);
      }
      setAgentState('idle');
    }, 400);
  };

  const isDark = theme.id === 'awwwards';

  return (
    <div 
      className={`w-screen h-screen flex flex-col overflow-hidden select-none transition-all duration-[1000ms] ease-out ${isLoaded ? 'opacity-100' : 'opacity-0 scale-[0.99]'}`}
      style={{ backgroundColor: theme.bg, color: theme.text, fontFamily: '"Inter", sans-serif' }}
    >
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@300;400;500&display=swap');
        
        * { box-sizing: border-box; }
        
        ::-webkit-scrollbar { width: 3px; height: 3px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: ${theme.border}; border-radius: 4px; }
        
        .grain {
          position: absolute;
          top: -150%; left: -50%; right: -50%; bottom: -150%;
          width: 200%; height: 400vh;
          background: transparent url('data:image/svg+xml;utf8,%3Csvg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"%3E%3Cfilter id="noiseFilter"%3E%3CfeTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" stitchTiles="stitch"/%3E%3C/filter%3E%3Crect width="100%25" height="100%25" filter="url(%23noiseFilter)"/%3E%3C/svg%3E');
          opacity: ${isDark ? 0.04 : 0.015};
          pointer-events: none;
          z-index: 50;
          animation: grain 8s steps(10) infinite;
        }

        @keyframes grain {
          0%, 100% { transform: translate(0, 0); }
          10% { transform: translate(-5%, -10%); }
          20% { transform: translate(-15%, 5%); }
          30% { transform: translate(7%, -25%); }
          40% { transform: translate(-5%, 25%); }
          50% { transform: translate(-15%, 10%); }
          60% { transform: translate(15%, 0%); }
          70% { transform: translate(0%, 15%); }
          80% { transform: translate(3%, 35%); }
          90% { transform: translate(-10%, 10%); }
        }

        .editor-text {
          font-family: 'JetBrains Mono', monospace;
          font-weight: 300;
          font-size: 13.5px;
          line-height: 1.8;
          letter-spacing: -0.01em;
        }

        .nav-link {
          position: relative;
          color: ${theme.muted};
          transition: color 0.4s ease;
        }
        .nav-link:hover, .nav-link.active {
          color: ${theme.accent};
        }
        .nav-link::after {
          content: '';
          position: absolute;
          bottom: -4px;
          left: 0;
          width: 100%;
          height: 1px;
          background: ${theme.accent};
          transform: scaleX(0);
          transform-origin: right;
          transition: transform 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
        }
        .nav-link:hover::after, .nav-link.active::after {
          transform: scaleX(1);
          transform-origin: left;
        }

        /* Ambient Tachometer Animations */
        @keyframes breathing-blue {
          0%, 100% { opacity: 0.3; transform: scaleX(0.98); }
          50% { opacity: 1; transform: scaleX(1); }
        }
        @keyframes scanning-cobalt {
          0% { background-position: -200% center; }
          100% { background-position: 200% center; }
        }
        @keyframes alert-gold {
          0%, 100% { background-color: #F59E0B; opacity: 0.5; }
          50% { background-color: #EF4444; opacity: 1; }
        }
        
        .tachometer-indexing {
          animation: breathing-blue 2s ease-in-out infinite;
          background: #3B4DFF;
        }
        .tachometer-working {
          background: linear-gradient(90deg, #3B4DFF, #7080FF, #3B4DFF);
          background-size: 200% 100%;
          animation: scanning-cobalt 1.5s infinite linear;
        }
        .tachometer-alert {
          animation: alert-gold 0.8s ease-in-out infinite;
        }
        .tachometer-done {
          background: #10B981;
          transition: background-color 1s ease;
        }

        ${isHypervigilant ? `
          .grain { opacity: 0.12 !important; }
          textarea { color: #FF3366 !important; text-shadow: 0 0 5px rgba(255, 51, 102, 0.3); }
          h1 { color: #FF3366 !important; }
          .nav-link.active { color: #FF3366 !important; }
          .nav-link.active::after { background: #FF3366 !important; }
        ` : ''}
      `}</style>

      <div className="grain" />

      {/* AMBIENT TACHOMETER (3px Top-screen bar for 2E Mode) */}
      {cognitiveMode === '2E' && (
        <div 
          className={`h-[3px] w-full z-50 transition-all duration-500 ${
            agentState === 'indexing' ? 'tachometer-indexing' :
            agentState === 'working' ? 'tachometer-working' :
            agentState === 'done' ? 'tachometer-done' :
            isHypervigilant ? 'tachometer-alert' : 'bg-transparent opacity-10'
          }`}
        />
      )}

      {/* ULTRA MINIMAL HEADER */}
      <header 
        className="h-16 flex items-center justify-between px-10 z-40"
        style={{ WebkitAppRegion: 'drag' } as any}
      >
        <div className="flex items-center gap-12">
          <span className="text-[10px] font-medium tracking-[0.2em] uppercase" style={{ color: theme.accent }}>
            {cognitiveMode === '2E' ? 'B_60' : 'Babylon_60'}
          </span>
          
          <nav className="flex gap-8 text-[11px] font-medium tracking-wide uppercase" style={{ WebkitAppRegion: 'no-drag' } as any}>
            <button className={`nav-link ${sidebarTab === 'architecture' ? 'active' : ''} outline-none`} onClick={() => setSidebarTab('architecture')}>
              {cognitiveMode === '2E' ? '◈' : 'Architecture'}
            </button>
            <button className={`nav-link ${sidebarTab === 'swarm' ? 'active' : ''} outline-none`} onClick={() => setSidebarTab('swarm')}>
              {cognitiveMode === '2E' ? '⎈' : 'Swarm'}
            </button>
            <button className={`nav-link ${sidebarTab === 'ledger' ? 'active' : ''} outline-none`} onClick={() => setSidebarTab('ledger')}>
              {cognitiveMode === '2E' ? '⌬' : 'Ledger'}
            </button>
            <button className={`nav-link ${sidebarTab === 'inference' ? 'active' : ''} outline-none`} onClick={() => setSidebarTab('inference')}>
              {cognitiveMode === '2E' ? '⚡' : 'Inference'}
            </button>
            <button className={`nav-link ${sidebarTab === 'settings' ? 'active' : ''} outline-none`} onClick={() => setSidebarTab('settings')}>
              {cognitiveMode === '2E' ? '⚙' : 'Settings'}
            </button>
          </nav>
        </div>
        
        <div className="flex items-center gap-6" style={{ WebkitAppRegion: 'no-drag' } as any}>
          <button 
            onClick={() => setCognitiveMode(prev => (prev === 'NT' ? '2E' : 'NT'))}
            className="text-[10px] uppercase tracking-widest font-mono text-white/40 hover:text-white transition-colors"
          >
            {cognitiveMode} Mode
          </button>

          <button
            onClick={() => setIsHypervigilant(!isHypervigilant)}
            className="text-[10px] uppercase tracking-widest font-medium outline-none transition-all duration-300"
            style={{ color: isHypervigilant ? '#FF3366' : theme.muted }}
          >
            {isHypervigilant ? '● Vigilant' : 'Vigilance'}
          </button>

          <button
            onClick={toggleDictation}
            className="text-[10px] uppercase tracking-widest font-medium outline-none transition-all duration-300"
            style={{ color: isDictating ? '#FF3333' : theme.muted }}
          >
            {isDictating ? 'Recording' : 'Dictation'}
          </button>
        </div>
      </header>

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 flex overflow-hidden px-10 pb-10 gap-16 relative z-10">
        
        {/* LISTINGS / SECONDARY NAV */}
        <div className="w-64 flex flex-col pt-12">
          {sidebarTab === 'architecture' && (
            <div className="flex flex-col gap-6">
              <span className="text-[10px] tracking-widest uppercase text-white/20">Modules</span>
              {PROJECT_FILES.map(file => (
                <div 
                  key={file.name}
                  onClick={() => setActiveFile(file)}
                  className="flex flex-col cursor-pointer group"
                >
                  <div className="flex items-center gap-2">
                    {/* ADHD Module Tagging (Módulos por Colores) */}
                    <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: file.moduleColor }} />
                    <span 
                      className="text-[13px] font-medium transition-all duration-500"
                      style={{ 
                        color: activeFile.name === file.name ? theme.accent : theme.muted,
                        transform: activeFile.name === file.name ? 'translateX(4px)' : 'none'
                      }}
                    >
                      {file.name}
                    </span>
                  </div>
                  <span className="text-[9px] font-mono mt-1 pl-3.5 text-white/30 uppercase tracking-widest">
                    {file.moduleName}
                  </span>
                </div>
              ))}
            </div>
          )}

          {sidebarTab === 'swarm' && (
            <div className="flex flex-col gap-8">
              {PREDEFINED_SKILLS.map(skill => (
                <div 
                  key={skill.id}
                  onClick={() => setActiveSkillId(skill.id)}
                  className="flex flex-col cursor-pointer group"
                >
                  <div className="flex items-center gap-3">
                    <div 
                      className="w-1.5 h-1.5 rounded-full transition-all duration-500" 
                      style={{ 
                        backgroundColor: skill.status === 'active' ? theme.accent : 'transparent',
                        border: `1px solid ${theme.border}`,
                        transform: activeSkillId === skill.id ? 'scale(1.5)' : 'scale(1)'
                      }} 
                    />
                    <span 
                      className="text-[12px] font-medium transition-all duration-500"
                      style={{ color: activeSkillId === skill.id ? theme.accent : theme.muted }}
                    >
                      {skill.name}
                    </span>
                  </div>
                  
                  <div 
                    className="overflow-hidden transition-all duration-500 pl-4 flex flex-col gap-1"
                    style={{ 
                      maxHeight: activeSkillId === skill.id ? '100px' : '0',
                      opacity: activeSkillId === skill.id ? 1 : 0,
                      marginTop: activeSkillId === skill.id ? '8px' : '0'
                    }}
                  >
                    <span className="text-[10px] uppercase tracking-widest text-white/30">{skill.type} · {skill.exergy}</span>
                    <span className="text-[11px] leading-relaxed opacity-75">{skill.desc}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {sidebarTab === 'ledger' && (
            <div className="flex flex-col gap-6">
              <span className="text-[10px] tracking-widest uppercase text-white/30">Schema & Databases</span>
              {MOCK_TABLES.map(table => (
                <div 
                  key={table.name} 
                  onClick={() => setSelectedTable(table)}
                  className={`cursor-pointer transition-colors p-2 rounded ${selectedTable?.name === table.name ? 'bg-white/5 text-white' : 'text-[#B4B9DF] hover:text-white'}`}
                >
                  <div className="text-[13px] font-medium">{table.name}</div>
                  <div className="text-[10px] font-mono opacity-50">{table.rows} rows</div>
                </div>
              ))}
            </div>
          )}

          {sidebarTab === 'inference' && (
            <div className="flex flex-col gap-8">
              <span className="text-[10px] tracking-widest uppercase text-white/30">Quick Presets</span>
              <button 
                onClick={() => { setPromptInput("Explain the core of the Robinson-Moskv theorem"); runInference("Explain the core of the Robinson-Moskv theorem"); }}
                className="text-left bg-transparent border-0 text-[#B4B9DF] hover:text-white text-[12px] cursor-pointer outline-none"
              >
                ⚡ Robinson Theorem
              </button>
              <button 
                onClick={() => { setPromptInput("Attest current ledger transaction status"); runInference("Attest current ledger transaction status"); }}
                className="text-left bg-transparent border-0 text-[#B4B9DF] hover:text-white text-[12px] cursor-pointer outline-none"
              >
                🛡 Attest Ledger
              </button>
              <button 
                onClick={() => { setPromptInput("Run self-audit loop on active workspace"); runInference("Run self-audit loop on active workspace"); }}
                className="text-left bg-transparent border-0 text-[#B4B9DF] hover:text-white text-[12px] cursor-pointer outline-none"
              >
                ◈ Self-Audit
              </button>
            </div>
          )}

          {sidebarTab === 'settings' && (
            <div className="flex flex-col gap-10">
              <div className="flex flex-col gap-6">
                <span className="text-[10px] tracking-widest uppercase text-white/30">Preferences</span>
                <div className="flex justify-between items-center cursor-pointer group">
                  <span className="text-[12px] transition-colors" style={{ color: theme.accent }}>Typography</span>
                  <span className="text-[10px] font-mono text-white/40">JetBrains Mono</span>
                </div>
                <div className="flex justify-between items-center cursor-pointer group" onClick={toggleDictation}>
                  <span className="text-[12px] transition-colors" style={{ color: theme.accent }}>Voice Override</span>
                  <span className="text-[10px] font-mono" style={{ color: isDictating ? '#FF3333' : theme.muted }}>{isDictating ? 'ON' : 'OFF'}</span>
                </div>
              </div>
              
              <div className="flex flex-col gap-5">
                <span className="text-[10px] tracking-widest uppercase text-white/30">Ecosystem Bridge</span>
                <div className="flex justify-between items-center">
                  <span className="text-[12px] text-white/70">CORTEX Persist Sync</span>
                  <button 
                    onClick={() => setCortexSync(!cortexSync)}
                    className="text-[10px] font-mono border bg-transparent px-2 py-0.5 rounded cursor-pointer text-white/80"
                    style={{ borderColor: cortexSync ? theme.accent : '#555' }}
                  >
                    {cortexSync ? 'CONNECTED' : 'DISCONNECTED'}
                  </button>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[12px] text-white/70">MOSKV-1 Kernels</span>
                  <button 
                    onClick={() => setMoskv1Core(!moskv1Core)}
                    className="text-[10px] font-mono border bg-transparent px-2 py-0.5 rounded cursor-pointer text-white/80"
                    style={{ borderColor: moskv1Core ? theme.accent : '#555' }}
                  >
                    {moskv1Core ? 'ACTIVE' : 'STANDBY'}
                  </button>
                </div>
              </div>

              <div className="flex flex-col gap-5">
                <span className="text-[10px] tracking-widest uppercase text-white/30">Languages</span>
                <div className="flex gap-6 text-[11px] font-mono">
                  <span className="cursor-pointer border-b pb-1" style={{ color: theme.accent, borderColor: theme.accent }}>ES-ES</span>
                  <span className="cursor-pointer pb-1 transition-colors hover:text-white text-white/40">EN-US</span>
                  <span className="cursor-pointer pb-1 transition-colors hover:text-white text-white/40">JA-JP</span>
                  <span className="cursor-pointer pb-1 transition-colors hover:text-white text-white/40">RU-RU</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* EDITOR OR OTHER CONSOLES */}
        <div className="flex-1 flex flex-col relative pt-12">
          
          {sidebarTab === 'inference' ? (
            <div className="flex-1 flex gap-10 relative">
              <div className="flex-1 flex flex-col">
                <h1 className="text-3xl font-light tracking-tight mb-8">Local Inference Console</h1>
                
                <div className="flex flex-col gap-4 mb-6">
                  <span className="text-[10px] font-mono uppercase text-white/40">Local Prompt</span>
                  <textarea
                    value={promptInput}
                    onChange={(e) => setPromptInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        runInference();
                      }
                    }}
                    placeholder="Enter prompt... (Press Enter to submit, Shift+Enter for newline)"
                    className="w-full h-32 bg-white/5 border border-white/10 rounded-md p-4 text-[13.5px] font-mono text-white outline-none focus:border-[#3B4DFF] resize-none"
                  />
                  <div className="flex justify-between">
                    <span className="text-[10px] font-mono text-white/40">Model: mamba-ssm-c5</span>
                    <button 
                      onClick={() => runInference()}
                      className="px-6 py-2 bg-[#3B4DFF] text-white border-0 rounded text-[11px] font-mono tracking-widest uppercase cursor-pointer hover:bg-[#5060FF]"
                    >
                      Execute
                    </button>
                  </div>
                </div>

                <div className="flex-1 flex flex-col">
                  <span className="text-[10px] font-mono uppercase text-white/40 mb-2">Attestation Stream Output</span>
                  <div className="flex-1 bg-black/40 border border-white/5 rounded-md p-4 font-mono text-[12px] overflow-y-auto whitespace-pre text-white/80">
                    {inferenceOutput || 'Awaiting execution. Select a preset or type a prompt above.'}
                  </div>
                </div>
              </div>

              <div className="w-80 border-l border-white/5 pl-10 flex flex-col gap-6">
                <span className="text-[10px] font-mono uppercase text-white/30">Local Attestation Manual</span>
                <div className="flex flex-col gap-4 text-[12.5px] leading-relaxed text-white/70">
                  <p>Every transaction, fact, or code block generated in this console is computed locally under the **Zero-Network Policy**.</p>
                  <p>The resulting logical path is parsed by the local Mamba SSM engine, hash-chained, and anchored directly to the BFT state chain.</p>
                  <p>This guarantees that decisions generated by local silicon are untamperable and fully auditable by downstream validators.</p>
                </div>
                
                {latencyMs > 0 && (
                  <div className="border border-[#3B4DFF]/30 bg-[#3B4DFF]/5 rounded-md p-4 flex flex-col gap-2 mt-auto">
                    <span className="text-[10px] font-mono uppercase text-[#7080FF] tracking-wider">Silicon Throughput</span>
                    <div className="text-2xl font-light">{tokensPerSecond} <span className="text-[11px] font-mono text-white/50">tok/s</span></div>
                    <div className="text-[11px] font-mono text-white/40">Latency: {latencyMs} ms</div>
                  </div>
                )}
              </div>
            </div>

          ) : sidebarTab === 'ledger' ? (
            <div className="flex-1 flex flex-col">
              <h1 className="text-3xl font-light tracking-tight mb-8">Ledger Database Console</h1>
              
              <div className="flex gap-10 flex-1">
                <div className="flex-1 flex flex-col">
                  <div className="flex flex-col gap-3 mb-6">
                    <div className="flex justify-between items-center">
                      <span className="text-[10px] font-mono uppercase text-white/40">SQL query</span>
                      <button 
                        onClick={runSQLQuery}
                        className="px-4 py-1.5 bg-white/10 hover:bg-white/15 text-white border-0 rounded text-[11px] font-mono uppercase cursor-pointer"
                      >
                        Run Query
                      </button>
                    </div>
                    <input 
                      type="text"
                      value={sqlQuery}
                      onChange={(e) => setSqlQuery(e.target.value)}
                      className="bg-white/5 border border-white/10 rounded p-3 text-[13px] font-mono text-white outline-none focus:border-[#3B4DFF]"
                    />
                  </div>

                  <div className="flex-1 bg-black/40 border border-white/5 rounded-md p-4 overflow-auto">
                    {queryResults.length > 0 ? (
                      <table className="w-full border-collapse font-mono text-[12px] text-left text-white/80">
                        <thead>
                          <tr className="border-b border-white/10">
                            {Object.keys(queryResults[0]).map(key => (
                              <th key={key} className="pb-2 font-medium uppercase tracking-wider text-white/40">{key}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {queryResults.map((row, idx) => (
                            <tr key={idx} className="border-b border-white/5 hover:bg-white/5">
                              {Object.values(row).map((val: any, colIdx) => (
                                <td key={colIdx} className="py-2.5 truncate max-w-[200px]" title={val}>{val}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    ) : (
                      <div className="flex items-center justify-center h-full text-white/30 font-mono text-xs uppercase tracking-widest">
                        Awaiting Query Execution
                      </div>
                    )}
                  </div>
                </div>

                <div className="w-72 border-l border-white/5 pl-10 flex flex-col gap-6">
                  {selectedTable ? (
                    <>
                      <span className="text-[10px] font-mono uppercase text-white/30">Schema: {selectedTable.name}</span>
                      <div className="flex flex-col gap-4">
                        {selectedTable.columns.map(col => (
                          <div key={col.name} className="flex justify-between items-baseline font-mono text-xs">
                            <span className={col.pk ? 'text-[#3B4DFF]' : 'text-white/80'}>
                              {col.name} {col.pk && '🔑'}
                            </span>
                            <span className="text-white/30">{col.type}</span>
                          </div>
                        ))}
                      </div>
                    </>
                  ) : (
                    <span className="text-[10px] font-mono uppercase text-white/30">No Table Selected</span>
                  )}
                </div>
              </div>
            </div>

          ) : (
            // STANDARD MINIMAL CODE EDITOR
            <>
              <div className="flex items-baseline justify-between gap-4 mb-12">
                <div className="flex items-baseline gap-4">
                  <h1 className="text-4xl font-light tracking-tight m-0 p-0" style={{ color: theme.accent }}>
                    {activeFile.name.split('.')[0]}
                  </h1>
                  <span className="text-[12px] font-mono tracking-widest" style={{ color: theme.muted }}>
                    .{activeFile.name.split('.')[1]}
                  </span>
                </div>
                {/* Visual indicator of unified ecosystem status */}
                <div className="flex gap-4 text-[9px] font-mono text-white/40 uppercase">
                  <span className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: cortexSync ? theme.verify : theme.breakColor }} />
                    Cortex-Persist: {cortexSync ? 'Sync' : 'Standby'}
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: moskv1Core ? theme.verify : theme.breakColor }} />
                    Moskv-1: {moskv1Core ? 'Apex' : 'Standby'}
                  </span>
                </div>
              </div>

              <div className="flex-1 relative">
                {isHypervigilant && (
                  <div className="absolute top-0 right-0 z-30 flex items-center gap-3 text-[9px] font-mono tracking-[0.2em] text-[#FF3366] uppercase animate-pulse">
                    <span>Threat Level: Zero</span>
                    <span>·</span>
                    <span>Anergy Filter: Strict</span>
                  </div>
                )}

                <textarea
                  value={editorContent}
                  onChange={handleTextChange}
                  onKeyDown={handleKeyDown}
                  spellCheck={false}
                  className="editor-text absolute inset-0 w-full h-full bg-transparent border-0 resize-none outline-none focus:ring-0 z-20"
                  style={{ color: theme.text }}
                />
                
                {ghostText && (
                  <pre className="editor-text absolute inset-0 pointer-events-none z-10 whitespace-pre-wrap">
                    <span className="opacity-0">{editorContent.slice(0, cursorPos)}</span>
                    <span className="opacity-40 transition-opacity duration-1000" style={{ color: theme.muted }}>{ghostText}</span>
                  </pre>
                )}

                {/* SOTA Voice Dictation Overlay (Canvas waveform) */}
                {isDictating && (
                  <div className="absolute bottom-6 right-8 z-30 bg-black/80 border border-white/5 px-6 py-4 rounded-xl flex flex-col gap-3 shadow-2xl w-80">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono tracking-widest text-[#FF3366] uppercase animate-pulse">
                        🎤 Voice Transducer (es-es)
                      </span>
                      <span className="text-[9px] font-mono text-white/40">Ready</span>
                    </div>
                    {/* Live Waveform Canvas */}
                    <canvas ref={canvasRef} width="280" height="40" className="w-full bg-white/5 rounded border border-white/5" />
                    <span className="text-[9px] font-sans text-white/50 leading-relaxed">
                      Say "limpiar pantalla" to clear, or dictate code directly.
                    </span>
                  </div>
                )}
              </div>
              
              {/* FOOTER METADATA */}
              <div className="h-10 flex items-center justify-between text-[10px] font-mono tracking-widest border-t transition-colors duration-500" style={{ borderColor: theme.border, color: theme.muted }}>
                <div className="flex items-center gap-6">
                  <span>{activeFile.path}</span>
                </div>
                <div className="flex items-center gap-8">
                  <span>C5-REAL</span>
                  <span>{activeFile.lang.toUpperCase()}</span>
                </div>
              </div>
            </>
          )}

        </div>
      </div>
    </div>
  );
}
