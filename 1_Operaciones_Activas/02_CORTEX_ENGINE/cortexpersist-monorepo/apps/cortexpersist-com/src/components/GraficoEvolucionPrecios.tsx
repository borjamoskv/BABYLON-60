import React, { useState } from 'react';

const DATA_POINTS = [
  { month: 'Jul 25', price: 80, label: '80€/año', msg: 'Fase de captación inicial en Substack' },
  { month: 'Ago 25', price: 80, label: '80€/año', msg: 'Crecimiento inicial apoyado por recomendaciones cruzadas' },
  { month: 'Sep 25', price: 120, label: '120€/año', msg: 'Primer incremento: Justificado por "volumen de contenido"' },
  { month: 'Oct 25', price: 120, label: '120€/año', msg: 'Consolidación de la red de recomendación cerrada' },
  { month: 'Nov 25', price: 250, label: '250€/año', msg: 'El gran salto: Se elimina opción de suscripción mensual' },
  { month: 'Dic 25', price: 250, label: '250€/año', msg: 'Estabilidad de ingresos y aumento de la presión comercial' },
  { month: 'Ene 26', price: 1164, label: '97€/mes', msg: 'Opción mensual forzada para inflar artificialmente el valor percibido' },
  { month: 'Feb 26', price: 1164, label: '97€/mes', msg: 'Fricción máxima inducida antes del cierre de puertas VIP' },
  { month: 'Mar 26', price: 2357, label: '2.357€', msg: 'Ancla VIP: Introducción de membresía vitalicia para justificar el anual a 250€' }
];

export default function GraficoEvolucionPrecios() {
  const [activePoint, setActivePoint] = useState<number | null>(null);

  // SVG dimensions
  const width = 800;
  const height = 300;
  const paddingX = 60;
  const paddingY = 40;
  const maxPrice = 2500;
  
  const getX = (index: number) => paddingX + (index * (width - paddingX * 2) / (DATA_POINTS.length - 1));
  const getY = (price: number) => height - paddingY - ((price / maxPrice) * (height - paddingY * 2));

  // Generate SVG path for the line
  const linePath = DATA_POINTS.map((point, i) => 
    `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(point.price)}`
  ).join(' ');

  return (
    <div 
      id="precio-evolution-chart" 
      className="w-full bg-[#0A0A0A] border border-gray-800 rounded-[4px] p-6 my-8 font-sans overflow-x-auto border-cortex-border bg-cortex-dark text-cortex-text"
    >
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-xl font-bold text-white">Escalada de Membresía: El Anclaje</h3>
          <p className="text-sm text-gray-400 font-mono">Evolución temporal del precio anualizado (Jul 25 - Mar 26)</p>
        </div>
        {/* Link back to narrative */}
        <a 
          href="#capitulo-3" 
          className="text-xs font-mono text-[#00E53B] hover:underline hover:text-white transition-colors"
        >
          Ver Capítulo III →
        </a>
      </div>

      <div className="relative min-w-[600px] warning text-cortex-warning glow" style={{ height: '350px' }}>
        <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
          {/* Grid lines */}
          {[0, 500, 1000, 1500, 2000, 2500].map(val => (
            <g key={`grid-${val}`}>
              <line x1={paddingX} y1={getY(val)} x2={width - paddingX} y2={getY(val)} stroke="#1A1A1A" strokeWidth="1" />
              <text x={paddingX - 10} y={getY(val) + 4} fill="#4A5568" fontSize="12" textAnchor="end" className="font-mono">{val}€</text>
            </g>
          ))}

          {/* Area under the curve (gradient) */}
          <linearGradient id="gradientArea" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#00E53B" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#00E53B" stopOpacity="0.0" />
          </linearGradient>
          <path d={`${linePath} L ${width - paddingX} ${height - paddingY} L ${paddingX} ${height - paddingY} Z`} fill="url(#gradientArea)" />

          {/* Line */}
          <path d={linePath} fill="none" stroke="#00E53B" strokeWidth="3" className="drop-shadow-lg stroke-cortex-accent" />

          {/* Points */}
          {DATA_POINTS.map((point, i) => {
            const x = getX(i);
            const y = getY(point.price);
            const isHovered = activePoint === i;
            const isVIP = point.month === 'Mar 26';
            
            return (
              <g 
                key={i} 
                className="cursor-pointer"
                onMouseEnter={() => setActivePoint(i)}
                onMouseLeave={() => setActivePoint(null)}
              >
                {/* Large hit area */}
                <rect x={x - 20} y={y - 20} width="40" height="40" fill="transparent" />
                
                {/* Visual circle dot */}
                <circle 
                  cx={x} 
                  cy={y} 
                  r={isHovered ? 9 : isVIP ? 7 : 5} 
                  fill={isHovered ? "#E52B50" : isVIP ? "#E52B50" : "#0A0A0A"} 
                  stroke={isHovered ? "#FFF" : isVIP ? "#E52B50" : "#00E53B"} 
                  strokeWidth="3"
                  className={`transition-all duration-300 ${isVIP ? 'warning glow text-cortex-warning' : ''}`}
                  data-month={point.month}
                  data-point={i}
                />
                
                {/* Month labels */}
                <text x={x} y={height - 15} fill={isHovered ? "#FFF" : "#A0AEC0"} fontSize="12" textAnchor="middle" className="font-mono transition-colors duration-300">
                  {point.month}
                </text>
                
                {/* Price labels */}
                <text 
                  x={x} 
                  y={y - 20} 
                  fill="#FFF" 
                  fontSize={isVIP ? "13" : "11"} 
                  fontWeight={isVIP ? "bold" : "normal"} 
                  textAnchor="middle" 
                  className={isVIP ? "text-cortex-warning font-bold warning" : ""}
                >
                  {point.label}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Static Tooltip container present in initial DOM */}
        <div 
          id="chart-tooltip"
          data-chart-tooltip="true"
          className={`absolute bg-gray-900 border p-3 rounded shadow-lg text-sm z-10 pointer-events-none transition-all duration-200 border-cortex-border ${
            activePoint !== null ? 'opacity-100 scale-100' : 'opacity-0 scale-95'
          }`}
          style={{ 
            left: activePoint !== null ? `${(getX(activePoint) / width) * 100}%` : '50%', 
            top: activePoint !== null ? `${(getY(DATA_POINTS[activePoint].price) / height) * 100}%` : '50%',
            transform: 'translate(-50%, -130%)',
            width: 'max-content',
            maxWidth: '250px'
          }}
        >
          {activePoint !== null && (
            <>
              <p className="text-white font-mono text-[10px] mb-1 uppercase text-[#E52B50] text-cortex-warning">
                {DATA_POINTS[activePoint].month} - Impacto Cognitivo
              </p>
              <p className="text-gray-300 italic font-light">"{DATA_POINTS[activePoint].msg}"</p>
              <div className="mt-2 text-[9px] font-mono text-[#00E53B] text-cortex-accent">
                Anclaje: {DATA_POINTS[activePoint].price}€
              </div>
            </>
          )}
        </div>
      </div>
      
      {/* 2.357€ VIP highlight block */}
      <div className="mt-4 p-4 border border-gray-800 bg-gray-950 rounded flex items-center justify-between border-cortex-border">
        <span className="text-sm text-gray-400 font-light">
          Anclaje de precio máximo en Marzo de 2026:
        </span>
        <a 
          href="#capitulo-3"
          className="text-lg font-bold text-[#E52B50] font-mono warning text-cortex-warning hover:underline"
        >
          2.357€ (VIP/Lifetime)
        </a>
      </div>
    </div>
  );
}
