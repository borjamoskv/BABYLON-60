import { useState } from 'react';
import { invoke } from '@tauri-apps/api/tauri';

// Atomic Dispatcher for the frontend
const dispatch = (d: number, p: number, m: number, t: number) => {
  invoke('dispatch', { d, p, m, t }).catch(console.error);
};

const DOMAINS = ["SOURCE", "MATRIX", "PULSE", "KINETIC", "LOGIC", "VECTOR", "STORAGE", "OSINT", "CLOCK", "COMPILER"];
const PRIMITIVES = ["INIT", "MUTATE", "BIND", "QUERY", "STREAM", "COMMIT", "SYNC", "HALT", "FORK", "JOIN"];
const MODIFIERS = ["RAW", "ATOMIC", "PERSIST", "EPHEMERAL", "ASYNC", "SYNC", "QUANTIZED", "MAPPED", "WRAPPED", "LOCKED"];
const TARGETS = ["LOCAL", "NETWORK", "SWARM", "LEDGER", "MEMORY", "DISPATCH", "UI", "SYSTEM", "BFT", "CORE"];

export default function AntigravityKernelUI() {
  const [domain, setDomain] = useState(0);
  const [primitive, setPrimitive] = useState(0);
  const [modifier, setModifier] = useState(0);
  const [target, setTarget] = useState(0);

  const code = (domain * 1000) + (primitive * 100) + (modifier * 10) + target;
  const name = `${DOMAINS[domain]}-${PRIMITIVES[primitive]}-${MODIFIERS[modifier]}-${TARGETS[target]}`;

  return (
    <main className="w-screen h-screen bg-[#0A0A0A] text-white flex flex-col items-center justify-center font-sans overflow-hidden">
      <div className="absolute top-8 left-8 text-[10px] tracking-widest text-[#2B3BE5] uppercase">
        MOSKV-1 APEX SINGULARITY // LEGION 10K MATRIX
      </div>
      
      <div className="flex gap-12 mb-16">
        <Column title="DOMAIN" items={DOMAINS} selected={domain} onSelect={setDomain} />
        <Column title="PRIMITIVE" items={PRIMITIVES} selected={primitive} onSelect={setPrimitive} />
        <Column title="MODIFIER" items={MODIFIERS} selected={modifier} onSelect={setModifier} />
        <Column title="TARGET" items={TARGETS} selected={target} onSelect={setTarget} />
      </div>

      <div className="flex flex-col items-center gap-6">
        <div className="text-4xl font-light tracking-[0.2em]">{name}</div>
        <div className="text-sm text-white/50 font-mono">CODE: {code.toString().padStart(4, '0')}</div>
        
        <button 
          className="mt-8 px-12 py-4 border border-[#2B3BE5] text-[#2B3BE5] hover:bg-[#2B3BE5] hover:text-white transition-all duration-300 tracking-widest text-sm uppercase cursor-pointer"
          onClick={() => dispatch(domain, primitive, modifier, target)}
        >
          TRANSDUCE
        </button>
      </div>
    </main>
  );
}

function Column({ title, items, selected, onSelect }: { title: string, items: string[], selected: number, onSelect: (i: number) => void }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="text-xs text-white/30 tracking-widest mb-4 border-b border-white/10 pb-2">{title}</div>
      {items.map((item, i) => (
        <div 
          key={item}
          onClick={() => onSelect(i)}
          className={`text-xs tracking-wider cursor-pointer transition-colors duration-200 ${
            selected === i ? 'text-[#2B3BE5] font-bold' : 'text-white/40 hover:text-white'
          }`}
        >
          {i} : {item}
        </div>
      ))}
    </div>
  );
}
