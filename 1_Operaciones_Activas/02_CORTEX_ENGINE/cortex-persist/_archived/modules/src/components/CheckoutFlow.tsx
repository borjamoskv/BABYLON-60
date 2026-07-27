import React, { useState, useEffect } from 'react';
import CheckoutModal from './CheckoutModal';

export default function CheckoutFlow() {
  const [isOpen, setIsOpen] = useState(false);
  const [plan, setPlan] = useState('Pro Plan');
  const [price, setPrice] = useState('49');

  useEffect(() => {
    const handleOpenCheckout = (e: CustomEvent) => {
      setPlan(e.detail?.plan || 'Pro Plan');
      setPrice(e.detail?.price || '49');
      setIsOpen(true);
    };

    window.addEventListener('open-checkout', handleOpenCheckout as EventListener);

    return () => {
      window.removeEventListener('open-checkout', handleOpenCheckout as EventListener);
    };
  }, []);

  return (
    <CheckoutModal
      isOpen={isOpen}
      onClose={() => setIsOpen(false)}
      planName={plan}
      planPrice={price}
    />
  );
}
