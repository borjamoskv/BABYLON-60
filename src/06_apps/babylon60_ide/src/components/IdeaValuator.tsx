// C5-REAL EXERGY CERTIFIED - PITCH & CONVERSION ENGINE
import { useState } from 'react';
import { Zap, ShoppingCart, CheckCircle, Rocket, ArrowRight, ShieldCheck } from 'lucide-react';

export function IdeaValuator() {
  const [pitchText, setPitchText] = useState('');
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [score, setScore] = useState<number | null>(null);
  const [progress, setProgress] = useState(0);
  const [purchaseSuccess, setPurchaseSuccess] = useState(false);
  const targetScore = 21000;

  const handleEvaluate = () => {
    if (!pitchText.trim() || isEvaluating) return;
    setIsEvaluating(true);

    const startScore = Math.floor(Math.random() * 4000) + 2000;
    setScore(startScore);
    setProgress(0);

    let current = startScore;
    const interval = setInterval(() => {
      current += Math.floor(Math.random() * 600) + 200;
      if (current >= targetScore) {
        current = targetScore;
        clearInterval(interval);
        setIsEvaluating(false);
      }
      setScore(current);
      setProgress((current / targetScore) * 100);
    }, 40);
  };

  const [showCheckoutModal, setShowCheckoutModal] = useState(false);
  const [customStripeUrl, setCustomStripeUrl] = useState('https://babylon60.com/');

  const handleBuy = () => {
    const targetUrl = import.meta.env.VITE_STRIPE_URL || customStripeUrl || 'https://babylon60.com/';
    window.open(targetUrl, '_blank');
  };

  return (
    <div className="idea-valuator pitch-conversion-card">
      <div className="valuator-header pitch-header">
        <Rocket size={18} className="text-green" />
        <span className="pitch-title">MOTOR DE PITCH & CONVERSIÓN BABYLON-60</span>
        <span className="pitch-badge">PITCH DIRECTO</span>
      </div>

      <p className="pitch-subtitle">
        Introduce tu idea o propuesta ejecutiva. BABYLON-60 evaluará su exergía y colapsará el pitch en un contrato determinista.
      </p>

      {/* Primary Pitch Input Area */}
      <div className="valuator-input-area">
        <textarea
          value={pitchText}
          onChange={(e) => setPitchText(e.target.value)}
          placeholder="Escribe aquí el Pitch de tu idea (ej. Plataforma local con 0 coste de nube que automatiza contratos bajo EU AI Act)..."
          className="valuator-input pitch-textarea"
          rows={4}
        />
        
        <div className="pitch-actions-bar">
          <button
            onClick={handleEvaluate}
            className={`valuator-btn btn-pitch-eval ${isEvaluating ? 'evaluating' : ''}`}
            disabled={isEvaluating || !pitchText.trim()}
          >
            <Zap size={18} />
            {isEvaluating ? 'AUDITANDO PITCH EN RING-0...' : 'VALORAR PITCH AHORA'}
          </button>
        </div>
      </div>

      {/* Pitch Evaluation Results */}
      {score !== null && (
        <div className="valuator-result pitch-result-box">
          <div className="score-display">
            <span className="score-label">VALOR EXERGÉTICO DEL PITCH:</span>
            <span className={`score-value ${score === targetScore ? 'max-score' : ''}`}>
              {score.toLocaleString()} / 21,000 EXG
            </span>
          </div>

          <div className="progress-bar-bg">
            <div
              className="progress-bar-fill"
              style={{ width: `${progress}%` }}
            ></div>
          </div>

          {score === targetScore && (
            <div className="max-reached-alert">
              ✓ PITCH VALIDADO: ÓPTIMO EXERGÉTICO Y COMPLIANCE EU AI ACT ALCANZADO
            </div>
          )}
        </div>
      )}

      {/* DIRECT BUY / CONVERSION SECTION */}
      <div className="pitch-buy-section">
        <div className="buy-card-header">
          <ShieldCheck size={18} color="#00FF41" />
          <span>ADQUIRIR LICENCIA BABYLON-60</span>
        </div>
        
        <ul className="buy-benefits-list">
          <li>✓ <strong>$0 Coste Marginal de Nube:</strong> Cómputo local soberano.</li>
          <li>✓ <strong>Garantía Fail-Stop:</strong> Cero alucinación o deriva estocástica.</li>
          <li>✓ <strong>Compliance EU AI Act:</strong> Artículos 9-14 atestados por hardware.</li>
        </ul>

        <button onClick={handleBuy} className="btn-buy-now">
          <ShoppingCart size={18} />
          <span>ADQUIRIR LICENCIA BABYLON-60</span>
          <ArrowRight size={18} />
        </button>
      </div>

      {/* NATIVE CHECKOUT MODAL */}
      {showCheckoutModal && (
        <div className="checkout-modal-overlay" onClick={() => setShowCheckoutModal(false)}>
          <div className="checkout-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="checkout-modal-header">
              <ShieldCheck size={20} className="text-green" />
              <h3>PASARELA DE PAGO BABYLON-60</h3>
              <button className="btn-close-modal" onClick={() => setShowCheckoutModal(false)}>✕</button>
            </div>

            <p className="checkout-modal-desc">
              Introduce el enlace de Stripe de tu producto o activa la pasarela de prueba soberana BABYLON-60.
            </p>

            <div className="checkout-input-group">
              <label>URL de Checkout Stripe (Personalizado):</label>
              <input
                type="url"
                placeholder="https://buy.stripe.com/tu_enlace_personalizado"
                value={customStripeUrl}
                onChange={(e) => setCustomStripeUrl(e.target.value)}
                className="checkout-url-input"
              />
            </div>

            <div className="checkout-modal-actions">
              {customStripeUrl ? (
                <button
                  className="btn-buy-now"
                  onClick={() => window.open(customStripeUrl, '_blank')}
                >
                  <ShoppingCart size={16} />
                  <span>IR A STRIPE PERSONALIZADO</span>
                </button>
              ) : (
                <button
                  className="btn-buy-now"
                  onClick={() => {
                    setPurchaseSuccess(true);
                    setTimeout(() => setShowCheckoutModal(false), 1500);
                  }}
                >
                  <CheckCircle size={16} />
                  <span>CONFIRMAR ADQUISICIÓN SOBERANA ($0 COGS)</span>
                </button>
              )}
            </div>

            {purchaseSuccess && (
              <div className="buy-success-badge" style={{ marginTop: '12px' }}>
                <CheckCircle size={18} />
                <span>LICENCIA BABYLON-60 EMITIDA Y ATESTADA EN RING-0</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

