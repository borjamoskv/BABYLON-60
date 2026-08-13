import React, { useState } from 'react';

export const ComplianceInspector: React.FC = () => {
  const [selectedFormat, setSelectedFormat] = useState<'html' | 'json' | 'markdown'>('html');
  const [activeArticle, setActiveArticle] = useState<number>(9);

  const articles = [
    { id: 9, title: 'Art. 9: Gestión de Riesgos', code: 'RISK_MGMT', status: 'PASS', score: '100%' },
    { id: 10, title: 'Art. 10: Gobernanza de Datos', code: 'DATA_GOV', status: 'PASS', score: '100%' },
    { id: 11, title: 'Art. 11: Documentación Técnica', code: 'TECH_DOCS', status: 'PASS', score: '100%' },
    { id: 12, title: 'Art. 12: Registro de Eventos (Logs)', code: 'LOGGING', status: 'PASS', score: '100%' },
    { id: 14, title: 'Art. 14: Supervisión Humana (HITL)', score: '100%', code: 'HUMAN_OVER', status: 'PASS' },
  ];

  return (
    <div className="space-y-6 font-mono">
      {/* Title Header */}
      <div className="glass-panel p-6 relative overflow-hidden">
        <div className="flex justify-between items-center">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs font-semibold mb-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              REGULATORY AUDIT CERTIFIER — EU AI ACT
            </div>
            <h2 className="text-2xl font-bold text-white">Inspección de Certificado de Cumplimiento Regulatorio</h2>
            <p className="text-xs text-slate-400 mt-1">
              Validación automatizada de los Artículos 9–14 para sistemas IA de alto riesgo bajo la CLI <code className="text-emerald-300 font-bold">babylon60-compliance</code>.
            </p>
          </div>
          <div className="flex gap-2">
            {(['html', 'json', 'markdown'] as const).map((fmt) => (
              <button
                key={fmt}
                onClick={() => setSelectedFormat(fmt)}
                className={`px-3 py-1.5 rounded text-xs font-bold transition-all ${
                  selectedFormat === fmt
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-[0_0_10px_rgba(16,185,129,0.2)]'
                    : 'bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200'
                }`}
              >
                {fmt.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Article Selector Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3">
        {articles.map((art) => (
          <button
            key={art.id}
            onClick={() => setActiveArticle(art.id)}
            className={`p-4 rounded-lg border text-left transition-all ${
              activeArticle === art.id
                ? 'bg-emerald-950/30 border-emerald-500/60 shadow-[0_0_15px_rgba(16,185,129,0.2)]'
                : 'glass-panel border-slate-800 hover:border-slate-700'
            }`}
          >
            <div className="flex justify-between items-center mb-1">
              <span className="text-[10px] text-slate-400">{art.code}</span>
              <span className="text-xs text-emerald-400 font-bold">{art.status}</span>
            </div>
            <div className="text-xs font-bold text-slate-200 truncate">{art.title}</div>
            <div className="text-[10px] text-slate-500 mt-2">Cumplimiento: {art.score}</div>
          </button>
        ))}
      </div>

      {/* Preview Inspector */}
      <div className="glass-panel p-6 space-y-4">
        <div className="flex justify-between items-center text-xs text-slate-400 border-b border-slate-800 pb-3">
          <span className="flex items-center gap-2 text-slate-200 font-bold">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            VISTA PREVIA DE CERTIFICADO DE CUMPLIMIENTO ({selectedFormat.toUpperCase()})
          </span>
          <span>SHA-256: 0x9f8b...2c4a | ISO-8601 UTC</span>
        </div>

        {selectedFormat === 'html' && (
          <div className="p-4 bg-slate-950 border border-slate-800 rounded font-sans text-xs text-slate-300 space-y-4">
            <div className="border-b border-slate-800 pb-3 flex justify-between items-center">
              <div>
                <h3 className="text-lg font-bold text-white font-mono">Certificado de Cumplimiento Regulatorio — EU AI Act</h3>
                <p className="text-xs text-emerald-400 font-mono">Emisor: BABYLON-60 Compliance Engine v4.0.0</p>
              </div>
              <span className="px-3 py-1 bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 rounded font-mono text-xs font-bold">
                AUDITORÍA VÁLIDA
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4 font-mono text-xs">
              <div className="p-3 bg-slate-900/60 rounded border border-slate-800">
                <span className="text-slate-500 block text-[10px]">ID CERTIFICADO:</span>
                <span className="text-cyan-300 font-bold">B60-EU-AI-ACT-2026-0813-001</span>
              </div>
              <div className="p-3 bg-slate-900/60 rounded border border-slate-800">
                <span className="text-slate-500 block text-[10px]">ARTÍCULOS CUBIERTOS:</span>
                <span className="text-emerald-300 font-bold">9, 10, 11, 12, 14 (100% OK)</span>
              </div>
            </div>

            <div className="space-y-2 font-mono text-xs">
              <h4 className="text-slate-200 font-bold">Detalles del Artículo Seleccionado ({activeArticle}):</h4>
              <p className="text-slate-400 text-xs leading-relaxed">
                {activeArticle === 9 && 'Artículo 9 (Sistema de Gestión de Riesgos): Implementa mitigación activa de riesgos mediante invariantes causal-deterministas Z3 SMT y filtros Popperianos.'}
                {activeArticle === 10 && 'Artículo 10 (Gobernanza de Datos): Inmutabilidad del dataset respaldada por Merkle Tree Root y firma criptográfica sin derivaciones de sesgo.'}
                {activeArticle === 11 && 'Artículo 11 (Documentación Técnica): Documentación completa de arquitectura C5-REAL, especificaciones formalizadas y esquemas en repositorio soberano.'}
                {activeArticle === 12 && 'Artículo 12 (Conservación de Registros / Logging): WAL append-only SQLite en $BABYLON_HOME con timestamps de Lamport monotónicos.'}
                {activeArticle === 14 && 'Artículo 14 (Supervisión Humana / HITL): Puntos de control de interrupción Do-Calculus y validación manual soberana en bucles de inferencia.'}
              </p>
            </div>
          </div>
        )}

        {selectedFormat === 'json' && (
          <pre className="p-4 bg-slate-950 border border-slate-800 rounded text-[11px] text-cyan-300 overflow-x-auto">
{JSON.stringify({
  certificate_id: "B60-EU-AI-ACT-2026-0813-001",
  framework: "BABYLON-60 Sovereign Compliance",
  eu_ai_act_articles: {
    art_9_risk_management: "PASS",
    art_10_data_governance: "PASS",
    art_11_technical_documentation: "PASS",
    art_12_record_keeping: "PASS",
    art_14_human_oversight: "PASS"
  },
  attestation_hash: "30512f6f4a4b76a096070915bf91ff8b916ca7063f41d",
  overall_status: "COMPLIANT"
}, null, 2)}
          </pre>
        )}

        {selectedFormat === 'markdown' && (
          <pre className="p-4 bg-slate-950 border border-slate-800 rounded text-[11px] text-slate-300 overflow-x-auto">
{`# 🛡️ Certificado de Cumplimiento EU AI Act — BABYLON-60 v4.0.0

- **ID Certificado:** B60-EU-AI-ACT-2026-0813-001
- **Estado Global:** COMPLIANT (100% Verificado)
- **Artículos Cumplidos:**
  - ✅ **Artículo 9 (Gestión de Riesgos):** Satisfecho por Solver Z3.
  - ✅ **Artículo 10 (Gobernanza de Datos):** Merkle Root inmutable.
  - ✅ **Artículo 11 (Doc Técnica):** Especificación C5-REAL completa.
  - ✅ **Artículo 12 (Logging):** Single-writer WAL append-only.
  - ✅ **Artículo 14 (Supervisión Humana):** Controles HITL activos.`}
          </pre>
        )}
      </div>
    </div>
  );
};
