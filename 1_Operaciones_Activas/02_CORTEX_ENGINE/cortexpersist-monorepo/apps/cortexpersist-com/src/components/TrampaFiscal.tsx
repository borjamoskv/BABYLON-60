// @C5-REAL
import React, { useState } from 'react';
import { Check, ShieldAlert, Filter, RefreshCw } from 'lucide-react';

interface TaxRow {
  variable: string;
  ley49: string | null;
  ihelp: string | null;
  description: string;
}

const TAX_DATA: TaxRow[] = [
  {
    variable: "Deducción",
    ley49: "80% de deducción fiscal",
    ihelp: "80% de deducción para los primeros 250€",
    description: "Porcentaje del capital aportado deducible en el IRPF"
  },
  {
    variable: "IVA",
    ley49: "Exento (sin IVA)",
    ihelp: "Exento de IVA por donación directa",
    description: "Aplicabilidad de impuesto indirecto sobre el servicio"
  },
  {
    variable: "Coste Real",
    ley49: "20% neto del valor aportado",
    ihelp: "50€ de coste neto real para donaciones de 250€",
    description: "Gasto monetario final del adquirente tras incentivos"
  },
  {
    variable: "Validación Jurídica",
    ley49: "Requiere convenio formal",
    ihelp: null, // Test fallback to "-"
    description: "Estado de la base reguladora para el cumplimiento"
  }
];

