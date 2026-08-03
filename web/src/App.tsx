import { useEffect, useState } from 'react'
import { Canvas } from './ui/Canvas'
import { mountProject } from './io/fs-access'
import { checkCortexStatus } from './cortex/lm-bridge'

function App() {
  const [cortexOnline, setCortexOnline] = useState(false);
  const [fsMounted, setFsMounted] = useState(false);

  useEffect(() => {
    // Check Cortex (LM Studio) status on load
    checkCortexStatus().then(setCortexOnline);
    
    // Keyboard shortcut for mounting FS
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.metaKey && e.key === 'o') {
        e.preventDefault();
        mountProject().then(handle => {
          if (handle) setFsMounted(true);
        });
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="flex flex-col h-screen w-screen bg-[#0a0a0a] overflow-hidden">
      {/* Main Canvas - ADHD Mode */}
      <div className="flex-1">
        <Canvas />
      </div>

      {/* Subtle Status Bar */}
      <div className="h-6 bg-[#0f0f0f] border-t border-[#1a1a1a] flex items-center justify-between px-4 text-xs font-mono text-slate-500">
        <div className="flex gap-4">
          <span>BABYLON-60</span>
          <span className={fsMounted ? 'text-green-500' : ''}>
            FS {fsMounted ? '●' : '○'}
          </span>
          <span className={cortexOnline ? 'text-amber-500' : ''}>
            CORTEX {cortexOnline ? '●' : '○'}
          </span>
        </div>
        <div>
          <span>WASM ●</span>
        </div>
      </div>
    </div>
  )
}

export default App
