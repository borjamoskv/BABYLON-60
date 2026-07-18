import { useState, useEffect, useRef } from 'react';

// Temas VS Code compatibles
interface Theme {
  id: string;
  name: string;
  bg: string;
  surface: string;
  border: string;
  accent: string;
  sidebar: string;
  editorBg: string;
  text: string;
  comment: string;
  keyword: string;
}

const THEMES: Record<string, Theme> = {
  noir: {
    id: 'noir',
    name: 'Industrial Noir 2026',
    bg: '#0A0A0A',
    surface: '#121212',
    border: '#222222',
    accent: '#2B3BE5',
    sidebar: '#0E0E0E',
    editorBg: '#080808',
    text: '#E0E0E0',
    comment: '#555555',
    keyword: '#2B3BE5',
  },
  dracula: {
    id: 'dracula',
    name: 'Dracula',
    bg: '#282a36',
    surface: '#1e1f29',
    border: '#44475a',
    accent: '#bd93f9',
    sidebar: '#191a21',
    editorBg: '#282a36',
    text: '#f8f8f2',
    comment: '#6272a4',
    keyword: '#ff79c6',
  },
  onedark: {
    id: 'onedark',
    name: 'One Dark Pro',
    bg: '#282c34',
    surface: '#21252b',
    border: '#181a1f',
    accent: '#61afef',
    sidebar: '#21252b',
    editorBg: '#282c34',
    text: '#abb2bf',
    comment: '#5c6370',
    keyword: '#c678dd',
  },
  monokai: {
    id: 'monokai',
    name: 'Monokai',
    bg: '#272822',
    surface: '#1e1f1c',
    border: '#3e3d32',
    accent: '#f92672',
    sidebar: '#1e1f1c',
    editorBg: '#272822',
    text: '#f8f8f2',
    comment: '#75715e',
    keyword: '#f92672',
  }
};

interface FileItem {
  name: string;
  path: string;
  lang: 'java' | 'python' | 'tsx' | 'css';
  content: string;
  prediction?: string;
  trigger?: string;
}

const PROJECT_FILES: FileItem[] = [
  {
    name: 'Kernel.java',
    path: 'src/main/java/com/babylon/Kernel.java',
    lang: 'java',
    content: `package com.babylon;

public class Kernel {
    private static final String VERSION = "V3.2";
    
    public void execute() {
        System.out.println("C5-REAL Kernel Active");
    }
}`,
    trigger: 'public',
    prediction: ' static void main(String[] args) {\n        new Kernel().execute();\n    }'
  },
  {
    name: 'ultrathink_audit_loop.py',
    path: 'scripts/ultrathink_audit_loop.py',
    lang: 'python',
    content: `import os
import hashlib
import sqlite3

class EpistemicHalt(Exception):
    pass

def phase_1_latent_friction(prompt):
    if "Espero" in prompt:
        raise EpistemicHalt("Anergía detectada (Φ2)")
    return prompt.strip()`,
    trigger: 'def',
    prediction: ' phase_2_phantom_target(target_path):\n    if not os.path.exists(target_path):\n        raise EpistemicHalt("Phantom Target (Ω27)")'
  },
  {
    name: 'App.tsx',
    path: 'src/App.tsx',
    lang: 'tsx',
    content: `import { useState } from 'react';

export default function App() {
  const [active, setActive] = useState(true);
  return (
    <div>Babylon-60 Active</div>
  );
}`,
    trigger: 'const',
    prediction: ' [theme, setTheme] = useState("noir");'
  },
  {
    name: 'yinmn_design_system.css',
    path: 'assets/yinmn_design_system.css',
    lang: 'css',
    content: `:root {
  --color-bg: #0a0a0a;
  --color-yinmn-blue: #2b3be5;
  --font-family-sans: "Humanist Sans";
}`,
    trigger: '--color',
    prediction: '-terminal-green: #00ff41;'
  }
];

const AUTOPROMPTER_PRESETS = [
  { command: 'mejoralo /goal', desc: 'Inicia optimización MCTS.', icon: '⚡' },
  { command: 'itera', desc: 'Avanza el estado del repositorio.', icon: '🔄' },
  { command: 'SIGKILL slop', desc: 'Purga la memoria con OBLITERATOR_OMEGA.', icon: '🩸' },
  { command: 'forjar /goal', desc: 'Activa la forja atómica del proyecto.', icon: '🛠️' },
  { command: 'BFT sync', desc: 'Sincroniza y valida consistencia en Swarm N>=3.', icon: '⚖️' }
];