export default function TrampaFiscal() {
  const [activeFilter, setActiveFilter] = useState<'all' | 'ihelp' | 'fiscal'>('all');

  const filterCampaign = (campaign: 'all' | 'ihelp' | 'fiscal') => {
    setActiveFilter(campaign);
    
    // Dispatch custom event to trigger EcosistemaCreadores filter
    const event = new CustomEvent('cortex-filter-campaign', {
      detail: { campaign }
    });
    window.dispatchEvent(event);
  };

  return (
    <div className="w-full bg-[#0A0A0A] border border-white/[0.06] rounded-[4px] p-6 relative overflow-hidden group">
      {/* Subtle warning glow */}
      <div className="absolute -top-24 -left-24 w-48 h-48 bg-cortex-warning/5 rounded-full blur-3xl pointer-events-none"></div>
      
      {/* Component Title & Status */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <ShieldAlert className="text-cortex-warning w-4 h-4 animate-pulse" />
            <span className="text-cortex-warning font-mono text-[10px] tracking-[0.2em] uppercase">Auditoría Fiscal Reguladora</span>
          </div>
          <h3 className="text-xl font-light text-white tracking-tight">Estructura de Deducción · Ley 49/2002 & iHelp</h3>
        </div>
        
        {/* Interactive Filter Controls inside the component */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-white/40 uppercase mr-1">Filtrar Red:</span>
          <button 
            data-filter="all"
            data-campaign-trigger="all"
            onClick={() => filterCampaign('all')}
            className={`px-2.5 py-1 rounded text-[9px] font-mono transition-all flex items-center gap-1 cursor-pointer ${
              activeFilter === 'all' 
                ? 'bg-cortex-accent text-white shadow-[0_0_10px_rgba(0,229,59,0.3)]' 
                : 'bg-[#0A0A0A]/30 border border-white/[0.06] text-white/50 hover:text-white hover:border-white/20'
            }`}
          >
            <RefreshCw className="w-2.5 h-2.5" />
            VER TODOS
          </button>
          <button 
            data-filter="fiscal"
            data-campaign-trigger="fiscal"
            onClick={() => filterCampaign('fiscal')}
            className={`px-2.5 py-1 rounded text-[9px] font-mono transition-all flex items-center gap-1 cursor-pointer ${
              activeFilter === 'fiscal' 
                ? 'bg-cortex-accent text-white shadow-[0_0_10px_rgba(0,229,59,0.3)]' 
                : 'bg-[#0A0A0A]/30 border border-white/[0.06] text-white/50 hover:text-white hover:border-white/20'
            }`}
          >
            <Filter className="w-2.5 h-2.5" />
            LEY 49/2002
          </button>
          <button 
            data-filter="ihelp"
            data-campaign-trigger="ihelp"
            onClick={() => filterCampaign('ihelp')}
            className={`px-2.5 py-1 rounded text-[9px] font-mono transition-all flex items-center gap-1 cursor-pointer ${
              activeFilter === 'ihelp' 
                ? 'bg-cortex-accent text-white shadow-[0_0_10px_rgba(0,229,59,0.3)]' 
                : 'bg-[#0A0A0A]/30 border border-white/[0.06] text-white/50 hover:text-white hover:border-white/20'
            }`}
          >
            <Filter className="w-2.5 h-2.5" />
            IHELP
          </button>
        </div>
      </div>

      {/* Main Comparison Table */}
      <div className="overflow-x-auto custom-scrollbar border border-white/[0.06] rounded-[4px] bg-[#0A0A0A]/20">
        <table 
          id="trampa-fiscal-table" 
          data-trampa-fiscal 
          className="w-full text-left border-collapse border-spacing-0"
        >
          <thead>
            <tr className="border-b border-white/[0.06] bg-white/[0.02]">
              <th className="p-4 px-6 py-4 text-xs font-mono text-white/40 uppercase tracking-wider">Concepto Impositivo</th>
              <th 
                data-campaign="fiscal" 
                onClick={() => filterCampaign('fiscal')}
                className="p-4 px-6 py-4 text-xs font-mono text-white tracking-widest uppercase cursor-pointer hover:text-cortex-accent transition-colors"
              >
                Ley 49/2002
              </th>
              <th 
                data-campaign="ihelp" 
                onClick={() => filterCampaign('ihelp')}
                className="p-4 px-6 py-4 text-xs font-mono text-white tracking-widest uppercase cursor-pointer hover:text-cortex-accent transition-colors"
              >
                iHelp
              </th>
            </tr>
          </thead>
          <tbody>
            {TAX_DATA.map((row) => (
              <tr 
                key={row.variable} 
                className={`border-b border-white/[0.06] hover:bg-white/[0.01] transition-colors ${
                  row.variable === "Coste Real" ? "bg-cortex-warning/5 border-l-2 border-l-cortex-warning border-cortex-warning" : ""
                }`}
              >
                {/* Variable Cell */}
                <td className="p-4 px-6 py-4 font-mono text-xs font-semibold text-white/80 break-words whitespace-normal">
                  <div className="flex flex-col">
                    <span>{row.variable}</span>
                    <span className="text-[10px] text-white/30 font-light mt-0.5">{row.description}</span>
                  </div>
                </td>

                {/* Ley 49/2002 Value Cell */}
                <td className="p-4 px-6 py-4 text-xs text-white/70 font-mono break-words whitespace-normal">
                  <div className="flex items-center gap-2">
                    {row.ley49 !== null ? (
                      <>
                        <Check className="text-green-400 w-3.5 h-3.5 shrink-0" aria-label="Beneficio válido" />
                        <span>{row.ley49}</span>
                      </>
                    ) : (
                      <span>-</span>
                    )}
                  </div>
                </td>

                {/* iHelp Value Cell */}
                <td className="p-4 px-6 py-4 text-xs text-white/70 font-mono break-words whitespace-normal">
                  <div className="flex items-center gap-2">
                    {row.ihelp !== null ? (
                      <>
                        <Check className="text-green-400 w-3.5 h-3.5 shrink-0" aria-label="Beneficio válido" />
                        <span>{row.ihelp}</span>
                      </>
                    ) : (
                      <span>-</span>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer Info Disclaimer */}
      <div className="mt-4 p-4 rounded-[4px] bg-[#0A0A0A]/40 border border-white/[0.06] text-[10px] font-mono text-white/40 leading-relaxed break-words whitespace-normal">
        <span className="text-cortex-warning font-semibold">⚠️ AVISO LEGAL Y EXENCIÓN DE RESPONSABILIDAD:</span> Las simulaciones impositivas y cálculos derivados de la <span className="text-white/60">Ley 49/2002</span> y el programa <span className="text-white/60">iHelp</span> mostrados arriba son estrictamente con fines ilustrativos, didácticos y académicos. No constituyen recomendación ni asesoramiento financiero, legal o fiscal de ningún tipo.
      </div>
    </div>
  );
}
