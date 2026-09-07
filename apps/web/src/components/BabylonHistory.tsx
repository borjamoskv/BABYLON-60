import React, { useState } from 'react';
import { soundFx } from './AudioEngine';

export const BabylonHistory: React.FC = () => {
  const [selectedNumber, setSelectedNumber] = useState<number>(60);

  const divisors10 = [1, 2, 5, 10];
  const divisors60 = [1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60];

  return (
    <div className="border border-slate-800 bg-[#06080d] p-6 lg:p-8 space-y-8 font-mono">
      <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
        <span className="w-2.5 h-2.5 bg-cyan-400 block" />
        <span className="text-xs text-cyan-400 font-bold uppercase tracking-wider">
          La Arqueología de las 12 Falanges: El Error de los 10 Dedos
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Story Text */}
        <div className="lg:col-span-7 space-y-4 text-xs text-slate-300 leading-relaxed">
          <p>
            ¿Por qué la civilización moderna cuenta de 10 en 10? Por pura <strong>inercia anatómica</strong>: 
            porque tenemos 10 dedos planos en las manos. La base 10 no posee ninguna ventaja matemática o física; 
            es un accidente biológico.
          </p>
          <p>
            Hace más de 4.000 años, los astrónomos e ingenieros de <strong>Babilonia y Sumeria</strong> descubrieron 
            una técnica biomecánica infinitamente superior:
          </p>
          <div className="bg-slate-900/80 p-4 border-l-2 border-cyan-400 space-y-2">
            <div className="text-cyan-300 font-bold">La Cuenta Sexagesimal Babilónica:</div>
            <p className="text-slate-400">
              Con el pulgar de una mano, contaban las <strong>12 falanges</strong> de los otros 4 dedos (3 falanges por dedo × 4 = 12). 
              Con los 5 dedos de la otra mano, acumulaban las docenas completas:
            </p>
            <div className="text-base text-cyan-200 font-bold pt-1">
              12 falanges × 5 dedos = 60 unidades exactas.
            </div>
          </div>
          <p>
            El <strong>60</strong> es el arquetipo de los <em>números altamente compuestos</em>: tiene <strong>12 divisores enteros</strong>. 
            Cualquier fracción del tiempo o del espacio dividida en mitades, tercios, cuartos, quintos o sextos 
            da números enteros perfectos. 
          </p>
          <p className="text-slate-400 italic">
            Por eso, 4 milenios después, la humanidad fue incapaz de sustituir a Babilonia en lo que no puede fallar: 
            <strong> 60 minutos en una hora, 60 segundos en un minuto, 360° en la circunferencia y coordenadas GPS terrestres.</strong>
          </p>
        </div>

        {/* Comparison Interactive Matrix */}
        <div className="lg:col-span-5 bg-slate-900/50 border border-slate-800 p-6 space-y-6 rounded">
          <div className="text-xs text-slate-400 font-bold uppercase tracking-wider flex justify-between items-center">
            <span>Factorabilidad Comparada</span>
            <div className="flex gap-2">
              <button 
                onClick={() => { soundFx.playClick(); setSelectedNumber(10); }}
                className={`px-2 py-0.5 text-[10px] border ${selectedNumber === 10 ? 'border-red-500 bg-red-500/20 text-red-300' : 'border-slate-800 text-slate-500'}`}
              >
                Base 10
              </button>
              <button 
                onClick={() => { soundFx.playClick(); setSelectedNumber(60); }}
                className={`px-2 py-0.5 text-[10px] border ${selectedNumber === 60 ? 'border-cyan-500 bg-cyan-500/20 text-cyan-300' : 'border-slate-800 text-slate-500'}`}
              >
                Base 60
              </button>
            </div>
          </div>

          {selectedNumber === 10 ? (
            <div className="space-y-4">
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Número de divisores:</span>
                <span className="text-red-400 font-bold">4 divisores</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {divisors10.map(d => (
                  <span key={d} className="px-3 py-1 bg-red-950/40 border border-red-800 text-red-300 text-xs font-bold rounded">
                    ÷ {d}
                  </span>
                ))}
              </div>
              <div className="text-[11px] text-slate-400 bg-red-950/20 p-3 border border-red-900/30 rounded space-y-1">
                <p className="text-red-400 font-semibold">❌ Inflexibilidad en fracciones:</p>
                <p>10 ÷ 3 = 3.333333... (periódico infinito)</p>
                <p>10 ÷ 4 = 2.5 (decimal)</p>
                <p>10 ÷ 6 = 1.666666... (periódico)</p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Número de divisores:</span>
                <span className="text-cyan-400 font-bold">12 divisores enteros</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {divisors60.map(d => (
                  <span key={d} className="px-2.5 py-1 bg-cyan-950/40 border border-cyan-700 text-cyan-300 text-xs font-bold rounded">
                    ÷ {d}
                  </span>
                ))}
              </div>
              <div className="text-[11px] text-slate-400 bg-cyan-950/20 p-3 border border-cyan-900/30 rounded space-y-1">
                <p className="text-cyan-400 font-semibold">✅ Simetría y exactitud absoluta:</p>
                <p>60 ÷ 2 = 30 | 60 ÷ 3 = 20 | 60 ÷ 4 = 15</p>
                <p>60 ÷ 5 = 12 | 60 ÷ 6 = 10 | 60 ÷ 10 = 6</p>
                <p className="text-emerald-400 pt-1 font-bold">Cero restos periódicos en divisiones críticas.</p>
              </div>
            </div>
          )}

          <div className="border-t border-slate-800 pt-4 text-[10px] text-slate-500">
            BABYLON-60 transfiere esta misma simetría de hace 4.000 años al espacio de memoria y al reloj causal de los modelos de inteligencia artificial.
          </div>
        </div>
      </div>
    </div>
  );
};