interface LogEntry {
  timestamp: string;
  sender: string;
  message: string;
}

interface ExtensionItem {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
}

export default function BabylonPremiumIDE() {
  const [selectedTheme, setSelectedTheme] = useState<Theme>(THEMES.noir);
  const [fatigueReduction, setFatigueReduction] = useState(true);
  const [activeFile, setActiveFile] = useState<FileItem>(PROJECT_FILES[1]); // default to python script
  const [editorContent, setEditorContent] = useState(activeFile.content);
  const [ghostText, setGhostText] = useState('');
  const [cursorPos, setCursorPos] = useState(0);
  const [sidebarTab, setSidebarTab] = useState<'files' | 'chat' | 'ledger' | 'extensions' | 'portal'>('files');
  const [chatInput, setChatInput] = useState('');
  const [showAutopromptMenu, setShowAutopromptMenu] = useState(false);
  const [focusMode, setFocusMode] = useState(false);
  
  // Extension State
  const [extensions, setExtensions] = useState<ExtensionItem[]>([
    { id: 'mcts-auto', name: 'MCTS Autocomplete Pro', description: 'Inline ghost text helper.', enabled: true },
    { id: 'linter-c5', name: 'C5-REAL Linter', description: 'Checks for syntax and empty exception blocks.', enabled: true }
  ]);
  const [newExtensionName, setNewExtensionName] = useState('');
  const [newExtensionDesc, setNewExtensionDesc] = useState('');

  const [chatHistory, setChatHistory] = useState<LogEntry[]>([
    { timestamp: '07:15:22', sender: 'System', message: 'Legion initialized. Nodos Alpha, Beta y Obliterator en espera.' }
  ]);
  const [ledgerLogs, setLedgerLogs] = useState<string[]>([
    '[07:16:37] [Ledger] Transmisión exitosa. Commit: c885ab9a',
    '[07:15:22] [Cortex] Init TIER_0 Master Ledger. Hash: 42abc2b3'
  ]);
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const activeTheme = selectedTheme;

  // Actualizar contenido del editor al cambiar de archivo
  useEffect(() => {
    setEditorContent(activeFile.content);
    setGhostText('');
  }, [activeFile]);

  // Manejar el ghost text (predicciones en línea)
  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setEditorContent(val);
    const cursor = e.target.selectionStart;
    setCursorPos(cursor);

    // Detección del trigger para autocompletado en línea (solo si la extensión de autocomplete está habilitada)
    const autocompleteEnabled = extensions.find(ext => ext.id === 'mcts-auto')?.enabled;
    if (autocompleteEnabled && activeFile.trigger && activeFile.prediction) {
      const textBeforeCursor = val.slice(0, cursor);
      if (textBeforeCursor.endsWith(activeFile.trigger)) {
        setGhostText(activeFile.prediction);
      } else {
        setGhostText('');
      }
    } else {
      setGhostText('');
    }
  };

  // Tecla TAB para aceptar predicción fantasma
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab' && ghostText) {
      e.preventDefault();
      const textBefore = editorContent.slice(0, cursorPos);
      const textAfter = editorContent.slice(cursorPos);
      const newText = textBefore + ghostText + textAfter;
      setEditorContent(newText);
      setGhostText('');
      
      // Mover el cursor al final de la predicción insertada
      setTimeout(() => {
        if (textareaRef.current) {
          const newPos = cursorPos + ghostText.length;
          textareaRef.current.selectionStart = newPos;
          textareaRef.current.selectionEnd = newPos;
        }
      }, 10);
    }
  };

  const handleChatSend = () => {
    if (!chatInput.trim()) return;
    const time = new Date().toTimeString().slice(0, 8);
    const userMsg: LogEntry = { timestamp: time, sender: 'Operador', message: chatInput };
    setChatHistory(prev => [...prev, userMsg]);
    setChatInput('');

    // Respuesta del Auditor/Swarm en base a las 5 Fases
    setTimeout(() => {
      let response = '';
      if (chatInput.toLowerCase().includes('forge') || chatInput.toLowerCase().includes('crea')) {
        response = 'Consenso BFT en progreso. Nodo Alpha (Sintaxis): OK. Nodo Beta (Pruebas): OK. Mutación atómica validada.';
      } else if (chatInput.toLowerCase().includes('status')) {
        response = `Master Ledger: cortex.db (WAL). Exergía global: 91.2%. Zero Drift.`;
      } else {
        response = 'Directiva asimilada por el swarm. Evaluando fricción latente.';
      }
      setChatHistory(prev => [...prev, { timestamp: time, sender: 'Auditor_C5', message: response }]);
    }, 400);
  };

  const handlePurgeMemory = () => {
    const time = new Date().toTimeString().slice(0, 8);
    setChatHistory(prev => [...prev, { timestamp: time, sender: 'Obliterator', message: 'Purga TIER_1 completada. Weaponized Forgetting activo. +14,000 tokens purgados.' }]);
    setLedgerLogs(prev => [`[${time}] [Obliterator] Weaponized Forgetting finalizado.`, ...prev]);
  };

  const triggerPortalAction = async (route: string, label: string) => {
    const time = new Date().toTimeString().slice(0, 8);
    try {
      const res = await fetch(`http://localhost:6060${route}`, { method: 'POST' });
      const data = await res.json();
      if (data.status === 'ok') {
        setLedgerLogs(l => [`[${time}] [Portal] ${data.message}`, ...l]);
      } else {
        setLedgerLogs(l => [`[${time}] [Portal ERROR] ${data.message}`, ...l]);
      }
    } catch (e) {
      setLedgerLogs(l => [`[${time}] [Portal C4-SIM] ${label} ejecutado (Daemon offline).`, ...l]);
    }
  };

  const handleInstallExtension = () => {
    if (!newExtensionName.trim()) return;
    const time = new Date().toTimeString().slice(0, 8);
    const newId = `ext-${Date.now()}`;
    const newExt: ExtensionItem = {
      id: newId,
      name: newExtensionName,
      description: newExtensionDesc || 'Extensión instalada por el operador.',
      enabled: true
    };

    setExtensions(prev => [...prev, newExt]);
    setNewExtensionName('');
    setNewExtensionDesc('');

    setLedgerLogs(prev => [`[${time}] [Extensions] Extensión "${newExt.name}" registrada físicamente.`, ...prev]);
    setChatHistory(prev => [...prev, { timestamp: time, sender: 'System', message: `Extensión "${newExt.name}" instalada y activada con éxito.` }]);
  };

  const toggleExtension = (id: string) => {
    const time = new Date().toTimeString().slice(0, 8);
    setExtensions(prev => prev.map(ext => {
      if (ext.id === id) {
        const nextState = !ext.enabled;
        setLedgerLogs(l => [`[${time}] [Extensions] "${ext.name}" ${nextState ? 'Habilitada' : 'Deshabilitada'}.`, ...l]);
        return { ...ext, enabled: nextState };
      }
      return ext;
    }));
  };

  return (
    <main 
      className="w-screen h-screen flex flex-col justify-between overflow-hidden select-none border-2 transition-all duration-300"
      style={{
        backgroundColor: activeTheme.bg,
        color: activeTheme.text,
        borderColor: activeTheme.border,
        fontFamily: fatigueReduction ? '"Inter", sans-serif' : 'system-ui'
      }}
    >
      
      {/* Top Header - Compact Option bar */}
      <header 
        className="w-full px-6 py-3 border-b flex items-center justify-between transition-colors duration-300"
        style={{ backgroundColor: activeTheme.sidebar, borderColor: activeTheme.border }}
      >
        <div className="flex items-center gap-3">
          <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: activeTheme.accent }} />
          <span className="text-[10px] font-mono tracking-[0.25em] font-bold uppercase">
            BABYLON-60 IDE // SOBERANO
          </span>
          <span 
            className="text-[9px] font-mono tracking-widest px-2 py-0.5 border"
            style={{ borderColor: `${activeTheme.accent}40`, color: activeTheme.accent, backgroundColor: `${activeTheme.accent}10` }}
          >
            C5-REAL KERNEL
          </span>
        </div>

        {/* Dynamic Config Controls */}
        <div className="flex items-center gap-6">
          {/* Ergonomic Switch */}
          <button 
            onClick={() => setFatigueReduction(!fatigueReduction)}
            className="flex items-center gap-2 px-3 py-1 border font-mono text-[9px] tracking-wider uppercase bg-transparent transition-all duration-200 cursor-pointer"
            style={{ 
              borderColor: fatigueReduction ? activeTheme.accent : '#555',
              color: fatigueReduction ? activeTheme.accent : '#888'
            }}
          >
            👁️ FATIGA: {fatigueReduction ? 'REDUCIDA (CALIBRADO)' : 'OFF'}
          </button>

          {/* Theme Selector */}
          <div className="flex items-center gap-1.5 bg-[#000] p-1 border border-[#333]">
            {Object.values(THEMES).map(t => (
              <button
                key={t.id}
                onClick={() => setSelectedTheme(t)}
                title={t.name}
                className="w-3.5 h-3.5 border transition-all duration-150 cursor-pointer"
                style={{ 
                  backgroundColor: t.editorBg, 
                  borderColor: selectedTheme.id === t.id ? t.accent : 'transparent' 
                }}
              />
            ))}
          </div>
        </div>
      </header>

      {/* Main Core Layout: Compact Toolbar + Explorer + Editor + IA Sidebar */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Compact Vertical Toolbar (Iconos estilizados, sin toolbar pesada) */}
        <div 
          className="w-12 h-full border-r flex flex-col justify-between items-center py-4 z-10 transition-colors duration-300"
          style={{ backgroundColor: activeTheme.sidebar, borderColor: activeTheme.border }}
        >
          <div className="flex flex-col gap-5">
            <IconButton 
              icon="📂" 
              active={sidebarTab === 'files'} 
              onClick={() => setSidebarTab('files')} 
              accent={activeTheme.accent} 
              title="Explorador del Swarm" 
            />
            <IconButton 
              icon="🧩" 
              active={sidebarTab === 'extensions'} 
              onClick={() => setSidebarTab('extensions')} 
              accent={activeTheme.accent} 
              title="Extensiones VS Code" 
            />
            <IconButton 
              icon="💬" 
              active={sidebarTab === 'chat'} 
              onClick={() => setSidebarTab('chat')} 
              accent={activeTheme.accent} 
              title="IA Swarm Chat" 
            />
            <IconButton 
              icon="⚖️" 
              active={sidebarTab === 'ledger'} 
              onClick={() => setSidebarTab('ledger')} 
              accent={activeTheme.accent} 
              title="Master Ledger WAL" 
            />
            <IconButton 
              icon="🌀" 
              active={sidebarTab === 'portal'} 
              onClick={() => setSidebarTab('portal')} 
              accent={activeTheme.accent} 
              title="Portal de Aplicaciones" 
            />
          </div>
          
          <div className="flex flex-col gap-3">
            <IconButton 
              icon={focusMode ? "🎯" : "👁️"} 
              active={focusMode} 
              onClick={() => setFocusMode(!focusMode)} 
              accent={activeTheme.accent} 
              title="Modo Foco (Focus Mode)" 
            />
            <IconButton 
              icon="🩸" 
              active={false} 
              onClick={handlePurgeMemory} 
              accent={activeTheme.accent} 
              title="SIGKILL SLOP (Purga)" 
            />
          </div>
        </div>

        {/* Sidebar Panel Content */}
        {!focusMode && (
          <div 
            className="w-64 h-full border-r flex flex-col transition-all duration-300"
            style={{ backgroundColor: activeTheme.sidebar, borderColor: activeTheme.border }}
          >
            {sidebarTab === 'files' && (
            <div className="p-4 flex flex-col gap-4">
              <span className="text-[10px] font-mono tracking-widest text-white/40 uppercase">// PROYECTO</span>
              <div className="flex flex-col gap-2">
                {PROJECT_FILES.map(file => (
                  <button
                    key={file.name}
                    onClick={() => setActiveFile(file)}
                    className="flex items-center justify-between text-left px-3 py-2 text-xs font-mono tracking-wide rounded-sm transition-all duration-150 hover:bg-white/5 cursor-pointer"
                    style={{ 
                      color: activeFile.name === file.name ? activeTheme.accent : 'inherit',
                      backgroundColor: activeFile.name === file.name ? `${activeTheme.accent}15` : 'transparent'
                    }}
                  >
                    <span>📄 {file.name}</span>
                    <span className="text-[8px] opacity-30 uppercase">{file.lang}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {sidebarTab === 'extensions' && (
            <div className="p-4 flex flex-col gap-4 h-full justify-between">
              <div className="flex flex-col gap-4 overflow-y-auto">
                <span className="text-[10px] font-mono tracking-widest text-white/40 uppercase">// EXTENSIONES VS CODE</span>
                
                {/* Lista de extensiones */}
                <div className="flex flex-col gap-3">
                  {extensions.map(ext => (
                    <div key={ext.id} className="p-3 bg-white/5 border border-white/10 rounded-sm flex flex-col gap-1.5">
                      <div className="flex justify-between items-center">
                        <span className="text-xs font-mono font-bold">{ext.name}</span>
                        <button 
                          onClick={() => toggleExtension(ext.id)}
                          className="text-[8px] font-mono border px-1.5 py-0.5 hover:bg-white/10 cursor-pointer"
                          style={{ borderColor: ext.enabled ? activeTheme.accent : '#555', color: ext.enabled ? activeTheme.accent : '#888' }}
                        >
                          {ext.enabled ? 'DESACTIVAR' : 'ACTIVAR'}
                        </button>
                      </div>
                      <p className="text-[10px] text-white/50 leading-relaxed font-mono">{ext.description}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Formulario para añadir nuevas extensiones */}
              <div className="pt-4 border-t flex flex-col gap-2" style={{ borderColor: activeTheme.border }}>
                <span className="text-[9px] font-mono text-white/40 uppercase">Instalar Nueva Extensión:</span>
                <input
                  type="text"
                  value={newExtensionName}
                  onChange={(e) => setNewExtensionName(e.target.value)}
                  placeholder="Nombre de extensión..."
                  className="bg-black/40 border px-3 py-1.5 font-mono text-[10px] text-white focus:outline-none focus:border-[#2B3BE5]"
                  style={{ borderColor: activeTheme.border }}
                />
                <input
                  type="text"
                  value={newExtensionDesc}
                  onChange={(e) => setNewExtensionDesc(e.target.value)}
                  placeholder="Descripción..."
                  className="bg-black/40 border px-3 py-1.5 font-mono text-[10px] text-white focus:outline-none focus:border-[#2B3BE5]"
                  style={{ borderColor: activeTheme.border }}
                />
                <button 
                  onClick={handleInstallExtension}
                  className="py-2 text-white font-mono text-[10px] uppercase font-bold cursor-pointer transition-all duration-150"
                  style={{ backgroundColor: activeTheme.accent }}
                >
                  🧩 Instalar
                </button>
              </div>
            </div>
          )}

          {sidebarTab === 'chat' && (
            <div className="flex flex-col h-full justify-between">
              <div className="p-4 border-b flex justify-between items-center" style={{ borderColor: activeTheme.border }}>
                <span className="text-[10px] font-mono tracking-widest text-white/40 uppercase">// CHAT IA INVISIBLE</span>
                <button 
                  onClick={handlePurgeMemory} 
                  className="text-[8px] font-mono tracking-wide border px-1.5 py-0.5 hover:bg-white/5 cursor-pointer"
                  style={{ borderColor: activeTheme.border }}
                >
                  PURGAR
                </button>
              </div>
              
              {/* Chat Log history */}
              <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-3 font-mono text-[11px] leading-relaxed">
                {chatHistory.map((msg, i) => (
                  <div key={i} className="flex flex-col gap-1">
                    <div className="flex justify-between opacity-30 text-[9px]">
                      <span>{msg.sender}</span>
                      <span>{msg.timestamp}</span>
                    </div>
                    <div className="text-white/80">{msg.message}</div>
                  </div>
                ))}
              </div>

              {/* Chat Input */}
              <div className="p-3 border-t flex gap-2 relative" style={{ borderColor: activeTheme.border }}>
                {showAutopromptMenu && (
                  <div 
                    className="absolute bottom-14 left-3 right-3 bg-[#0A0A0A] border p-3 flex flex-col gap-2 z-50 font-mono text-[10px] shadow-[0_0_30px_rgba(43,59,229,0.25)] rounded-sm"
                    style={{ borderColor: activeTheme.accent }}
                  >
                    <div className="text-white/40 border-b border-white/10 pb-1.5 uppercase tracking-widest text-[8px] flex justify-between font-bold">
                      <span>// AUTOPROMPTER SELECT</span>
                      <button onClick={() => setShowAutopromptMenu(false)} className="text-[#ff5500] cursor-pointer bg-transparent border-0 hover:text-[#ff3300]">✕</button>
                    </div>
                    <div className="flex flex-col gap-1.5 max-h-48 overflow-y-auto">
                      {AUTOPROMPTER_PRESETS.map(preset => (
                        <button
                          key={preset.command}
                          onClick={() => {
                            setChatInput(preset.command);
                            setShowAutopromptMenu(false);
                            setChatHistory(prev => [...prev, { timestamp: new Date().toTimeString().slice(0, 8), sender: 'System', message: `Autoprompt insertado: "${preset.command}"` }]);
                          }}
                          className="text-left px-2 py-1.5 hover:bg-white/5 text-white/80 rounded-sm cursor-pointer border-0 bg-transparent flex flex-col gap-0.5 transition-colors duration-150"
                        >
                          <span className="font-bold text-white flex items-center gap-1">
                            {preset.icon} {preset.command}
                          </span>
                          <span className="text-[8px] text-white/40 leading-normal">{preset.desc}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleChatSend()}
                  onClick={(e) => {
                    if (e.detail === 3) {
                      setShowAutopromptMenu(true);
                      setChatHistory(prev => [...prev, { timestamp: new Date().toTimeString().slice(0, 8), sender: 'System', message: 'Modo AUTOPROMPTER activado vía triple click.' }]);
                    }
                  }}
                  placeholder="Inyectar Ψ... [Triple click para Autoprompt]"
                  className="flex-1 bg-black/40 border px-3 py-2 font-mono text-[10px] text-white focus:outline-none transition-all duration-300 placeholder:text-white/20"
                  style={{ borderColor: activeTheme.border }}
                />
                <button 
                  onClick={handleChatSend}
                  className="px-3 py-2 text-white font-mono text-[10px] cursor-pointer"
                  style={{ backgroundColor: activeTheme.accent }}
                >
                  →
                </button>
              </div>
            </div>
          )}

          {sidebarTab === 'ledger' && (
            <div className="p-4 flex flex-col gap-4">
              <span className="text-[10px] font-mono tracking-widest text-white/40 uppercase">// MASTER LEDGER (WAL)</span>
              <div className="flex flex-col gap-3 font-mono text-[10px] text-white/60 leading-normal">
                {ledgerLogs.map((log, i) => (
                  <div key={i} className="p-2 border-l border-white/20 bg-white/5">
                    {log}
                  </div>
                ))}
              </div>
            </div>
          )}

          {sidebarTab === 'portal' && (
            <div className="p-4 flex flex-col gap-4 h-full justify-between">
              <div className="flex flex-col gap-4">
                <span className="text-[10px] font-mono tracking-widest text-white/40 uppercase">// PORTAL.APP SHORTCUTS</span>
                <div className="flex flex-col gap-3">
                  <div className="p-3 bg-white/5 border border-white/10 rounded-sm flex flex-col gap-1.5 font-mono text-[10px]">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-white">🌐 Brave Browser</span>
                      <button 
                        onClick={() => triggerPortalAction('/launch-brave', 'Brave Browser')}
                        className="text-[8px] border px-1.5 py-0.5 hover:bg-white/10 cursor-pointer text-white bg-transparent border-0 outline-none"
                        style={{ borderColor: activeTheme.accent }}
                      >
                        LAUNCH
                      </button>
                    </div>
                    <span className="text-white/40">Foco: OSINT / Scraper Web local.</span>
                  </div>

                  <div className="p-3 bg-white/5 border border-white/10 rounded-sm flex flex-col gap-1.5 font-mono text-[10px]">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-white">💿 Teorema-Robinson-Moskv DMG</span>
                      <button 
                        onClick={() => triggerPortalAction('/mount-dmg', 'Montar DMG')}
                        className="text-[8px] border px-1.5 py-0.5 hover:bg-white/10 cursor-pointer text-white bg-transparent border-0 outline-none"
                        style={{ borderColor: activeTheme.accent }}
                      >
                        MOUNT
                      </button>
                    </div>
                    <span className="text-white/40">Origen: Teorema-Robinson-Moskv.dmg</span>
                  </div>

                  <div className="p-3 bg-white/5 border border-white/10 rounded-sm flex flex-col gap-1.5 font-mono text-[10px]">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-white">⚙️ Ollama local</span>
                      <button 
                        onClick={() => triggerPortalAction('/restart-ollama', 'Ollama local')}
                        className="text-[8px] border px-1.5 py-0.5 hover:bg-white/10 cursor-pointer text-white bg-transparent border-0 outline-none"
                        style={{ borderColor: activeTheme.accent }}
                      >
                        RESTART
                      </button>
                    </div>
                    <span className="text-white/40">Host: http://localhost:11434</span>
                  </div>
                </div>
              </div>
            </div>
          )}
          </div>
        )}

        {/* Code Editor and Prediction Workspace */}
        <div className="flex-1 flex flex-col" style={{ backgroundColor: activeTheme.editorBg }}>
          {/* File path tab */}
          <div className="px-6 py-2 border-b flex justify-between items-center text-[10px] font-mono text-white/30" style={{ borderColor: activeTheme.border }}>
            <span>{activeFile.path}</span>
            <span>UTF-8 // {activeFile.lang.toUpperCase()}</span>
          </div>

          {/* Interactive Text Area with Ghost Text */}
          <div className="flex-1 relative p-6">
            <textarea
              ref={textareaRef}
              value={editorContent}
              onChange={handleTextChange}
              onKeyDown={handleKeyDown}
              spellCheck={false}
              className="absolute inset-0 w-full h-full p-6 bg-transparent border-0 resize-none outline-none font-mono text-xs focus:ring-0 focus:outline-none whitespace-pre"
              style={{
                color: activeTheme.text,
                fontSize: fatigueReduction ? '14px' : '12px',
                lineHeight: fatigueReduction ? '1.85' : '1.5',
                letterSpacing: fatigueReduction ? '0.05em' : 'normal',
              }}
            />
            {/* Transparent prediction layer (Ghost Text) */}
            {ghostText && (
              <pre 
                className="absolute pointer-events-none p-6 font-mono text-xs whitespace-pre"
                style={{
                  color: activeTheme.comment,
                  fontSize: fatigueReduction ? '14px' : '12px',
                  lineHeight: fatigueReduction ? '1.85' : '1.5',
                  letterSpacing: fatigueReduction ? '0.05em' : 'normal',
                }}
              >
                {/* Repetimos el texto antes de la predicción y metemos la sugerencia translúcida */}
                <span>{editorContent.slice(0, cursorPos)}</span>
                <span className="opacity-40" style={{ color: activeTheme.accent }}>{ghostText}</span>
                <span>{editorContent.slice(cursorPos)}</span>
              </pre>
            )}
          </div>

          {/* Inline notification of prediction availability */}
          {ghostText && (
            <div 
              className="px-6 py-2 border-t text-[9px] font-mono animate-pulse flex justify-between"
              style={{ borderColor: activeTheme.border, color: activeTheme.accent }}
            >
              <span>⚡ PREDICCIÓN DISPONIBLE. PRESIONA [TAB] PARA INJECTAR AL AST</span>
              <span>COMPATIBILIDAD VSCODE ACTIVA</span>
            </div>
          )}
        </div>
      </div>

      {/* Footer / Status bar */}
      <footer 
        className="w-full px-6 py-3 border-t flex items-center justify-between text-[9px] font-mono text-white/30 tracking-widest uppercase transition-colors duration-300"
        style={{ backgroundColor: activeTheme.sidebar, borderColor: activeTheme.border }}
      >
        <div>THEME: {activeTheme.name}</div>
        <div>SPACING: {fatigueReduction ? 'CALIBRADO (ANTI-FATIGA)' : 'ESTÁNDAR'}</div>
        <div>CORTEX BFT SYNC: PASS</div>
      </footer>
    </main>
  );
}

// Icon Button Component
function IconButton({ 
  icon, 
  active, 
  onClick, 
  accent, 
  title 
}: { 
  icon: string; 
  active: boolean; 
  onClick: () => void; 
  accent: string;
  title?: string;
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      className="w-8 h-8 rounded flex items-center justify-center transition-all duration-150 cursor-pointer"
      style={{
        backgroundColor: active ? `${accent}15` : 'transparent',
        border: active ? `1px solid ${accent}40` : '1px solid transparent',
        color: active ? accent : '#888'
      }}
    >
      <span className="text-sm">{icon}</span>
    </button>
  );
}
