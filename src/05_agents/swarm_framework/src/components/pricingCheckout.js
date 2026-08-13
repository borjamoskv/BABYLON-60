// C5-REAL EXERGY CERTIFIED
export function initPricingCheckout() {
  const modal = document.getElementById('checkout-modal');
  if (!modal) return;

  const closeBtn = modal.querySelector('.modal-close');
  const confirmBtn = document.getElementById('btn-checkout-confirm');
  const planNameEl = document.getElementById('checkout-plan-name');
  const planPriceEl = document.getElementById('checkout-plan-price');
  const emailInput = document.getElementById('checkout-email');
  const amountInput = document.getElementById('checkout-custom-amount');

  let currentPlan = null;

  const planDetails = {
    sprint: { name: 'Sprint Adversarial', price: '€25k' },
    council: { name: 'Sovereign Council', price: '€8k/mo' },
    cert: { name: 'Pre-deploy Cert', price: '€15k' }
  };

  document.querySelectorAll('.plan-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      currentPlan = e.target.getAttribute('data-plan');
      const details = planDetails[currentPlan];
      if (details) {
        planNameEl.textContent = details.name;
        planPriceEl.textContent = details.price;
        modal.classList.add('active');
      }
    });
  });

  closeBtn.addEventListener('click', () => {
    modal.classList.remove('active');
  });

  // Also close on overlay click
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      modal.classList.remove('active');
    }
  });

  confirmBtn.addEventListener('click', async () => {
    if (!currentPlan) return;

    const email = emailInput.value.trim();
    const customAmountStr = amountInput ? amountInput.value.trim() : "";
    const parsedAmount = parseInt(customAmountStr, 10);

    // PWYW - Free Tier Bypass
    if (!isNaN(parsedAmount) && parsedAmount === 0) {
      window.location.href = '/success.html?session_id=PWYW_FREE_TIER_GRANTED';
      return;
    }

    const btnTextEl = confirmBtn.querySelector('.btn-text');
    const originalText = btnTextEl.textContent;
    btnTextEl.textContent = 'Iniciando conexión...';
    confirmBtn.disabled = true;
    confirmBtn.style.opacity = '0.7';

    try {
      const payload = { plan: currentPlan, email: email || undefined };
      if (!isNaN(parsedAmount) && parsedAmount > 0) {
        payload.customAmount = parsedAmount;
      }

      const res = await fetch('/api/create-checkout-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (res.ok && data.url) {
        window.location.href = data.url;
      } else {
        alert('Error: ' + (data.error || 'Failed to initialize checkout.'));
      }
    } catch (error) {
      console.error(error);
      alert('Error de red. Inténtalo de nuevo.');
    } finally {
      btnTextEl.textContent = originalText;
      confirmBtn.disabled = false;
      confirmBtn.style.opacity = '1';
    }
  });
}

// Auto-init
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initPricingCheckout);
} else {
  initPricingCheckout();
}
