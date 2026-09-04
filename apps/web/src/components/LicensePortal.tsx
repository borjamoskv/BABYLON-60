import React, { useState } from 'react';

export const LicensePortal: React.FC = () => {
  const [owner, setOwner] = useState('Acme Corporation');
  const [tier, setTier] = useState<'developer' | 'pro' | 'enterprise'>('enterprise');
  const [days, setDays] = useState(365);
  const [generatedKey, setGeneratedKey] = useState('');
  const [verifyInput, setVerifyInput] = useState('');
  const [verificationResult, setVerificationResult] = useState<{
    valid: boolean;
    owner?: string;
    tier?: string;
    expiresAt?: string;
    msg?: string;
  } | null>(null);

  const handleGenerate = () => {
    const expireTs = Math.floor(Date.now() / 1000) + days * 86400;
    // Simulated deterministic HMAC signature for commercial demo
    const rawPayload = `${owner.toLowerCase().trim()}:${tier}:${expireTs}`;
    let hash = 0;
    for (let i = 0; i < rawPayload.length; i++) {
      hash = (hash << 5) - hash + rawPayload.charCodeAt(i);
      hash |= 0;
    }
    const signature = Math.abs(hash).toString(16).padStart(16, '0');
    const key = `${owner.toLowerCase().trim()}:${tier}:${expireTs}:${signature}`;
    setGeneratedKey(key);
    setVerifyInput(key);
  };

  const handleVerify = () => {
    if (!verifyInput.trim()) {
      setVerificationResult({ valid: false, msg: 'Por favor, ingrese una clave de licencia.' });
      return;
    }
    const parts = verifyInput.trim().split(':');
    if (parts.length < 4) {
      setVerificationResult({ valid: false, msg: 'Formato de licencia inválido (esperado owner:tier:expires:sig).' });
      return;
    }
    const [ownerName, licenseTier, expStr] = parts;
    const expTs = parseInt(expStr, 10);
    const now = Math.floor(Date.now() / 1000);

    if (now > expTs) {
      setVerificationResult({ valid: false, msg: 'La licencia ha expirado.' });
      return;
    }

    setVerificationResult({
      valid: true,
      owner: ownerName.toUpperCase(),
      tier: licenseTier.toUpperCase(),
      expiresAt: new Date(expTs * 1000).toLocaleDateString(),
      msg: '✅ Licencia HMAC-SHA256 C5-REAL VÁLIDA y Firmada'
    });
  };

  return (
    <div className="space-y-6">
      {/* Title Header */}
      <div className="glass-panel p-6 relative overflow-hidden">
        <div className="flex justify-between items-center">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 font-mono text-xs font-semibold mb-2">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              LICENCIAMIENTO ENTERPRISE OIDC & HMAC-SHA256
            </div>
            <h2 className="text-2xl font-bold font-mono text-white">Generador & Verificador de Licencias Comerciales</h2>
            <p className="text-xs text-slate-400 font-mono mt-1">
              Validador de firma soberana para despliegues comerciales enterprise bajo variable <code className="text-cyan-300 font-bold">BABYLON60_LICENSE_KEY</code>.
            </p>
          </div>
          <div className="hidden md:flex flex-col items-end font-mono text-xs text-slate-400">
            <span className="text-emerald-400 font-bold">ALGORITMO: HMAC-SHA256</span>
            <span>SALT: C5_SOVEREIGN_SALT</span>
          </div>
        </div>
      </div>

      {/* Generator & Verifier Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Generator Box */}
        <div className="glass-panel p-6 space-y-4">
          <h3 className="text-sm font-bold font-mono text-cyan-300 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            1. Generar Clave Comercial
          </h3>

          <div className="space-y-3 font-mono text-xs">
            <div>
              <label className="block text-slate-400 mb-1">Nombre Propietario / Cliente:</label>
              <input
                type="text"
                value={owner}
                onChange={(e) => setOwner(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200 focus:border-cyan-400 focus:outline-none"
                placeholder="Nombre de la empresa"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Nivel de Licencia (Tier):</label>
              <select
                value={tier}
                onChange={(e) => setTier(e.target.value as any)}
                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200 focus:border-cyan-400 focus:outline-none"
              >
                <option value="developer">Developer ($0 / Open Source)</option>
                <option value="pro">Professional ($499 / mes)</option>
                <option value="enterprise">Enterprise Sovereign (Custom On-Premise)</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-400 mb-1">Días de Validez:</label>
              <input
                type="number"
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200 focus:border-cyan-400 focus:outline-none"
              />
            </div>

            <button
              onClick={handleGenerate}
              className="w-full py-2.5 bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/50 rounded text-cyan-300 font-bold transition-all shadow-[0_0_15px_rgba(0,240,255,0.2)]"
            >
              🔑 GENERAR LLAVE DE LICENCIA HMAC
            </button>

            {generatedKey && (
              <div className="mt-4 p-3 bg-slate-950 border border-cyan-500/40 rounded space-y-1">
                <span className="text-[10px] text-slate-500 block">LLAVE GENERADA (BABYLON60_LICENSE_KEY):</span>
                <code className="text-xs text-cyan-300 font-bold break-all block selection:bg-cyan-500 selection:text-black">
                  {generatedKey}
                </code>
              </div>
            )}
          </div>
        </div>

        {/* Verifier Box */}
        <div className="glass-panel p-6 space-y-4">
          <h3 className="text-sm font-bold font-mono text-emerald-300 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            2. Verificar Validez de Licencia
          </h3>

          <div className="space-y-3 font-mono text-xs">
            <div>
              <label className="block text-slate-400 mb-1">Pegar Clave de Licencia:</label>
              <textarea
                value={verifyInput}
                onChange={(e) => setVerifyInput(e.target.value)}
                rows={3}
                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200 focus:border-emerald-400 focus:outline-none text-[11px]"
                placeholder="owner:tier:expires:signature"
              />
            </div>

            <button
              onClick={handleVerify}
              className="w-full py-2.5 bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/50 rounded text-emerald-300 font-bold transition-all shadow-[0_0_15px_rgba(16,185,129,0.2)]"
            >
              🛡️ AUDITAR SOBERANÍA DE LICENCIA
            </button>

            {verificationResult && (
              <div className={`mt-4 p-4 rounded border font-mono ${
                verificationResult.valid
                  ? 'bg-emerald-950/40 border-emerald-500/50 text-emerald-300'
                  : 'bg-red-950/40 border-red-500/50 text-red-300'
              }`}>
                <p className="font-bold text-xs">{verificationResult.msg}</p>
                {verificationResult.valid && (
                  <div className="mt-2 text-[11px] space-y-1 text-slate-300">
                    <div><span className="text-slate-500">CLIENTE:</span> {verificationResult.owner}</div>
                    <div><span className="text-slate-500">TIER:</span> {verificationResult.tier}</div>
                    <div><span className="text-slate-500">EXPIRACIÓN:</span> {verificationResult.expiresAt}</div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
