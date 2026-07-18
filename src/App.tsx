import { useState, useEffect, useRef } from 'react';

// SOTA Minimalist Awwwards Theme
interface Theme {
  id: string;
  name: string;
  bg: string;
  surface: string;
  border: string;
  accent: string;
  text: string;
  muted: string;
}

const THEMES: Record<string, Theme> = {
  awwwards: {
    id: 'awwwards',
    name: 'Void Minimalist',
    bg: '#000000',
    surface: '#030303',
    border: 'rgba(255, 255, 255, 0.03)',
    accent: '#FFFFFF',
    text: '#EAEAEA',
    muted: '#4A4A4A',
  },
  geist: {
    id: 'geist',
    name: 'Geist Monolith',
    bg: '#FAFAFA',
    surface: '#FFFFFF',
    border: 'rgba(0, 0, 0, 0.04)',
    accent: '#000000',
    text: '#111111',
    muted: '#A0A0A0',
  }
};

interface FileItem {
  name: string;
  path: string;
  lang: string;
  content: string;
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

const PROJECT_FILES: FileItem[] = [
  {
    name: 'active_inference.py',
    path: 'cortex/active_inference.py',
    lang: 'python',
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
    content: `% TEOREMA DE ROBINSON - C5-REAL
% Unificación Martelli-Montanari

unify(X, Y) :- X == Y, !.
unify(X, Y) :- var(X), !, occurs_check(X, Y), X = Y.
unify(X, Y) :- var(Y), !, occurs_check(Y, X), Y = X.
`,
    trigger: 'unify',
    prediction: '(f(A), f(B)) :- unify(A, B).'
  }
];

const PREDEFINED_SKILLS: SkillItem[] = [
  { id: 'S1', name: 'DOM_CSS_Transducer', type: 'Visual', exergy: 'Max', desc: 'Awwwards UI Engine', status: 'active' },
  { id: 'S2', name: 'MCTS_Budget_Forcer', type: 'Logic', exergy: 'Ultra', desc: 'Thermodynamic bounds', status: 'idle' },
  { id: 'S3', name: 'Swarm_Dispatcher', type: 'Orchestrator', exergy: 'High', desc: 'BFT parallelization', status: 'active' },
  { id: 'S4', name: 'OBLITERATOR', type: 'Destructive', exergy: 'Max', desc: 'Entropy vector purge', status: 'locked' }
];

export default function BabylonMinimalistIDE() {
  const [theme, setTheme] = useState<Theme>(THEMES.awwwards);
  const [activeFile, setActiveFile] = useState<FileItem>(PROJECT_FILES[0]);
  const [editorContent, setEditorContent] = useState(activeFile.content);
  const [ghostText, setGhostText] = useState('');
  const [cursorPos, setCursorPos] = useState(0);
  const [sidebarTab, setSidebarTab] = useState<'architecture' | 'swarm' | 'ledger' | 'settings'>('architecture');
  const [isLoaded, setIsLoaded] = useState(false);
  const [activeSkillId, setActiveSkillId] = useState<string | null>(null);

  // Dictation State
  const [isDictating, setIsDictating] = useState(false);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    setIsLoaded(true);
    return () => {
      if (recognitionRef.current) recognitionRef.current.stop();
    };
  }, []);

  useEffect(() => {
    setEditorContent(activeFile.content);
    setGhostText('');
  }, [activeFile]);

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
        if (text) setEditorContent(prev => prev + (prev.endsWith('\\n') ? '' : ' ') + text.trim() + '\\n');
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

  const isDark = theme.id === 'awwwards';

  return (
    <div 
      className={\`w-screen h-screen flex flex-col overflow-hidden select-none transition-all duration-[1200ms] ease-out \${isLoaded ? 'opacity-100' : 'opacity-0 scale-[0.98]'}\`}
      style={{ backgroundColor: theme.bg, color: theme.text, fontFamily: '"Inter", "Helvetica Neue", sans-serif' }}
    >
      <style>{\`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500&family=JetBrains+Mono:wght@300;400&display=swap');
        
        * { box-sizing: border-box; }
        
        ::-webkit-scrollbar { width: 2px; height: 2px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: \${theme.muted}; opacity: 0.2; }
        
        .grain {
          position: absolute;
          top: -150%; left: -50%; right: -50%; bottom: -150%;
          width: 200%; height: 400vh;
          background: transparent url('data:image/svg+xml;utf8,%3Csvg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"%3E%3Cfilter id="noiseFilter"%3E%3CfeTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" stitchTiles="stitch"/%3E%3C/filter%3E%3Crect width="100%25" height="100%25" filter="url(%23noiseFilter)"/%3E%3C/svg%3E');
          opacity: \${isDark ? 0.04 : 0.015};
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
          color: \${theme.muted};
          transition: color 0.4s ease;
        }
        .nav-link:hover, .nav-link.active {
          color: \${theme.accent};
        }
        .nav-link::after {
          content: '';
          position: absolute;
          bottom: -4px;
          left: 0;
          width: 100%;
          height: 1px;
          background: \${theme.accent};
          transform: scaleX(0);
          transform-origin: right;
          transition: transform 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
        }
        .nav-link:hover::after, .nav-link.active::after {
          transform: scaleX(1);
          transform-origin: left;
        }
      \`}</style>

      <div className="grain" />

      {/* ULTRA MINIMAL HEADER */}
      <header 
        className="h-16 flex items-center justify-between px-10 z-40"
        style={{ WebkitAppRegion: 'drag' } as any}
      >
        <div className="flex items-center gap-12">
          <span className="text-[10px] font-medium tracking-[0.2em] uppercase" style={{ color: theme.accent }}>
            Babylon_60
          </span>
          
          <nav className="flex gap-8 text-[11px] font-medium tracking-wide uppercase" style={{ WebkitAppRegion: 'no-drag' } as any}>
            <button className={\`nav-link \${sidebarTab === 'architecture' ? 'active' : ''} outline-none\`\} onClick={() => setSidebarTab('architecture')}>Architecture</button>
            <button className={\`nav-link \${sidebarTab === 'swarm' ? 'active' : ''} outline-none\`\} onClick={() => setSidebarTab('swarm')}>Swarm</button>
            <button className={\`nav-link \${sidebarTab === 'ledger' ? 'active' : ''} outline-none\`\} onClick={() => setSidebarTab('ledger')}>Ledger</button>
            <button className={\`nav-link \${sidebarTab === 'settings' ? 'active' : ''} outline-none\`\} onClick={() => setSidebarTab('settings')}>Settings</button>
          </nav>
        </div>
        
        <div className="flex items-center gap-6" style={{ WebkitAppRegion: 'no-drag' } as any}>
          <button
            onClick={toggleDictation}
            className="text-[10px] uppercase tracking-widest font-medium outline-none transition-all duration-300"
            style={{ color: isDictating ? '#FF3333' : theme.muted }}
          >
            {isDictating ? 'Recording' : 'Dictation'}
          </button>
          
          {/* Subtle Theme Toggle */}
          <button 
            onClick={() => setTheme(isDark ? THEMES.geist : THEMES.awwwards)}
            className="w-3 h-3 rounded-full border transition-all duration-500 outline-none"
            style={{ 
              borderColor: theme.accent, 
              backgroundColor: isDark ? 'transparent' : theme.accent 
            }}
          />
        </div>
      </header>

      {/* MAIN CONTENT AREA - PURE TYPOGRAPHY & SPACING */}
      <div className="flex-1 flex overflow-hidden px-10 pb-10 gap-16 relative z-10">
        
        {/* LISTINGS / SECONDARY NAV */}
        <div className="w-64 flex flex-col pt-12">
          {sidebarTab === 'architecture' && (
            <div className="flex flex-col gap-6">
              {PROJECT_FILES.map(file => (
                <div 
                  key={file.name}
                  onClick={() => setActiveFile(file)}
                  className="flex flex-col cursor-pointer group"
                >
                  <span 
                    className="text-[13px] font-medium transition-all duration-500"
                    style={{ 
                      color: activeFile.name === file.name ? theme.accent : theme.muted,
                      transform: activeFile.name === file.name ? 'translateX(4px)' : 'none'
                    }}
                  >
                    {file.name}
                  </span>
                  <span 
                    className="text-[10px] font-mono mt-1 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                    style={{ color: theme.muted }}
                  >
                    {file.path}
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
                        border: \`1px solid \${theme.muted}\`,
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
                    className="overflow-hidden transition-all duration-500 pl-4.5 flex flex-col gap-1"
                    style={{ 
                      maxHeight: activeSkillId === skill.id ? '100px' : '0',
                      opacity: activeSkillId === skill.id ? 1 : 0,
                      marginTop: activeSkillId === skill.id ? '8px' : '0'
                    }}
                  >
                    <span className="text-[10px] uppercase tracking-widest" style={{ color: theme.muted }}>{skill.type} · {skill.exergy}</span>
                    <span className="text-[11px] leading-relaxed" style={{ color: theme.muted }}>{skill.desc}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {sidebarTab === 'settings' && (
            <div className="flex flex-col gap-10">
              <div className="flex flex-col gap-6">
                <span className="text-[10px] tracking-widest uppercase" style={{ color: theme.muted }}>Preferences</span>
                <div className="flex justify-between items-center cursor-pointer group">
                  <span className="text-[12px] transition-colors" style={{ color: theme.accent }}>Typography Engine</span>
                  <span className="text-[10px] font-mono" style={{ color: theme.muted }}>Inter / JetBrains</span>
                </div>
                <div className="flex justify-between items-center cursor-pointer group" onClick={toggleDictation}>
                  <span className="text-[12px] transition-colors" style={{ color: theme.accent }}>Voice Dictation Mode</span>
                  <span className="text-[10px] font-mono" style={{ color: isDictating ? '#FF3333' : theme.muted }}>{isDictating ? 'ACTIVE' : 'OFF'}</span>
                </div>
                <div className="flex justify-between items-center cursor-pointer group">
                  <span className="text-[12px] transition-colors" style={{ color: theme.accent }}>BFT Consensus Strict</span>
                  <span className="text-[10px] font-mono" style={{ color: theme.muted }}>ON</span>
                </div>
              </div>
              
              <div className="flex flex-col gap-5">
                <span className="text-[10px] tracking-widest uppercase" style={{ color: theme.muted }}>Languages</span>
                <div className="flex gap-6 text-[11px] font-mono">
                  <span className="cursor-pointer border-b pb-1" style={{ color: theme.accent, borderColor: theme.accent }}>ES-ES</span>
                  <span className="cursor-pointer pb-1 transition-colors hover:text-white" style={{ color: theme.muted }}>EN-US</span>
                  <span className="cursor-pointer pb-1 transition-colors hover:text-white" style={{ color: theme.muted }}>JA-JP</span>
                  <span className="cursor-pointer pb-1 transition-colors hover:text-white" style={{ color: theme.muted }}>RU-RU</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* EDITOR AREA - MASSIVE NEGATIVE SPACE */}
        <div className="flex-1 flex flex-col relative pt-12">
          
          <div className="flex items-baseline gap-4 mb-12">
            <h1 className="text-4xl font-light tracking-tight m-0 p-0" style={{ color: theme.accent }}>
              {activeFile.name.split('.')[0]}
            </h1>
            <span className="text-[12px] font-mono tracking-widest" style={{ color: theme.muted }}>
              .{activeFile.name.split('.')[1]}
            </span>
          </div>

          <div className="flex-1 relative">
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
        </div>
      </div>
    </div>
  );
}
