import React, { useState } from 'react';

export default function App() {
  const [catastralRef, setCatastralRef] = useState('28010-MADRID-RETIRO');
  const [selectedPreset, setSelectedPreset] = useState('madrid-cte');
  const [isCompiling, setIsCompiling] = useState(false);
  const [showModal, setShowModal] = useState(false);

  // Lead Form
  const [leadForm, setLeadForm] = useState({
    name: '',
    email: '',
    catastral: '28010-MADRID-RETIRO'
  });
  const [submitted, setSubmitted] = useState(false);

  const runVerification = () => {
    setIsCompiling(true);
    setTimeout(() => {
      setIsCompiling(false);
    }, 600);
  };

  const handleLeadSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
    setTimeout(() => {
      setShowModal(false);
      setSubmitted(false);
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-[#030508] text-slate-100 font-mono relative">
      
      {/* Header */}
      <header className="sticky top-0 z-40 bg-[#030508]/95 border-b border-[#1E293B] py-3.5 px-6">
        <div className="c5-container flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-sm font-bold tracking-tight text-white">
              AGENTS<span className="text-[#00F2FE]">.ARCHI</span>
            </span>
            <span className="text-[10px] px-2 py-0.5 border border-[#00F2FE]/30 bg-[#00F2FE]/10 text-[#00F2FE]">
              ⬡ CORTEX V1.0.4 Z3
            </span>
          </div>

          <nav className="hidden md:flex items-center gap-8 text-xs text-slate-400">
            <a href="#manifesto" className="hover:text-white transition-colors">01 / MANIFIESTO</a>
            <a href="#demo" className="hover:text-white transition-colors">02 / ENTORNO IDE</a>
            <a href="#code" className="hover:text-white transition-colors">03 / CORTEX GUARD</a>
          </nav>

          <button
            onClick={() => setShowModal(true)}
            className="px-3.5 py-1.5 text-xs font-bold text-[#030508] bg-[#00F2FE] hover:bg-[#38F9D7] transition-all"
          >
            VERIFICAR PROYECTO
          </button>
        </div>
      </header>

      {/* Hero / Sovereign Manifesto */}
      <section id="manifesto" className="py-16 border-b border-[#1E293B]">
        <div className="c5-container">
          <div className="max-w-4xl">
            <div className="text-xs text-[#00F2FE] mb-4">// FIRMA ADVERSARIAL DE BORJA MOSKV — INVARIANTE C5-REAL</div>
            <h1 className="text-2xl sm:text-4xl md:text-5xl font-extrabold text-white leading-tight mb-6">
              Detrás de AGENTS.archi opera un autómata físico gobernado por leyes termodinámicas estrictas.
            </h1>
            <p className="text-slate-400 text-xs md:text-sm leading-relaxed mb-6">
              La verdad no es conjetura; se compila paso a paso. Cero Anergía. Se eliminan las disculpas, la prosa decorativa y el <em>safety theater</em>. Verificación formal SMT/Z3 sobre restricciones lógicas CTE DB-HE/DB-SI y PGOU municipal.
            </p>
            <div className="flex flex-wrap gap-4 text-xs">
              <button
                onClick={() => setShowModal(true)}
                className="px-4 py-2 bg-[#00F2FE] text-[#030508] font-bold"
              >
                [ SOLICITAR AUDITORÍA DEDICADA ]
              </button>
              <a
                href="#demo"
                className="px-4 py-2 border border-[#1E293B] text-slate-300 hover:border-slate-500"
              >
                [ ACCEDER AL DEMO IDE ↓ ]
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Section 2: Rust Code Guard */}
      <section id="code" className="py-10 border-b border-[#1E293B] bg-[#04060A]">
        <div className="c5-container">
          <div className="flex items-center justify-between text-xs text-slate-500 pb-3 mb-3 border-b border-[#1E293B]">
            <span>crates/cortex-core/src/cortex_guard.rs</span>
            <span className="text-[#10B981]">✓ MUSL STATIC RUST BINARY</span>
          </div>
          <pre className="text-xs text-slate-300 overflow-x-auto leading-relaxed">
<code><span className="text-purple-400">pub fn</span> <span className="text-emerald-400">check_fluff</span>(payload: &amp;<span className="text-purple-400">str</span>) -&gt; <span className="text-purple-400">Result</span>&lt;<span className="text-[#00F2FE]">ExergyState</span>, <span className="text-[#EF4444]">&amp;'static str</span>&gt; &#123;
    <span className="text-purple-400">if</span> payload.contains(<span className="text-emerald-300">"safety_theater"</span>) || payload.contains(<span className="text-emerald-300">"fluff"</span>) &#123;
        <span className="text-purple-400">return</span> <span className="text-[#EF4444]">Err</span>(<span className="text-emerald-300">"ANERGY_DETECTED: Purging non-verifiable claims"</span>);
    &#125;
    <span className="text-slate-500">// Z3 SMT Constraint Resolver over Strict Structural Restraints</span>
    <span className="text-[#00F2FE]">Ok</span>(<span className="text-[#00F2FE]">ExergyState</span>::FormalProofVerified)
&#125;</code>
          </pre>
        </div>
      </section>

      {/* Section 3: Rigid Demo Bento Grid Environment */}
      <section id="demo" className="py-16 border-b border-[#1E293B]">
        <div className="c5-container">
          
          <div className="mb-6 flex items-center justify-between text-xs">
            <span className="text-[#00F2FE] font-bold">// 02. ENTORNO DE VERIFICACIÓN FORMAL (IDE DEMO)</span>
            <span className="text-slate-500">FORMATO RUST DIAGNOSTIC LOGS</span>
          </div>

          {/* Preset Buttons */}
          <div className="mb-4 flex flex-wrap gap-2 text-xs">
            <button
              onClick={() => { setSelectedPreset('madrid-cte'); runVerification(); }}
              className={`px-3 py-1 border ${selectedPreset === 'madrid-cte' ? 'border-[#00F2FE] text-[#00F2FE] bg-[#00F2FE]/10' : 'border-[#1E293B] text-slate-400'}`}
            >
              [ MADRID PGOU ZONA 4 + CTE DB-HE ]
            </button>
            <button
              onClick={() => { setSelectedPreset('sevilla-pgou'); runVerification(); }}
              className={`px-3 py-1 border ${selectedPreset === 'sevilla-pgou' ? 'border-[#00F2FE] text-[#00F2FE] bg-[#00F2FE]/10' : 'border-[#1E293B] text-slate-400'}`}
            >
              [ SEVILLA ZU-4 + CTE DB-SI ]
            </button>
            <button
              onClick={() => { setSelectedPreset('barcelona-bcn'); runVerification(); }}
              className={`px-3 py-1 border ${selectedPreset === 'barcelona-bcn' ? 'border-[#00F2FE] text-[#00F2FE] bg-[#00F2FE]/10' : 'border-[#1E293B] text-slate-400'}`}
            >
              [ BARCELONA EIXAMPLE REHAB ]
            </button>
          </div>

          {/* 3-Block Rigid Grid */}
          <div className="demo-container">
            
            {/* Panel A: INPUT PANEL */}
            <div className="demo-panel">
              <div className="text-xs text-slate-400 mb-3 border-b border-[#1E293B] pb-2 font-bold flex justify-between">
                <span>[ INPUT PANEL ]</span>
                <span className="text-[#00F2FE]">PARSER A1</span>
              </div>

              <div className="demo-drag-box mb-4">
                <div className="text-xs text-slate-300">
                  Suelte archivo técnico (.IFC, .DWG, .PDF).
                </div>
                <div className="text-[10px] text-slate-500 mt-1">
                  El autómata ignorará metadatos decorativos.
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[10px] text-slate-400 block uppercase">
                  Referencia Catastral / Municipio:
                </label>
                <input
                  type="text"
                  value={catastralRef}
                  onChange={(e) => setCatastralRef(e.target.value)}
                  className="w-full bg-[#030508] border border-[#1E293B] text-xs text-white p-2 focus:border-[#00F2FE] focus:outline-none"
                />
              </div>

              <button
                onClick={runVerification}
                className="mt-4 w-full py-2 bg-[#00F2FE] text-[#030508] text-xs font-bold uppercase hover:bg-[#38F9D7]"
              >
                EJECUTAR VERIFICACIÓN Z3
              </button>
            </div>

            {/* Panel B: TERMINAL DE COMPILACIÓN (LOGS) */}
            <div className="demo-panel bg-[#04060A]">
              <div className="text-xs text-slate-400 mb-3 border-b border-[#1E293B] pb-2 font-bold flex justify-between">
                <span>[ TERMINAL DE COMPILACIÓN ]</span>
                <span className="text-[#10B981]">LOG STREAM</span>
              </div>

              {isCompiling ? (
                <div className="py-12 text-center text-xs text-[#00F2FE]">
                  &gt; [RUNNING] Z3 SMT Solver procesando restricciones...
                </div>
              ) : (
                <div className="space-y-1.5 text-[11px] text-slate-300 font-mono">
                  <p><span className="text-slate-500">[00:01]</span> <span className="text-[#00F2FE]">[CORTEX]</span> Archivo recibido. Hash SHA-256 verificado.</p>
                  <p><span className="text-slate-500">[00:03]</span> <span className="text-[#00F2FE]">[GEOMETRY]</span> Polígonos de ocupación en planta: 412.35 m².</p>
                  <p><span className="text-slate-500">[00:05]</span> <span className="text-[#00F2FE]">[COMPLIANCE]</span> Extrayendo base vectorial PGOU ({catastralRef})...</p>
                  <p><span className="text-slate-500">[00:07]</span> <span className="text-[#00F2FE]">[VERIFICATION]</span> Árboles de decisión CTE DB-HE0 &amp; DB-SI6.</p>
                  <p><span className="text-slate-500">[00:09]</span> <span className="text-[#EF4444]">[Z3_SOLVER]</span> Restricción Retranqueo: UNSAT. Generando evidencia.</p>
                </div>
              )}
            </div>

            {/* Panel C: VERDICT PANEL (INFORME DE EVIDENCIA FORENSE ESTILO RUST COMPILER) */}
            <div className="verdict-panel">
              <div className="text-xs text-slate-400 mb-4 border-b border-[#1E293B] pb-2 font-bold flex justify-between">
                <span>[ VERDICT PANEL: INFORME DE EVIDENCIA FORENSE ]</span>
                <span className="text-[#EF4444]">STATUS: UNSAT (2 ERRORS / 1 PASS)</span>
              </div>

              <div className="space-y-4">
                
                {/* Rust Error 1 */}
                <div className="rust-error-block">
                  <div className="text-[#EF4444] font-bold mb-1">
                    [ERR_042] INCUMPLIMIENTO DE RETRANQUEO A LINDEROS
                  </div>
                  <div className="text-slate-300 text-[11px] mb-2">
                    ── Edificabilidad técnica superada en Fachada Norte.
                  </div>
                  <div className="text-[#94A3B8] text-[11px] space-y-0.5">
                    <p>│</p>
                    <p>├─ Plano aportado: Distancia medida = <strong className="text-white">2.85m</strong></p>
                    <p>├─ Norma aplicable: Retranqueo mínimo obligado = <strong className="text-white">3.00m</strong> (Diferencia: -0.15m)</p>
                    <p>│</p>
                    <p>└─ Evidencia Legal: <span className="text-[#00F2FE]">PGOU Madrid - Sección II, Art. 14.3.a ("Distancias mínimas a colindantes")</span></p>
                  </div>
                </div>

                {/* Rust Error 2 */}
                <div className="rust-error-block">
                  <div className="text-[#EF4444] font-bold mb-1">
                    [ERR_089] EXCESO DE CONSUMO DE ENERGÍA PRIMARIA NO RENOVABLE
                  </div>
                  <div className="text-slate-300 text-[11px] mb-2">
                    ── Demanda térmica supera el umbral límite CTE Zona D3.
                  </div>
                  <div className="text-[#94A3B8] text-[11px] space-y-0.5">
                    <p>│</p>
                    <p>├─ Calculado en Modelo IFC: <strong className="text-white">31.4 kWh/m²·año</strong></p>
                    <p>├─ Límite Máximo Permitido: <strong className="text-white">28.0 kWh/m²·año</strong></p>
                    <p>│</p>
                    <p>└─ Evidencia Legal: <span className="text-[#00F2FE]">CTE DB-HE0 (Sección 3.1, Tabla 3.1a)</span></p>
                  </div>
                </div>

                {/* Rust Pass 1 */}
                <div className="rust-pass-block">
                  <div className="text-[#10B981] font-bold mb-1">
                    [PASS_012] RETRANQUEO A FACHADA PRINCIPAL
                  </div>
                  <div className="text-slate-300 text-[11px]">
                    │ Medido: 3.45m | Mínimo Exigido: 3.00m [SATISFIED]
                  </div>
                </div>

              </div>
            </div>

          </div>

        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 bg-[#030508] border-t border-[#1E293B] text-xs text-slate-500">
        <div className="c5-container flex flex-col md:flex-row items-center justify-between gap-4">
          <div>
            © 2026 AGENTS.ARCHI — Borja Moskv Sovereign Ledger.
          </div>
          <div className="flex gap-6">
            <a href="https://babylon60.com" target="_blank" rel="noopener noreferrer" className="hover:text-white">BABYLON60 Runtime</a>
            <a href="#code" className="hover:text-white">cortex_guard.rs</a>
          </div>
        </div>
      </footer>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 bg-[#030508]/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="max-w-md w-full p-6 bg-[#080C14] border border-[#1E293B] font-mono relative">
            <button
              onClick={() => setShowModal(false)}
              className="absolute top-4 right-4 text-slate-500 hover:text-white"
            >
              ✕
            </button>

            <div className="mb-4">
              <span className="text-[10px] text-[#00F2FE] uppercase">// REGISTRO DE AUDITORÍA</span>
              <h3 className="text-base font-bold text-white mt-1">Solicitar Verificación C5-REAL</h3>
            </div>

            {submitted ? (
              <div className="p-4 bg-[#10B981]/10 border border-[#10B981]/30 text-[#10B981] text-xs text-center">
                ✓ Solicitud Recibida. Hash de registro asignado.
              </div>
            ) : (
              <form onSubmit={handleLeadSubmit} className="space-y-3 text-xs">
                <div>
                  <label className="text-slate-400 block mb-1">Nombre / Estudio:</label>
                  <input
                    type="text"
                    required
                    placeholder="Arq. María González"
                    value={leadForm.name}
                    onChange={(e) => setLeadForm({ ...leadForm, name: e.target.value })}
                    className="w-full bg-[#030508] border border-[#1E293B] text-white p-2 focus:border-[#00F2FE] focus:outline-none"
                  />
                </div>

                <div>
                  <label className="text-slate-400 block mb-1">Email Profesional:</label>
                  <input
                    type="email"
                    required
                    placeholder="maria@estudio.com"
                    value={leadForm.email}
                    onChange={(e) => setLeadForm({ ...leadForm, email: e.target.value })}
                    className="w-full bg-[#030508] border border-[#1E293B] text-white p-2 focus:border-[#00F2FE] focus:outline-none"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full py-2 bg-[#00F2FE] text-[#030508] font-bold uppercase hover:bg-[#38F9D7] mt-2"
                >
                  REGISTRAR PARA VERIFICACIÓN
                </button>
              </form>
            )}
          </div>
        </div>
      )}

    </div>
  );
}
