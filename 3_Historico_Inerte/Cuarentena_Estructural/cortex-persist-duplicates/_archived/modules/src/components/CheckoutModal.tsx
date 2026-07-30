import React, { useState, useEffect } from 'react';

// Make sure to declare Stripe in global scope for TS
declare global {
  interface Window {
    Stripe: any;
  }
}

interface CheckoutModalProps {
  isOpen: boolean;
  onClose: () => void;
  planName: string;
  planPrice: string;
}

export default function CheckoutModal({ isOpen, onClose, planName, planPrice }: CheckoutModalProps) {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [stripeInstance, setStripeInstance] = useState<any>(null);
  const [showStripeEmbed, setShowStripeEmbed] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      if (stripeInstance) {
        stripeInstance.destroy();
        setStripeInstance(null);
      }
      setShowStripeEmbed(false);
      setEmail('');
      setLoading(false);
    }
  }, [isOpen, stripeInstance]);

  const handleSubmit = async () => {
    if (!email) {
      alert("Please enter a valid email address.");
      return;
    }

    setLoading(true);
    const planId = planName.toLowerCase().includes('pro') ? 'pro' : 'enterprise';

    try {
      const response = await fetch('/v1/stripe/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          plan: planId,
          customer_email: email,
          success_url: globalThis.location.origin + "/docs/prototypes/success.html",
          cancel_url: globalThis.location.origin + "/docs/prototypes/cancel.html"
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Stripe initialization failed.');
      }

      const data = await response.json();
      if (data.client_secret && data.publishable_key) {
        const stripe = window.Stripe(data.publishable_key);
        setShowStripeEmbed(true);

        const instance = await stripe.initEmbeddedCheckout({
          clientSecret: data.client_secret,
          appearance: {
            theme: 'night',
            variables: {
              colorPrimary: '#CCFF00',
              colorBackground: '#0F0F0F',
              colorText: '#E0E0E0',
              colorDanger: '#FF5252',
              fontFamily: 'Inter, system-ui, sans-serif',
              borderRadius: '12px'
            }
          }
        });

        setStripeInstance(instance);
        instance.mount('#stripe-checkout-container');
      } else if (data.url) {
        globalThis.location.href = data.url;
      } else {
        throw new Error('No checkout session received.');
      }
    } catch (error: any) {
      console.error("Stripe Checkout Error:", error);
      alert("Payment gateway connection failed. Error: " + error.message);
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="checkout-overlay active" onClick={(e) => {
      if (e.target === e.currentTarget) onClose();
    }}>
      <div className="checkout-modal">
        <div className="checkout-header">
          <div className="checkout-title">Complete your Subscription</div>
          <button className="checkout-close" onClick={onClose}>&times;</button>
        </div>

        <div className="checkout-plan">
          <div className="checkout-plan-name">{planName}</div>
          <div className="checkout-plan-price">${planPrice}</div>
        </div>

        {!showStripeEmbed && (
          <>
            <div className="checkout-form">
              <input
                type="email"
                className="checkout-input"
                placeholder="Email Address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              <input type="text" className="checkout-input" placeholder="Card Number" required />
              <div style={{ display: 'flex', gap: '16px' }}>
                <input type="text" className="checkout-input" placeholder="MM/YY" style={{ flex: 1 }} required />
                <input type="text" className="checkout-input" placeholder="CVC" style={{ flex: 1 }} required />
              </div>
            </div>

            <button
              className="btn btn-primary checkout-btn"
              onClick={handleSubmit}
              disabled={loading}
              style={{ opacity: loading ? 0.7 : 1 }}
            >
              {loading ? (
                <>Processing... <span className="spinner"></span></>
              ) : (
                'Pay Securely →'
              )}
            </button>

            <div className="checkout-footer">
              <span style={{ display: 'inline-block', width: '12px', height: '12px', borderRadius: '50%', background: 'green', marginRight: '4px' }}></span>
              Encrypted & Secured by BABYLON60 Privacy Shield
            </div>
          </>
        )}

        <div id="stripe-checkout-container" style={{ display: showStripeEmbed ? 'block' : 'none', marginTop: '20px' }}></div>
      </div>
    </div>
  );
}
