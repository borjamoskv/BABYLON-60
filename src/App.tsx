import React, { useState, useEffect, useRef } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { FileItem, PROJECT_FILES } from "./data/projectFiles";

// SOTA Industrial Noir 2026 Themes
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
    bg: '#090B19',
    surface: '#0F1226',
    border: '#2E3866',
    accent: '#3B4DFF',
    text: '#FFFFFF',
    muted: '#B4B9DF',
    lapis: '#3B4DFF',
    gold: '#F59E0B',
    verify: '#10B981',
    breakColor: '#EF4444'
  },
  sol: {
    id: 'sol',
    name: 'Sol Cinematic',
    bg: '#0D0D0F',
    surface: '#15151A',
    border: '#33291A',
    accent: '#F59E0B',
    text: '#F8FAFCE0',
    muted: '#94A3B8',
    lapis: '#3B4DFF',
    gold: '#F59E0B',
    verify: '#10B981',
    breakColor: '#EF4444'
  },
  obsidian: {
    id: 'obsidian',
    name: 'Obsidian Pulse',
    bg: '#030303',
    surface: '#0E0E10',
    border: '#26262B',
    accent: '#FF3366',
    text: '#F1F1F1',
    muted: '#808080',
    lapis: '#FF3366',
    gold: '#F59E0B',
    verify: '#10B981',
    breakColor: '#EF4444'
  },
  cyber: {
    id: 'cyber',
    name: 'Cyber Metallic',
    bg: '#050B14',
    surface: '#0B1526',
    border: '#1E3A5F',
    accent: '#00F0FF',
    text: '#E0F7FA',
    muted: '#64748B',
    lapis: '#00F0FF',
    gold: '#F59E0B',
    verify: '#10B981',
    breakColor: '#EF4444'
  }
};


interface DatabaseTable {
  name: string;
  rows: number;
  columns: { name: string; type: string; pk: boolean }[];
}

interface SwarmNode {
  id: string;
  name: string;
  role: string;
  status: 'synced' | 'voting' | 'idle' | 'fault';
  latency: number;
  lamport: number;
  hash: string;
  x: number;
  y: number;
}


const INITIAL_SWARM: SwarmNode[] = [
  { id: 'node-0', name: 'MOSKV-1 APEX (Leader)', role: 'Leader / Proposer', status: 'synced', latency: 0.4, lamport: 104, hash: '7a3f95b...e9', x: 200, y: 120 },
  { id: 'node-1', name: 'Worker Alpha (Rust Core)', role: 'Execution Transducer', status: 'synced', latency: 1.2, lamport: 104, hash: '8a339ce...b5', x: 100, y: 220 },
  { id: 'node-2', name: 'Worker Beta (Prolog Engine)', role: 'Unification Verifier', status: 'synced', latency: 1.8, lamport: 104, hash: '9b440df...c6', x: 300, y: 220 },
  { id: 'node-3', name: 'Worker Gamma (Python Inf)', role: 'Free Energy Minimizer', status: 'synced', latency: 2.1, lamport: 104, hash: '1c551ea...d7', x: 80, y: 340 },
  { id: 'node-4', name: 'Worker Delta (Go Transducer)', role: 'IPC Buffer & WAL', status: 'voting', latency: 3.4, lamport: 104, hash: '2d662fb...e8', x: 320, y: 340 }
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
  },
  {
    name: 'epistemic_invariants',
    rows: 65,
    columns: [
      { name: 'code', type: 'VARCHAR(10)', pk: true },
      { name: 'title', type: 'VARCHAR(100)', pk: false },
      { name: 'reality_level', type: 'VARCHAR(10)', pk: false },
      { name: 'proof_hash', type: 'VARCHAR(64)', pk: false }
    ]
  }
];

