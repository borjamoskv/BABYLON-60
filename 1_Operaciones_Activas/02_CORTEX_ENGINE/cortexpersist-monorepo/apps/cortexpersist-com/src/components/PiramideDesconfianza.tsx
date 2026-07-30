import React, { useState } from 'react';

const TIERS = [
  {
    id: 4,
    key: 'sovereign',
    title: 'Nivel 4: El Círculo Interno',
    price: '3.000€',
    function: 'Extracción máxima del "1%" con alto presupuesto',
    mechanic: 'Retiros privados, consultoría 1-a-1 sin entregables definidos.',
    color: '#E52B50', // Warning Red
    width: 'w-[40%]',
    tag: 'Sovereign'
  },
  {
    id: 3,
    key: 'core',
    title: 'Nivel 3: El Bootcamp',
    price: '300€ - 1,000€',
    function: 'Extracción rápida de la cohorte comprometida',
    mechanic: 'Cursos de 4 semanas, escasez artificial ("solo 20 plazas"), FOMO extremo.',
    color: '#9C27B0', // Purple
    width: 'w-[60%]',
    tag: 'Core'
  },
  {
    id: 2,
    key: 'growth',
    title: 'Nivel 2: La Membresía',
    price: '10€ - 30€/mes',
    function: 'Generación de MRR (Ingresos Recurrentes)',
    mechanic: 'Newsletter premium. Contenido a menudo reciclado o traducido.',
    color: '#00E53B', // Cortex Accent
    width: 'w-[80%]',
    tag: 'Growth'
  },
  {
    id: 1,
    key: 'base',
    title: 'Nivel 1: El Cebo (Free)',
    price: '0€',
    function: 'Captura masiva de emails y atención',
    mechanic: 'Clickbait, hilos virales en X/LinkedIn, pop-ups agresivos.',
    color: '#4A5568', // Gray
    width: 'w-full',
    tag: 'Base'
  }
];

export default function PiramideDesconfianza() {
  const [selectedTier, setSelectedTier] = useState<number>(1);
  const activeTier = TIERS.find(t => t.id === selectedTier) || TIERS[3];

  return (
    <div 
      id="piramide-desconfianza" 
      className="w-full bg-[#0A0A0A] border border-gray-800 rounded-[4px] p-6 my-8 font-sans flex flex-col md:flex-row gap-8 bg-cortex-dark border-cortex-border text-cortex-text"
    >
      {/* Left side: The Pyramid structure */}
      <div className="w-full md:w-1/2 flex flex-col items-center justify-center space-y-2">
        <h4 className="text-sm font-mono text-gray-500 mb-4 uppercase tracking-[0.2em]">Topología del Embudo</h4>
        {TIERS.map((tier) => {
          const isActive = selectedTier === tier.id;
          return (
            <button
              key={tier.id}
              role="button"
              aria-label={`Seleccionar ${tier.title}`}
              aria-selected={isActive}
              data-tier={tier.id}
              data-active={isActive ? "true" : "false"}
              onClick={() => setSelectedTier(tier.id)}
              onMouseEnter={() => setSelectedTier(tier.id)}
              className={`pyramid-tier-btn flex flex-col items-center justify-center cursor-pointer transition-all duration-300 ${tier.width} ${
                isActive ? 'scale-[1.02] bg-cortex-accent border-cortex-accent drop-shadow-[0_0_15px_#00E53B80] bg-[#00E53B]' : 'opacity-70 hover:opacity-100'
              }`}
            >
              <div 
                className="w-full h-16 sm:h-20 flex flex-col items-center justify-center text-center rounded border border-white/[0.06]"
                style={{ 
                  backgroundColor: tier.color,
                  clipPath: tier.id === 4 ? 'polygon(50% 0%, 100% 100%, 0% 100%)' : 'polygon(5% 0, 95% 0, 100% 100%, 0% 100%)',
                }}
              >
                <span className="text-white font-bold tracking-wide text-lg drop-shadow-md">
                  {tier.price}
                </span>
                <span className="text-white/60 font-mono text-[10px] uppercase tracking-wider">
                  {tier.tag}
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Right side: Detailed descriptions */}
      <div className="w-full md:w-1/2 flex flex-col justify-between">
        <div 
          id="piramide-details" 
          data-tier-details={selectedTier}
          className="bg-gray-900/50 border border-gray-800 p-6 rounded-[4px] min-h-[220px] flex flex-col justify-between bg-cortex-dark-lighter border-cortex-border"
        >
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-mono text-[#00E53B] uppercase tracking-wider text-cortex-accent">
                {activeTier.tag} Level
              </span>
              <span 
                className="px-2 py-0.5 rounded text-[10px] font-mono font-bold text-white uppercase"
                style={{ backgroundColor: activeTier.color }}
              >
                {activeTier.price}
              </span>
            </div>
            <h4 className="text-xl font-bold text-white mb-2">{activeTier.title}</h4>
            <div className="text-sm text-gray-300 space-y-3 font-light">
              <p>
                <strong className="text-gray-500 font-mono text-xs block mb-0.5">Función Principal:</strong> 
                {activeTier.function}
              </p>
              <p>
                <strong className="text-gray-500 font-mono text-xs block mb-0.5">Mecánica de Extracción:</strong> 
                {activeTier.mechanic}
              </p>
            </div>
          </div>
          <div className="text-[10px] font-mono text-gray-500 mt-4 border-t border-gray-800/40 pt-2 text-right">
            Seleccionado: Nivel {activeTier.id} · C5-REAL attestation
          </div>
        </div>
      </div>
    </div>
  );
}
