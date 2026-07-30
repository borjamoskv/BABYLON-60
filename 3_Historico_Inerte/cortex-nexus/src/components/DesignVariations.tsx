import React, { useState } from 'react';
import { useTheme } from '../hooks/useTheme';
import { Settings2, X } from 'lucide-react'; // Assume lucide-react is installed, if not we will install it

const themes = [
  { id: 'noir', name: 'Industrial Noir', color: '#0a0a0a', border: '#333' },
  { id: 'calm', name: 'Soft Calm', color: '#faf8f5', border: '#e6e2db' },
  { id: 'brutal', name: 'Cyber Brutal', color: '#fff', border: '#000' },
  { id: 'glass', name: 'Glassmorphism', color: '#3a1c71', border: '#d76d77' }
] as const;

export default function DesignVariations() {
  const { theme, setTheme } = useTheme();
  const [isOpen, setIsOpen] = useState(false);

  if (!isOpen) {
    return (
      <button 
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 p-4 rounded-full bg-primary text-primary-foreground shadow-lg hover:scale-105 transition-transform"
        title="Design Variations"
      >
        <Settings2 size={24} />
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 w-80 bg-card border border-border shadow-2xl rounded-[var(--radius)] overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-border bg-muted/30">
        <h3 className="font-heading font-bold text-sm tracking-tight text-foreground flex items-center gap-2">
          <Settings2 size={16} />
          Design Variations
        </h3>
        <button 
          onClick={() => setIsOpen(false)}
          className="text-muted-foreground hover:text-foreground transition-colors"
        >
          <X size={16} />
        </button>
      </div>
      
      <div className="p-4 grid grid-cols-2 gap-3">
        {themes.map((t) => (
          <button
            key={t.id}
            onClick={() => setTheme(t.id)}
            className={`
              relative flex flex-col items-center justify-center p-3 gap-2 rounded-md border-2 transition-all
              ${theme === t.id ? 'border-primary bg-primary/10' : 'border-border bg-background hover:border-primary/50'}
            `}
          >
            <div 
              className="w-12 h-12 rounded-full border shadow-sm"
              style={{ backgroundColor: t.color, borderColor: t.border }}
            />
            <span className="text-xs font-semibold text-foreground">
              {t.name}
            </span>
            {theme === t.id && (
              <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-primary" />
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