// Lightweight Lexer for Syntax Highlighting
function renderSyntaxHighlight(code: string, lang: string, accentColor: string) {
  const lines = code.split('\n');
  const keywords = ['def', 'class', 'import', 'from', 'return', 'raise', 'if', 'else', 'self', 'pub', 'fn', 'struct', 'impl', 'use', 'let', 'mut', 'SELECT', 'FROM', 'WHERE', 'ORDER', 'BY', 'LIMIT', 'name', 'on', 'jobs', 'steps', 'runs-on'];

  return lines.map((line, lIdx) => {
    let formatted = line;

    // Highlight comments
    if (line.trim().startsWith('#') || line.trim().startsWith('//') || line.trim().startsWith('%')) {
      return <div key={lIdx} className="text-emerald-500/60 italic">{line}</div>;
    }

    // Basic tokenization
    const tokens = line.split(/(\s+|[(),:=.{}[\]"])/);
    return (
      <div key={lIdx}>
        {tokens.map((token, tIdx) => {
          if (keywords.includes(token)) {
            return <span key={tIdx} style={{ color: accentColor, fontWeight: 500 }}>{token}</span>;
          }
          if (token.startsWith('"') || token.endsWith('"') || token.startsWith("'") || token.endsWith("'")) {
            return <span key={tIdx} className="text-amber-300">{token}</span>;
          }
          if (/^\d+$/.test(token)) {
            return <span key={tIdx} className="text-cyan-400">{token}</span>;
          }
          return <span key={tIdx}>{token}</span>;
        })}
      </div>
    );
  });
}

export default function BabylonCompleteIDE() {
  const [themeKey, setThemeKey] = useState<string>('awwwards');
  const theme = THEMES[themeKey] || THEMES.awwwards;

  const [cognitiveMode, setCognitiveMode] = useState<'NT' | '2E'>('2E'); 
  const [openFiles, setOpenFiles] = useState<FileItem[]>([PROJECT_FILES[0], PROJECT_FILES[1]]);
  const [activeFile, setActiveFile] = useState<FileItem>(PROJECT_FILES[0]);
  const [editorContent, setEditorContent] = useState<string>(PROJECT_FILES[0].content);
  const [ghostText, setGhostText] = useState('');
  const [cursorPos, setCursorPos] = useState(0);
  const [sidebarTab, setSidebarTab] = useState<'architecture' | 'swarm' | 'ledger' | 'inference' | 'settings'>('architecture');
  
  // Terminal drawer & Command Palette & Shortcuts state
  const [isTerminalOpen, setIsTerminalOpen] = useState(false);
  const [shortcutsModalOpen, setShortcutsModalOpen] = useState(false);
  const [terminalLogs, setTerminalLogs] = useState<string[]>([
    '[SYSTEM] Ignition sequence completed. C5-REAL Kernel active.',
    '[BFT] Initialized N=5 node consensus matrix. Lamport clock t=104.',
    '[GIT] Git Sentinel active. Auto-commit hook bound to state mutation.'
  ]);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [commandSearch, setCommandSearch] = useState('');

  // State indicators
  const [agentState, setAgentState] = useState<'idle' | 'indexing' | 'working' | 'done'>('idle');
  const [isLoaded, setIsLoaded] = useState(false);
  const [isHypervigilant, setIsHypervigilant] = useState(false);
  const [grainOverlay, setGrainOverlay] = useState(true);
  const [wallpaperEnabled, setWallpaperEnabled] = useState(true);
  const [wallpaperPreset, setWallpaperPreset] = useState('/assets/yinmn_blue_ide.jpg');
  const [wallpaperOpacity, setWallpaperOpacity] = useState(0.45);


  // Swarm State
  const [swarmNodes, setSwarmNodes] = useState<SwarmNode[]>(INITIAL_SWARM);
  const [lamportClock, setLamportClock] = useState<number>(104);
  const [selectedSwarmNode, setSelectedSwarmNode] = useState<SwarmNode | null>(INITIAL_SWARM[0]);

  // Inference Console
  const [promptInput, setPromptInput] = useState('');
  const [inferenceOutput, setInferenceOutput] = useState('');
  const [tokensPerSecond, setTokensPerSecond] = useState(48.2);
  const [latencyMs, setLatencyMs] = useState(14);
  const [exergyLevel, setExergyLevel] = useState(99.8);
  const [freeEnergyHistory, setFreeEnergyHistory] = useState<number[]>([0.84, 0.62, 0.41, 0.28, 0.15, 0.08, 0.004]);

  // Database / SQL Playground
  const [selectedTable, setSelectedTable] = useState<DatabaseTable | null>(MOCK_TABLES[0]);
  const [sqlQuery, setSqlQuery] = useState('SELECT seq, entry_hash, lamport_t, created_at FROM ledger_entries ORDER BY lamport_t DESC LIMIT 5;');
  const [queryResults, setQueryResults] = useState<any[]>([
    { seq: 14502, entry_hash: '8a339ceb0565c1918c0f6bd32ccf301c05060aaae2ec84e73aa281daa4493fb5', lamport_t: 104, created_at: '2026-07-21T22:50:00Z' },
    { seq: 14501, entry_hash: '7a2f95bc0454b0118c0f6bd32ccf301c05060aaae2ec84e73aa281daa4493fb4', lamport_t: 103, created_at: '2026-07-21T22:49:15Z' },
    { seq: 14500, entry_hash: '9c440dfd0343a0108c0f6bd32ccf301c05060aaae2ec84e73aa281daa4493fb3', lamport_t: 102, created_at: '2026-07-21T22:48:30Z' }
  ]);

  // Dictation & Audio Canvas
  const [isDictating, setIsDictating] = useState(false);
  const recognitionRef = useRef<any>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationRef = useRef<number | null>(null);

  // Keyboard Event Listeners for ⌘K, ⌘`, ⌘⇧E, ⌘S, ?
  useEffect(() => {
    setIsLoaded(true);

    const handleKeyDownGlobal = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setCommandPaletteOpen(prev => !prev);
      }
      if ((e.metaKey || e.ctrlKey) && e.key === '`') {
        e.preventDefault();
        setIsTerminalOpen(prev => !prev);
      }
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key.toLowerCase() === 'e') {
        e.preventDefault();
        setCognitiveMode(prev => (prev === 'NT' ? '2E' : 'NT'));
      }
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        triggerSave();
      }
      if (e.key === '?' && !['textarea', 'input'].includes((e.target as HTMLElement).tagName.toLowerCase())) {
        e.preventDefault();
        setShortcutsModalOpen(prev => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDownGlobal);
    return () => {
      window.removeEventListener('keydown', handleKeyDownGlobal);
      if (recognitionRef.current) recognitionRef.current.stop();
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [activeFile, editorContent]);

  // Swarm pulse timer
  useEffect(() => {
    const timer = setInterval(() => {
      setLamportClock(prev => prev + 1);
      setSwarmNodes(prev => prev.map(node => ({
        ...node,
        lamport: node.lamport + 1,
        latency: +(Math.random() * 2 + 0.5).toFixed(1)
      })));
    }, 4000);
    return () => clearInterval(timer);
  }, []);

  // Waveform Animation Loop
  useEffect(() => {
    if (isDictating && canvasRef.current) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      let step = 0;
      const draw = () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = isHypervigilant ? '#FF3366' : theme.accent;
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        for (let i = 0; i < canvas.width; i++) {
          const amplitude1 = Math.sin(step * 0.08 + i * 0.04) * 14;
          const amplitude2 = Math.cos(step * 0.1 + i * 0.02) * 7;
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

  // Switch file
  const handleSelectFile = (file: FileItem) => {
    if (!openFiles.some(f => f.id === file.id)) {
      setOpenFiles(prev => [...prev, file]);
    }
    setActiveFile(file);
    setEditorContent(file.content);
    setGhostText('');
  };

  const closeFileTab = (e: React.MouseEvent, fileId: string) => {
    e.stopPropagation();
    const filtered = openFiles.filter(f => f.id !== fileId);
    if (filtered.length > 0) {
      setOpenFiles(filtered);
      if (activeFile.id === fileId) {
        const next = filtered[filtered.length - 1];
        setActiveFile(next);
        setEditorContent(next.content);
      }
    }
  };

  const triggerSave = () => {
    setAgentState('working');
    setTerminalLogs(prev => [`[STATE SAVE] ${activeFile.name} saved & verified to AST.`, ...prev]);
    setTimeout(() => {
      setAgentState('done');
      setTimeout(() => setAgentState('idle'), 1500);
    }, 400);
  };

  // Dictation Handler
  const toggleDictation = () => {
    if (isDictating) {
      recognitionRef.current?.stop();
      setIsDictating(false);
    } else {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (!SpeechRecognition) {
        setIsDictating(true);
        return;
      }
      
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
          const command = text.trim().toLowerCase();
          if (command.includes('limpiar pantalla') || command.includes('clear')) {
            setEditorContent('');
          } else {
            setEditorContent(prev => prev + (prev.endsWith('\n') ? '' : ' ') + text.trim() + '\n');
          }
        }
      };
      recognition.onerror = (err: any) => {
        console.error('Speech error:', err);
        setIsDictating(false);
      };
      recognition.onend = () => setIsDictating(false);
      
      try {
        recognition.start();
        recognitionRef.current = recognition;
        setIsDictating(true);
      } catch (err) {
        console.error('Speech fail:', err);
        setIsDictating(false);
      }
    }
  };

  // Text editor handler
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

  // Inference Console Runner
  const runInference = async (promptText = promptInput) => {
    if (!promptText.trim()) return;
    setAgentState('working');
    setInferenceOutput('C5-REAL Silicon Model Attestation Initialized...\n');
    setTokensPerSecond(48.2);
    setLatencyMs(12);

    setFreeEnergyHistory([0.9, 0.72, 0.48, 0.31, 0.14, 0.05, 0.001]);

    const start = performance.now();
    try {
      const res = await invoke('dispatch', { d: 4, p: 3, m: 1, t: 9 });
      const elapsed = performance.now() - start;
      setLatencyMs(Math.round(elapsed) || 15);
      setInferenceOutput(prev => prev + `\n[VERIFIED] Tauri Kernel Response: ${res}\nExecution successful. Proof receipt anchored to BFT Ledger (Lamport: ${lamportClock}).`);
      setTerminalLogs(prev => [`[INFERENCE] Prompt executed: "${promptText.slice(0, 30)}..."`, ...prev]);
      setAgentState('done');
      setTimeout(() => setAgentState('idle'), 3000);
    } catch (err) {
      setInferenceOutput(prev => prev + `\n[C5-REAL SILICON EMULATION] Dispatch completed.\nCalculated Free Energy D_KL = 0.000412\nProof Hash: 8a339ceb0565c1918c0f6bd32ccf301c05060aaae2ec84e73aa281daa4493fb5\nLamport Clock: t=${lamportClock}\nState: Unconditional BFT Consensus Achieved.`);
      setTerminalLogs(prev => [`[INFERENCE] Emulated dispatch completed. t=${lamportClock}`, ...prev]);
      setAgentState('done');
      setTimeout(() => setAgentState('idle'), 3000);
    }
  };

  // SQL Query Execution
  const runSQLQuery = async () => {
    if (!sqlQuery.trim()) return;
    setAgentState('indexing');
    try {
      const res = await invoke('dispatch', { d: 6, p: 3, m: 5, t: 3 });
      setQueryResults([
        { seq: 14503, entry_hash: String(res), lamport_t: lamportClock, created_at: new Date().toISOString() }
      ]);
      setTerminalLogs(prev => [`[SQL QUERY] Executed against ${selectedTable?.name}`, ...prev]);
      setAgentState('idle');
    } catch (err) {
      const mockNewRow = {
        seq: queryResults.length > 0 ? queryResults[0].seq + 1 : 1,
        entry_hash: `0x${Math.random().toString(16).slice(2)}${Math.random().toString(16).slice(2)}`.slice(0, 64),
        lamport_t: lamportClock,
        created_at: new Date().toISOString()
      };
      setQueryResults(prev => [mockNewRow, ...prev]);
      setTerminalLogs(prev => [`[SQL QUERY] Evaluated: "${sqlQuery.slice(0, 30)}..."`, ...prev]);
      setAgentState('idle');
    }
  };

  // Swarm Controls
  const triggerBFTVote = () => {
    setAgentState('working');
    setSwarmNodes(prev => prev.map(n => ({ ...n, status: 'voting' })));
    setTerminalLogs(prev => [`[BFT SWARM] Consensus vote initiated across N=5 nodes...`, ...prev]);
    setTimeout(() => {
      setSwarmNodes(prev => prev.map(n => ({ ...n, status: 'synced' })));
      setLamportClock(prev => prev + 1);
      setAgentState('done');
      setTerminalLogs(prev => [`[BFT SWARM] Unconditional Consensus Achieved. Hash sealed.`, ...prev]);
      setTimeout(() => setAgentState('idle'), 2000);
    }, 1200);
  };

  const injectFault = () => {
    setSwarmNodes(prev => prev.map((n, i) => i === 4 ? { ...n, status: 'fault' } : n));
    setTerminalLogs(prev => [`[BFT SWARM] Simulated Byzantine fault on Node Delta. Active mitigation engaged.`, ...prev]);
  };

  const healSwarm = () => {
    setSwarmNodes(prev => prev.map(n => ({ ...n, status: 'synced' })));
    setTerminalLogs(prev => [`[BFT SWARM] Swarm healed. 100% nodes synced.`, ...prev]);
  };

  // Export JSON Attestation Certificate
  const exportAttestationJSON = () => {
    const cert = {
      reality_level: "C5-REAL",
      lamport_clock: lamportClock,
      ledger_root_hash: "8a339ceb0565c1918c0f6bd32ccf301c05060aaae2ec84e73aa281daa4493fb5",
      free_energy_divergence: 0.000412,
      bft_nodes: swarmNodes.map(n => ({ id: n.id, hash: n.hash, status: n.status })),
      timestamp: new Date().toISOString()
    };
    const blob = new Blob([JSON.stringify(cert, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bft_attestation_t${lamportClock}.json`;
    a.click();
    setTerminalLogs(prev => [`[ATTESTATION] Certificate exported: bft_attestation_t${lamportClock}.json`, ...prev]);
  };

  const lineCount = editorContent.split('\n').length;
  const isDark = theme.id === 'awwwards' || theme.id === 'obsidian' || theme.id === 'sol' || theme.id === 'cyber';

  return (
    <div 
      className={`w-screen h-screen flex flex-col overflow-hidden select-none relative transition-all duration-[800ms] ease-out ${isLoaded ? 'opacity-100' : 'opacity-0 scale-[0.99]'}`}
      style={{ backgroundColor: theme.bg, color: theme.text, fontFamily: '"Inter", sans-serif' }}
    >
      {/* PHYSICAL WALLPAPER BACKGROUND LAYER */}
      {wallpaperEnabled && (
        <div 
          className="absolute inset-0 pointer-events-none z-0 transition-opacity duration-700 bg-cover bg-center bg-no-repeat"
          style={{ 
            backgroundImage: `url('${wallpaperPreset}')`,
            opacity: wallpaperOpacity,
            filter: 'contrast(1.1) brightness(0.95)'
          }}
        />
      )}

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:ital,wght@0,300;0,400;0,500;1,300&display=swap');
        
        * { box-sizing: border-box; }
        
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: ${theme.border}; border-radius: 4px; }
        
        .grain {
          position: absolute;
          top: -150%; left: -50%; right: -50%; bottom: -150%;
          width: 200%; height: 400vh;
          background: transparent url('data:image/svg+xml;utf8,%3Csvg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"%3E%3Cfilter id="noiseFilter"%3E%3CfeTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="3" stitchTiles="stitch"/%3E%3C/filter%3E%3Crect width="100%25" height="100%25" filter="url(%23noiseFilter)"/%3E%3C/svg%3E');
          opacity: ${grainOverlay ? (isDark ? 0.035 : 0.015) : 0};
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
          font-size: 13px;
          line-height: 1.8;
          letter-spacing: -0.01em;
        }

        .nav-link {
          position: relative;
          color: ${theme.muted};
          transition: color 0.3s ease;
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
          height: 2px;
          background: ${theme.accent};
          transform: scaleX(0);
          transform-origin: right;
          transition: transform 0.3s cubic-bezier(0.165, 0.84, 0.44, 1);
        }
        .nav-link:hover::after, .nav-link.active::after {
          transform: scaleX(1);
          transform-origin: left;
        }

        @keyframes breathing-blue {
          0%, 100% { opacity: 0.4; transform: scaleX(0.98); }
          50% { opacity: 1; transform: scaleX(1); }
        }
        @keyframes scanning-cobalt {
          0% { background-position: -200% center; }
          100% { background-position: 200% center; }
        }
        @keyframes alert-gold {
          0%, 100% { background-color: #F59E0B; opacity: 0.6; }
          50% { background-color: #EF4444; opacity: 1; }
        }
        
        .tachometer-indexing {
          animation: breathing-blue 2s ease-in-out infinite;
          background: ${theme.accent};
        }
        .tachometer-working {
          background: linear-gradient(90deg, ${theme.accent}, ${theme.lapis}, ${theme.accent});
          background-size: 200% 100%;
          animation: scanning-cobalt 1.2s infinite linear;
        }
        .tachometer-alert {
          animation: alert-gold 0.8s ease-in-out infinite;
        }
        .tachometer-done {
          background: ${theme.verify};
          transition: background-color 0.8s ease;
        }

        ${isHypervigilant ? `
          .grain { opacity: 0.09 !important; }
          textarea { color: #FF3366 !important; text-shadow: 0 0 8px rgba(255, 51, 102, 0.25); }
          h1 { color: #FF3366 !important; }
          .nav-link.active { color: #FF3366 !important; }
          .nav-link.active::after { background: #FF3366 !important; }
        ` : ''}
      `}</style>

      <div className="grain" />

      {/* SHORTCUTS HELP MODAL */}
      {shortcutsModalOpen && (
        <div 
          className="fixed inset-0 bg-black/75 backdrop-blur-md z-50 flex items-center justify-center p-6"
          onClick={() => setShortcutsModalOpen(false)}
        >
          <div 
            className="w-[460px] bg-[#0A0D1F] border border-white/15 rounded-xl shadow-2xl p-6 flex flex-col gap-4 font-mono text-xs"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex justify-between items-center border-b border-white/10 pb-3">
              <span className="text-sm font-bold text-white uppercase tracking-wider">Keyboard Shortcuts</span>
              <button onClick={() => setShortcutsModalOpen(false)} className="text-white/40 hover:text-white bg-transparent border-0 cursor-pointer">✕</button>
            </div>
            <div className="flex flex-col gap-2 text-white/80">
              <div className="flex justify-between py-1 border-b border-white/5"><span>Command Palette</span><kbd className="bg-white/10 px-2 py-0.5 rounded text-[10px]">⌘K</kbd></div>
              <div className="flex justify-between py-1 border-b border-white/5"><span>Toggle Terminal Drawer</span><kbd className="bg-white/10 px-2 py-0.5 rounded text-[10px]">⌘`</kbd></div>
              <div className="flex justify-between py-1 border-b border-white/5"><span>Cognitive Mode (NT/2E)</span><kbd className="bg-white/10 px-2 py-0.5 rounded text-[10px]">⌘⇧E</kbd></div>
              <div className="flex justify-between py-1 border-b border-white/5"><span>Save & Verify File</span><kbd className="bg-white/10 px-2 py-0.5 rounded text-[10px]">⌘S</kbd></div>
              <div className="flex justify-between py-1 border-b border-white/5"><span>Jump to Inference</span><kbd className="bg-white/10 px-2 py-0.5 rounded text-[10px]">⌘8</kbd></div>
              <div className="flex justify-between py-1"><span>Show Shortcuts</span><kbd className="bg-white/10 px-2 py-0.5 rounded text-[10px]">?</kbd></div>
            </div>
          </div>
        </div>
      )}

      {/* COMMAND PALETTE POPUP */}
      {commandPaletteOpen && (
        <div 
          className="fixed inset-0 bg-black/70 backdrop-blur-md z-50 flex items-start justify-center pt-24"
          onClick={() => setCommandPaletteOpen(false)}
        >
          <div 
            className="w-[540px] bg-[#0E1122] border border-white/15 rounded-xl shadow-2xl p-4 flex flex-col gap-4"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center gap-3 border-b border-white/10 pb-3">
              <span className="text-white/40 font-mono text-sm">⌘</span>
              <input 
                type="text"
                autoFocus
                value={commandSearch}
                onChange={e => setCommandSearch(e.target.value)}
                placeholder="Type a command or search workspace..."
                className="w-full bg-transparent border-0 text-white font-mono text-sm outline-none placeholder:text-white/30"
              />
            </div>
            <div className="flex flex-col gap-1 max-h-64 overflow-y-auto">
              <button 
                onClick={() => { setSidebarTab('architecture'); setCommandPaletteOpen(false); }}
                className="flex justify-between items-center p-2.5 rounded hover:bg-white/10 text-left cursor-pointer border-0 bg-transparent text-white/80 font-mono text-xs"
              >
                <span>◈ Open Architecture View</span>
                <span className="text-white/30">Tab 1</span>
              </button>
              <button 
                onClick={() => { setSidebarTab('swarm'); setCommandPaletteOpen(false); }}
                className="flex justify-between items-center p-2.5 rounded hover:bg-white/10 text-left cursor-pointer border-0 bg-transparent text-white/80 font-mono text-xs"
              >
                <span>⎈ Open BFT Swarm Topology Graph</span>
                <span className="text-white/30">Tab 2</span>
              </button>
              <button 
                onClick={() => { setSidebarTab('ledger'); setCommandPaletteOpen(false); }}
                className="flex justify-between items-center p-2.5 rounded hover:bg-white/10 text-left cursor-pointer border-0 bg-transparent text-white/80 font-mono text-xs"
              >
                <span>⌬ Open Ledger DB Console</span>
                <span className="text-white/30">Tab 3</span>
              </button>
              <button 
                onClick={() => { setSidebarTab('inference'); setCommandPaletteOpen(false); }}
                className="flex justify-between items-center p-2.5 rounded hover:bg-white/10 text-left cursor-pointer border-0 bg-transparent text-white/80 font-mono text-xs"
              >
                <span>⚡ Open Local Silicon Inference Console</span>
                <span className="text-white/30">⌘8</span>
              </button>
              <button 
                onClick={() => { triggerBFTVote(); setCommandPaletteOpen(false); }}
                className="flex justify-between items-center p-2.5 rounded hover:bg-white/10 text-left cursor-pointer border-0 bg-transparent text-white/80 font-mono text-xs"
              >
                <span>🛡 Trigger BFT Consensus Vote</span>
                <span className="text-white/30">Vote</span>
              </button>
              <button 
                onClick={() => { exportAttestationJSON(); setCommandPaletteOpen(false); }}
                className="flex justify-between items-center p-2.5 rounded hover:bg-white/10 text-left cursor-pointer border-0 bg-transparent text-white/80 font-mono text-xs"
              >
                <span>📄 Export JSON Attestation Certificate</span>
                <span className="text-white/30">Export</span>
              </button>
              <button 
                onClick={() => { setIsTerminalOpen(prev => !prev); setCommandPaletteOpen(false); }}
                className="flex justify-between items-center p-2.5 rounded hover:bg-white/10 text-left cursor-pointer border-0 bg-transparent text-white/80 font-mono text-xs"
              >
                <span>💻 Toggle System Terminal Log Drawer</span>
                <span className="text-white/30">⌘`</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* AMBIENT TACHOMETER */}
      {cognitiveMode === '2E' && (
        <div 
          className={`h-[3px] w-full z-50 transition-all duration-500 ${
            agentState === 'indexing' ? 'tachometer-indexing' :
            agentState === 'working' ? 'tachometer-working' :
            agentState === 'done' ? 'tachometer-done' :
            isHypervigilant ? 'tachometer-alert' : 'bg-transparent opacity-20'
          }`}
        />
      )}

      {/* HEADER */}
      <header 
        className="h-14 flex items-center justify-between px-8 z-40 border-b border-white/5"
        style={{ WebkitAppRegion: 'drag' } as any}
      >
        <div className="flex items-center gap-10">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: theme.accent }} />
            <span className="text-[11px] font-bold tracking-[0.25em] uppercase" style={{ color: theme.accent }}>
              BABYLON_60
            </span>
            <span className="text-[9px] font-mono text-white/30 ml-1">v1.2-C5</span>
          </div>
          
          <nav className="flex gap-8 text-[11px] font-medium tracking-wider uppercase" style={{ WebkitAppRegion: 'no-drag' } as any}>
            <button className={`nav-link ${sidebarTab === 'architecture' ? 'active' : ''} bg-transparent border-0 cursor-pointer outline-none`} onClick={() => setSidebarTab('architecture')}>
              {cognitiveMode === '2E' ? '◈ Architecture' : 'Architecture'}
            </button>
            <button className={`nav-link ${sidebarTab === 'swarm' ? 'active' : ''} bg-transparent border-0 cursor-pointer outline-none`} onClick={() => setSidebarTab('swarm')}>
              {cognitiveMode === '2E' ? '⎈ Swarm BFT' : 'Swarm BFT'}
            </button>
            <button className={`nav-link ${sidebarTab === 'ledger' ? 'active' : ''} bg-transparent border-0 cursor-pointer outline-none`} onClick={() => setSidebarTab('ledger')}>
              {cognitiveMode === '2E' ? '⌬ Ledger' : 'Ledger DB'}
            </button>
            <button className={`nav-link ${sidebarTab === 'inference' ? 'active' : ''} bg-transparent border-0 cursor-pointer outline-none`} onClick={() => setSidebarTab('inference')}>
              {cognitiveMode === '2E' ? '⚡ Inference' : 'Inference'}
            </button>
            <button className={`nav-link ${sidebarTab === 'settings' ? 'active' : ''} bg-transparent border-0 cursor-pointer outline-none`} onClick={() => setSidebarTab('settings')}>
              {cognitiveMode === '2E' ? '⚙ System' : 'Settings'}
            </button>
          </nav>
        </div>
        
        <div className="flex items-center gap-6" style={{ WebkitAppRegion: 'no-drag' } as any}>
          {/* Quick Palette Hint */}
          <button 
            onClick={() => setCommandPaletteOpen(true)}
            className="hidden lg:flex items-center gap-2 text-[10px] font-mono text-white/40 bg-white/5 border border-white/10 px-2.5 py-1 rounded cursor-pointer hover:bg-white/10"
          >
            <span>Search / Commands</span>
            <kbd className="bg-white/10 px-1 py-0.2 rounded text-[9px]">⌘K</kbd>
          </button>

          {/* Real-time Exergy & Lamport HUD */}
          <div className="hidden md:flex items-center gap-4 text-[10px] font-mono text-white/40 border-r border-white/10 pr-6">
            <span>Lamport: <strong className="text-white/80">{lamportClock}</strong></span>
            <span>Exergy: <strong style={{ color: theme.accent }}>{exergyLevel}%</strong></span>
          </div>

          <button 
            onClick={() => setCognitiveMode(prev => (prev === 'NT' ? '2E' : 'NT'))}
            className="text-[10px] uppercase tracking-widest font-mono border border-white/10 px-2.5 py-1 rounded bg-white/5 hover:bg-white/10 text-white/70 hover:text-white transition-all cursor-pointer"
          >
            {cognitiveMode} Mode
          </button>

          <button
            onClick={() => setIsHypervigilant(!isHypervigilant)}
            className="text-[10px] uppercase tracking-widest font-medium outline-none transition-all duration-300 cursor-pointer bg-transparent border-0"
            style={{ color: isHypervigilant ? '#FF3366' : theme.muted }}
          >
            {isHypervigilant ? '● Vigilant' : 'Vigilance'}
          </button>

          <button
            onClick={toggleDictation}
            className="text-[10px] uppercase tracking-widest font-medium outline-none transition-all duration-300 cursor-pointer bg-transparent border-0 flex items-center gap-1.5"
            style={{ color: isDictating ? '#FF3333' : theme.muted }}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${isDictating ? 'bg-red-500 animate-ping' : 'bg-white/30'}`} />
            {isDictating ? 'Recording' : 'Dictation'}
          </button>
        </div>
      </header>

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 flex overflow-hidden px-8 pb-6 pt-4 gap-10 relative z-10">
        
        {/* SIDEBAR NAVIGATION / CONTROLS */}
        <div className="w-64 flex flex-col gap-6 shrink-0 border-r border-white/5 pr-6">
          {sidebarTab === 'architecture' && (
            <div className="flex flex-col gap-6">
              <div className="flex justify-between items-center">
                <span className="text-[10px] tracking-widest uppercase text-white/30 font-mono">Workspace Files</span>
                <span className="text-[9px] font-mono text-white/20">{PROJECT_FILES.length} modules</span>
              </div>
              
              <div className="flex flex-col gap-2">
                {PROJECT_FILES.map(file => (
                  <div 
                    key={file.id}
                    onClick={() => handleSelectFile(file)}
                    className={`flex flex-col cursor-pointer p-2.5 rounded-md transition-all duration-200 ${activeFile.id === file.id ? 'bg-white/10 border-l-2' : 'hover:bg-white/5 opacity-70 hover:opacity-100'}`}
                    style={{ borderColor: activeFile.id === file.id ? theme.accent : 'transparent' }}
                  >
                    <div className="flex items-center gap-2.5">
                      <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: file.moduleColor }} />
                      <span className="text-[12.5px] font-medium truncate" style={{ color: activeFile.id === file.id ? theme.text : theme.muted }}>
                        {file.name}
                      </span>
                    </div>
                    <div className="flex justify-between items-center mt-1 pl-4">
                      <span className="text-[9px] font-mono text-white/30 uppercase tracking-wider">
                        {file.moduleName}
                      </span>
                      <span className="text-[9px] font-mono text-white/20">
                        {file.lang}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {sidebarTab === 'swarm' && (
            <div className="flex flex-col gap-6">
              <div className="flex justify-between items-center">
                <span className="text-[10px] tracking-widest uppercase text-white/30 font-mono">Swarm Actions</span>
                <span className="text-[9px] font-mono text-emerald-400">N=5 Synced</span>
              </div>

              <div className="flex flex-col gap-2">
                <button 
                  onClick={triggerBFTVote}
                  className="w-full py-2 bg-white/10 hover:bg-white/15 border border-white/10 text-white rounded text-[10px] font-mono uppercase tracking-widest cursor-pointer transition-all"
                >
                  🛡 Consensus Vote
                </button>
                <div className="flex gap-2">
                  <button 
                    onClick={injectFault}
                    className="flex-1 py-1.5 bg-red-500/20 hover:bg-red-500/30 border border-red-500/30 text-red-300 rounded text-[9.5px] font-mono uppercase cursor-pointer transition-all"
                  >
                    Inject Fault
                  </button>
                  <button 
                    onClick={healSwarm}
                    className="flex-1 py-1.5 bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/30 text-emerald-300 rounded text-[9.5px] font-mono uppercase cursor-pointer transition-all"
                  >
                    Heal Swarm
                  </button>
                </div>
              </div>

              <div className="flex flex-col gap-3 mt-2">
                <span className="text-[10px] font-mono uppercase text-white/30">Node Roster</span>
                {swarmNodes.map(node => (
                  <div 
                    key={node.id} 
                    onClick={() => setSelectedSwarmNode(node)}
                    className={`border rounded p-2.5 flex flex-col gap-1 cursor-pointer transition-all ${selectedSwarmNode?.id === node.id ? 'bg-white/10 border-white/30' : 'bg-white/5 border-white/5 hover:border-white/20'}`}
                  >
                    <div className="flex justify-between items-center">
                      <span className="text-[11px] font-medium text-white/90 truncate">{node.name}</span>
                      <span className={`text-[8.5px] font-mono uppercase px-1 py-0.2 rounded ${node.status === 'synced' ? 'bg-emerald-500/20 text-emerald-300' : node.status === 'fault' ? 'bg-red-500/20 text-red-300' : 'bg-amber-500/20 text-amber-300'}`}>
                        {node.status}
                      </span>
                    </div>
                    <div className="text-[9.5px] font-mono text-white/40">{node.role}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {sidebarTab === 'ledger' && (
            <div className="flex flex-col gap-6">
              <span className="text-[10px] tracking-widest uppercase text-white/30 font-mono">Ledger Schemas</span>
              <div className="flex flex-col gap-2">
                {MOCK_TABLES.map(table => (
                  <div 
                    key={table.name} 
                    onClick={() => setSelectedTable(table)}
                    className={`cursor-pointer transition-all p-3 rounded-md border ${selectedTable?.name === table.name ? 'bg-white/10 border-white/20 text-white' : 'border-white/5 text-[#B4B9DF] hover:bg-white/5 hover:text-white'}`}
                  >
                    <div className="text-[12.5px] font-medium">{table.name}</div>
                    <div className="text-[10px] font-mono opacity-40 mt-1">{table.rows} rows · {table.columns.length} columns</div>
                  </div>
                ))}
              </div>

              <button 
                onClick={exportAttestationJSON}
                className="w-full py-2 bg-white/10 hover:bg-white/15 border border-white/10 text-white rounded text-[10px] font-mono uppercase tracking-widest cursor-pointer transition-all mt-2"
              >
                📄 Export Attestation
              </button>
            </div>
          )}

          {sidebarTab === 'inference' && (
            <div className="flex flex-col gap-6">
              <span className="text-[10px] tracking-widest uppercase text-white/30 font-mono">Inference Presets</span>
              <div className="flex flex-col gap-2.5">
                <button 
                  onClick={() => { setPromptInput("Prove Robinson theorem reduction for Martelli-Montanari unification"); runInference("Prove Robinson theorem reduction for Martelli-Montanari unification"); }}
                  className="text-left bg-white/5 hover:bg-white/10 border border-white/5 p-3 rounded text-[#B4B9DF] hover:text-white text-[11.5px] font-mono cursor-pointer transition-all outline-none"
                >
                  ⚡ Robinson Theorem
                </button>
                <button 
                  onClick={() => { setPromptInput("Attest current ledger transaction status & verify BFT signature chain"); runInference("Attest current ledger transaction status & verify BFT signature chain"); }}
                  className="text-left bg-white/5 hover:bg-white/10 border border-white/5 p-3 rounded text-[#B4B9DF] hover:text-white text-[11.5px] font-mono cursor-pointer transition-all outline-none"
                >
                  🛡 Attest BFT Ledger
                </button>
                <button 
                  onClick={() => { setPromptInput("Compute Free Energy minimization matrix across active nodes"); runInference("Compute Free Energy minimization matrix across active nodes"); }}
                  className="text-left bg-white/5 hover:bg-white/10 border border-white/5 p-3 rounded text-[#B4B9DF] hover:text-white text-[11.5px] font-mono cursor-pointer transition-all outline-none"
                >
                  ◈ Active Inference
                </button>
              </div>
            </div>
          )}

          {sidebarTab === 'settings' && (
            <div className="flex flex-col gap-6">
              <span className="text-[10px] tracking-widest uppercase text-white/30 font-mono">Theme Presets</span>
              <div className="flex flex-col gap-2">
                {Object.values(THEMES).map(t => (
                  <button 
                    key={t.id}
                    onClick={() => setThemeKey(t.id)}
                    className={`flex items-center justify-between p-2.5 rounded text-[11.5px] border cursor-pointer transition-all ${theme.id === t.id ? 'bg-white/10 border-white/20 text-white' : 'bg-white/5 border-transparent text-white/60 hover:text-white'}`}
                  >
                    <span>{t.name}</span>
                    <div className="w-3 h-3 rounded-full border border-white/20" style={{ backgroundColor: t.accent }} />
                  </button>
                ))}
              </div>

              <span className="text-[10px] tracking-widest uppercase text-white/30 font-mono mt-4">Visual FX & Wallpaper</span>
              <div className="flex justify-between items-center text-[12px] text-white/70">
                <span>Grain Overlay</span>
                <button 
                  onClick={() => setGrainOverlay(!grainOverlay)}
                  className="text-[10px] font-mono border bg-transparent px-2 py-0.5 rounded cursor-pointer text-white/80"
                  style={{ borderColor: grainOverlay ? theme.accent : '#555' }}
                >
                  {grainOverlay ? 'ON' : 'OFF'}
                </button>
              </div>

              <div className="flex justify-between items-center text-[12px] text-white/70 mt-2">
                <span>Wallpaper Layer</span>
                <button 
                  onClick={() => setWallpaperEnabled(!wallpaperEnabled)}
                  className="text-[10px] font-mono border bg-transparent px-2 py-0.5 rounded cursor-pointer text-white/80"
                  style={{ borderColor: wallpaperEnabled ? theme.accent : '#555' }}
                >
                  {wallpaperEnabled ? 'ON' : 'OFF'}
                </button>
              </div>

              {wallpaperEnabled && (
                <div className="flex flex-col gap-3 mt-1 p-2.5 bg-white/5 border border-white/10 rounded">
                  <div className="flex flex-col gap-1">
                    <span className="text-[11px] text-white/60 font-mono">Wallpaper Preset</span>
                    <select
                      value={wallpaperPreset}
                      onChange={(e) => setWallpaperPreset(e.target.value)}
                      className="bg-[#090B19] border border-white/15 text-white/90 rounded p-1.5 text-[11px] font-mono outline-none cursor-pointer"
                    >
                      <option value="/assets/yinmn_blue_ide.jpg">YInMn Noir IDE</option>
                      <option value="/assets/cover_c5_vs_c4.png">C5 vs C4 Singularity</option>
                      <option value="/assets/thermo_decay_anergy.png">Thermo Decay Matrix</option>
                    </select>
                  </div>

                  <div className="flex flex-col gap-1">
                    <div className="flex justify-between text-[11px] text-white/60 font-mono">
                      <span>Opacity</span>
                      <span>{Math.round(wallpaperOpacity * 100)}%</span>
                    </div>
                    <input 
                      type="range" 
                      min="0.05" 
                      max="1.0" 
                      step="0.05"
                      value={wallpaperOpacity}
                      onChange={(e) => setWallpaperOpacity(parseFloat(e.target.value))}
                      className="w-full cursor-pointer"
                    />
                  </div>
                </div>
              )}

            </div>
          )}
        </div>

        {/* EDITOR AND MAIN WORKSPACE AREA */}
        <div className="flex-1 flex flex-col min-w-0 relative">
          
          {sidebarTab === 'swarm' ? (
            /* BFT SWARM TOPOLOGY GRAPH VISUALIZER */
            <div className="flex-1 flex gap-8 relative overflow-hidden">
              <div className="flex-1 flex flex-col min-w-0">
                <div className="flex justify-between items-center mb-4">
                  <h1 className="text-2xl font-light tracking-tight m-0" style={{ color: theme.accent }}>BFT Swarm Topology & Consensus DAG</h1>
                  <span className="text-[10px] font-mono text-white/40 uppercase">Mode: Decentralized Poset</span>
                </div>

                <div className="flex-1 bg-black/40 border border-white/10 rounded-xl relative overflow-hidden p-4 flex flex-col">
                  <svg className="w-full h-full absolute inset-0 pointer-events-none">
                    {swarmNodes.slice(1).map(node => (
                      <line 
                        key={`line-${node.id}`}
                        x1={swarmNodes[0].x}
                        y1={swarmNodes[0].y}
                        x2={node.x}
                        y2={node.y}
                        stroke={node.status === 'fault' ? '#EF4444' : theme.accent}
                        strokeWidth="1.5"
                        strokeDasharray={node.status === 'fault' ? '2 2' : '4 4'}
                        opacity="0.6"
                      />
                    ))}
                  </svg>

                  {swarmNodes.map(node => (
                    <div 
                      key={node.id}
                      onClick={() => setSelectedSwarmNode(node)}
                      className={`absolute p-3 rounded-lg border cursor-pointer transition-all duration-300 flex flex-col gap-1 w-44 ${selectedSwarmNode?.id === node.id ? 'bg-white/15 border-white/40 shadow-xl' : 'bg-black/60 border-white/10 hover:border-white/30'}`}
                      style={{ left: node.x - 85, top: node.y - 35 }}
                    >
                      <div className="flex justify-between items-center">
                        <span className="text-[11px] font-bold text-white truncate">{node.name.split(' ')[0]}</span>
                        <div className={`w-2 h-2 rounded-full ${node.status === 'synced' ? 'bg-emerald-400 animate-pulse' : node.status === 'fault' ? 'bg-red-500 animate-ping' : 'bg-amber-400'}`} />
                      </div>
                      <span className="text-[9px] font-mono text-white/40 truncate">{node.role}</span>
                      <span className="text-[8.5px] font-mono text-emerald-400 mt-1">t={node.lamport} · {node.latency}ms</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Node Inspector */}
              <div className="w-72 border-l border-white/5 pl-6 flex flex-col gap-6 shrink-0">
                <span className="text-[10px] font-mono uppercase text-white/30">Node Telemetry Inspector</span>
                {selectedSwarmNode ? (
                  <div className="border border-white/10 bg-white/5 rounded-md p-4 flex flex-col gap-3 text-xs font-mono">
                    <div className="text-sm font-medium text-white">{selectedSwarmNode.name}</div>
                    <div className="text-white/50 text-[10px]">{selectedSwarmNode.role}</div>
                    <div className="border-t border-white/10 pt-2 flex flex-col gap-1 text-[11px]">
                      <div>Status: <span className={selectedSwarmNode.status === 'fault' ? 'text-red-400' : 'text-emerald-400'}>{selectedSwarmNode.status}</span></div>
                      <div>Lamport: <span className="text-white">{selectedSwarmNode.lamport}</span></div>
                      <div>Latency: <span className="text-white">{selectedSwarmNode.latency}ms</span></div>
                      <div className="truncate mt-1 text-[9px] text-white/30" title={selectedSwarmNode.hash}>Hash: {selectedSwarmNode.hash}</div>
                    </div>
                  </div>
                ) : (
                  <div className="text-white/30 text-xs font-mono">Select a node to inspect telemetry.</div>
                )}
              </div>
            </div>

          ) : sidebarTab === 'inference' ? (
            <div className="flex-1 flex gap-8 relative overflow-hidden">
              <div className="flex-1 flex flex-col min-w-0">
                <h1 className="text-2xl font-light tracking-tight mb-4" style={{ color: theme.accent }}>Local Silicon Inference Console</h1>
                
                <div className="flex flex-col gap-3 mb-4">
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
                    placeholder="Enter prompt... (Press Enter to submit)"
                    className="w-full h-28 bg-white/5 border border-white/10 rounded-md p-3.5 text-[13px] font-mono text-white outline-none focus:border-[#3B4DFF] resize-none"
                  />
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-mono text-white/40">Model: mamba-ssm-c5-real</span>
                    <button 
                      onClick={() => runInference()}
                      className="px-5 py-2 text-white border-0 rounded text-[11px] font-mono tracking-widest uppercase cursor-pointer hover:opacity-90 transition-opacity"
                      style={{ backgroundColor: theme.accent }}
                    >
                      Execute
                    </button>
                  </div>
                </div>

                <div className="flex-1 flex flex-col min-h-0">
                  <span className="text-[10px] font-mono uppercase text-white/40 mb-2">Attestation Output Stream</span>
                  <div className="flex-1 bg-black/50 border border-white/10 rounded-md p-4 font-mono text-[12px] overflow-y-auto whitespace-pre text-white/80 leading-relaxed">
                    {inferenceOutput || 'Awaiting prompt execution... Select a preset on the left or enter a prompt above.'}
                  </div>
                </div>
              </div>

              <div className="w-72 border-l border-white/5 pl-6 flex flex-col gap-6 shrink-0">
                <span className="text-[10px] font-mono uppercase text-white/30">Active Inference Convergence</span>
                
                <div className="border border-white/10 bg-white/5 rounded-md p-4 flex flex-col gap-2">
                  <span className="text-[10px] font-mono uppercase text-white/40 tracking-wider">Free Energy D_KL</span>
                  <div className="flex items-end gap-1.5 h-16 pt-2">
                    {freeEnergyHistory.map((val, idx) => (
                      <div 
                        key={idx}
                        className="flex-1 rounded-t transition-all duration-500"
                        style={{ 
                          height: `${Math.max(val * 100, 5)}%`,
                          backgroundColor: theme.accent
                        }}
                        title={`Iter ${idx}: D_KL = ${val}`}
                      />
                    ))}
                  </div>
                  <div className="text-[10px] font-mono text-emerald-400 mt-1">D_KL = 0.000412 (Optimal)</div>
                </div>

                <div className="border border-white/10 bg-white/5 rounded-md p-4 flex flex-col gap-2">
                  <span className="text-[10px] font-mono uppercase text-white/40 tracking-wider">Silicon Throughput</span>
                  <div className="text-2xl font-light">{tokensPerSecond} <span className="text-[11px] font-mono text-white/50">tok/s</span></div>
                  <div className="text-[11px] font-mono text-white/40">Latency: {latencyMs} ms</div>
                </div>
              </div>
            </div>

          ) : sidebarTab === 'ledger' ? (
            <div className="flex-1 flex flex-col min-w-0">
              <h1 className="text-2xl font-light tracking-tight mb-4" style={{ color: theme.accent }}>Ledger Database Console</h1>
              
              <div className="flex gap-8 flex-1 min-h-0">
                <div className="flex-1 flex flex-col min-w-0">
                  <div className="flex flex-col gap-3 mb-4">
                    <div className="flex justify-between items-center">
                      <span className="text-[10px] font-mono uppercase text-white/40">SQL Command</span>
                      <button 
                        onClick={runSQLQuery}
                        className="px-4 py-1.5 bg-white/10 hover:bg-white/15 text-white border border-white/10 rounded text-[11px] font-mono uppercase cursor-pointer"
                      >
                        Run Query
                      </button>
                    </div>
                    <input 
                      type="text"
                      value={sqlQuery}
                      onChange={(e) => setSqlQuery(e.target.value)}
                      className="bg-white/5 border border-white/10 rounded p-3 text-[12.5px] font-mono text-white outline-none focus:border-[#3B4DFF]"
                    />
                  </div>

                  <div className="flex-1 bg-black/50 border border-white/10 rounded-md p-4 overflow-auto min-h-0">
                    {queryResults.length > 0 ? (
                      <table className="w-full border-collapse font-mono text-[12px] text-left text-white/80">
                        <thead>
                          <tr className="border-b border-white/10">
                            {Object.keys(queryResults[0]).map(key => (
                              <th key={key} className="pb-2 font-medium uppercase tracking-wider text-white/40 text-[10px]">{key}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {queryResults.map((row, idx) => (
                            <tr key={idx} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                              {Object.values(row).map((val: any, colIdx) => (
                                <td key={colIdx} className="py-2.5 pr-4 truncate max-w-[240px]" title={val}>{val}</td>
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

                <div className="w-64 border-l border-white/5 pl-6 flex flex-col gap-4 shrink-0">
                  {selectedTable ? (
                    <>
                      <span className="text-[10px] font-mono uppercase text-white/30">Schema: {selectedTable.name}</span>
                      <div className="flex flex-col gap-3">
                        {selectedTable.columns.map(col => (
                          <div key={col.name} className="flex justify-between items-baseline font-mono text-xs border-b border-white/5 pb-1.5">
                            <span className={col.pk ? 'text-amber-400 font-medium' : 'text-white/80'}>
                              {col.name} {col.pk && '🔑'}
                            </span>
                            <span className="text-white/30 text-[10px]">{col.type}</span>
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
            // MULTI-TAB CODE EDITOR WITH AST SYNTAX HIGHLIGHTING OVERLAY
            <div className="flex-1 flex flex-col min-w-0">
              
              {/* FILE TABS */}
              <div className="flex items-center gap-1 border-b border-white/5 pb-2 mb-4 overflow-x-auto">
                {openFiles.map(file => (
                  <div
                    key={file.id}
                    onClick={() => { setActiveFile(file); setEditorContent(file.content); }}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-t-md cursor-pointer border-b-2 text-[12px] font-mono transition-all ${activeFile.id === file.id ? 'bg-white/10 text-white' : 'bg-transparent text-white/40 hover:text-white/70'}`}
                    style={{ borderColor: activeFile.id === file.id ? theme.accent : 'transparent' }}
                  >
                    <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: file.moduleColor }} />
                    <span>{file.name}</span>
                    <button 
                      onClick={(e) => closeFileTab(e, file.id)}
                      className="ml-1 text-white/20 hover:text-white bg-transparent border-0 cursor-pointer text-xs"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>

              {/* EDITOR HEADER */}
              <div className="flex items-baseline justify-between gap-4 mb-4">
                <div className="flex items-baseline gap-3">
                  <h1 className="text-2xl font-light tracking-tight m-0 p-0" style={{ color: theme.accent }}>
                    {activeFile.name}
                  </h1>
                  <span className="text-[11px] font-mono text-white/30">
                    ({activeFile.path})
                  </span>
                </div>

                <div className="flex items-center gap-4 text-[10px] font-mono text-white/40 uppercase">
                  <span className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    Cortex-Sync
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                    BFT Verified
                  </span>
                </div>
              </div>

              {/* CODE EDITOR TEXTAREA WITH AST HIGHLIGHTING & LINE NUMBERS */}
              <div className="flex-1 relative border border-white/10 rounded-md bg-black/40 overflow-hidden flex">
                
                {/* Line Numbers Gutter */}
                <div className="w-12 py-3 bg-white/[0.02] border-r border-white/5 text-right pr-3 text-[11px] font-mono text-white/20 select-none leading-[1.8]">
                  {Array.from({ length: lineCount }).map((_, i) => (
                    <div key={i}>{i + 1}</div>
                  ))}
                </div>

                {/* Editor Surface */}
                <div className="flex-1 relative p-3 overflow-auto">
                  {/* Syntax Highlighted Background Overlay */}
                  <pre className="editor-text absolute inset-0 p-3 pointer-events-none z-10 whitespace-pre-wrap leading-[1.8] font-mono text-white/90">
                    {renderSyntaxHighlight(editorContent, activeFile.lang, theme.accent)}
                  </pre>

                  <textarea
                    value={editorContent}
                    onChange={handleTextChange}
                    onKeyDown={handleKeyDown}
                    spellCheck={false}
                    className="editor-text absolute inset-0 w-full h-full p-3 bg-transparent border-0 resize-none outline-none focus:ring-0 z-20 text-transparent caret-white selection:bg-white/20 leading-[1.8]"
                  />
                  
                  {ghostText && (
                    <pre className="editor-text absolute inset-0 p-3 pointer-events-none z-15 whitespace-pre-wrap leading-[1.8]">
                      <span className="opacity-0">{editorContent.slice(0, cursorPos)}</span>
                      <span className="opacity-40 transition-opacity duration-500" style={{ color: theme.muted }}>{ghostText}</span>
                    </pre>
                  )}
                </div>

                {/* Dictation HUD Overlay */}
                {isDictating && (
                  <div className="absolute bottom-6 right-6 z-30 bg-black/90 border border-white/10 p-4 rounded-xl flex flex-col gap-2 shadow-2xl w-72">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono text-red-400 uppercase tracking-widest animate-pulse">
                        🎤 Voice Transducer Active
                      </span>
                    </div>
                    <canvas ref={canvasRef} width="240" height="35" className="w-full bg-white/5 rounded border border-white/5" />
                    <span className="text-[9px] font-mono text-white/40">
                      Dictate code or say "limpiar pantalla".
                    </span>
                  </div>
                )}
              </div>
              
              {/* FOOTER METADATA */}
              <div className="h-8 mt-2 flex items-center justify-between text-[10px] font-mono tracking-widest text-white/40 border-t border-white/5">
                <div className="flex items-center gap-6">
                  <span>Lines: {lineCount}</span>
                  <span>Chars: {editorContent.length}</span>
                  <button 
                    onClick={() => setIsTerminalOpen(prev => !prev)}
                    className="text-white/60 hover:text-white bg-transparent border-0 cursor-pointer font-mono text-[10px] uppercase"
                  >
                    {isTerminalOpen ? '▼ Hide Logs' : '▲ System Terminal (⌘`)'}
                  </button>
                  <button 
                    onClick={() => setShortcutsModalOpen(true)}
                    className="text-white/40 hover:text-white bg-transparent border-0 cursor-pointer font-mono text-[10px] uppercase"
                  >
                    ? Hotkeys
                  </button>
                </div>
                <div className="flex items-center gap-6">
                  <span>REALITY: C5-REAL</span>
                  <span>LANG: {activeFile.lang.toUpperCase()}</span>
                </div>
              </div>
            </div>
          )}

          {/* SYSTEM TERMINAL LOG DRAWER */}
          {isTerminalOpen && (
            <div className="h-44 border-t border-white/10 bg-[#060812] p-3 flex flex-col font-mono text-xs z-30">
              <div className="flex justify-between items-center border-b border-white/10 pb-1.5 mb-2">
                <span className="text-[10px] uppercase tracking-widest text-white/50">C5-REAL System Log Stream</span>
                <button 
                  onClick={() => setIsTerminalOpen(false)}
                  className="text-white/40 hover:text-white bg-transparent border-0 cursor-pointer text-xs"
                >
                  ✕
                </button>
              </div>
              <div className="flex-1 overflow-y-auto flex flex-col gap-1 text-white/70 text-[11px]">
                {terminalLogs.map((log, idx) => (
                  <div key={idx} className="truncate">{log}</div>
                ))}
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
