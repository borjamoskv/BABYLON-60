import { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { streamCompletion, type Message } from '../cortex/lm-bridge';

export function Canvas() {
  const [code, setCode] = useState('// BABYLON-60 Causal Engine\n// Press Cmd+O to mount project...\n// Press Cmd+L to ping Cortex via LM Studio...');
  
  useEffect(() => {
    const handleKeyDown = async (e: KeyboardEvent) => {
      if (e.metaKey && e.key === 'l') {
        e.preventDefault();
        
        const messages: Message[] = [
          { role: 'system', content: 'You are the local Causal Motor. Keep it very brief.' },
          { role: 'user', content: 'Ping! Test the connection. Say something like: "Pong from 14B model."' }
        ];

        setCode(prev => prev + '\n\n// [CORTEX]: ');
        
        await streamCompletion(messages, undefined, (token) => {
          setCode(prev => prev + token);
        });
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="w-full h-full bg-[#0a0a0a] text-slate-200">
      <Editor
        height="100vh"
        defaultLanguage="python"
        theme="vs-dark"
        value={code}
        onChange={(val: string | undefined) => setCode(val || '')}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          fontFamily: "'JetBrains Mono', monospace",
          lineNumbers: 'on',
          scrollBeyondLastLine: false,
          wordWrap: 'on',
          padding: { top: 24 },
          renderLineHighlight: 'none',
          hideCursorInOverviewRuler: true,
          overviewRulerBorder: false,
          scrollbar: { vertical: 'hidden', horizontal: 'hidden' }
        }}
      />
    </div>
  );
}
