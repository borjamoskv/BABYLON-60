// Stripe Client Logic for MOSKV-1 Monetization Matrix

// Replace with the actual Stripe Publishable Key
const stripe = Stripe('pk_test_mock_c5_real_publishable_key'); 

document.getElementById('btn-c4').addEventListener('click', () => {
    initiateCheckout('C4-SIM');
});

document.getElementById('btn-c5').addEventListener('click', () => {
    initiateCheckout('C5-REAL');
});

async function initiateCheckout(tier) {
    try {
        console.log(`[CORTEX-UI] Iniciando pasarela SEPA/Stripe para tier: ${tier}`);
        
        // Disable buttons to prevent duplicate requests
        document.getElementById('btn-c4').disabled = true;
        document.getElementById('btn-c5').disabled = true;

        const response = await fetch('http://localhost:4242/create-checkout-session', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ tier: tier }),
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.error || 'Network response was not ok');
        }

        const session = await response.json();

        // Simulador C5-REAL
        if (session.id === "cs_test_mock_c5_real") {
            alert(`[CORTEX-MOCK] Simulando redirección a Stripe para Tier: ${tier}...\n¡Cobro por SEPA IBAN procesado con éxito!`);
            
            // Simular webhook de Stripe golpeando a nuestro backend
            fetch('http://localhost:4242/stripe-webhook', {
                method: 'POST',
                headers: { 
                    'stripe-signature': 'mock_sig_c5_real', 
                    'Content-Type': 'application/json' 
                },
                body: JSON.stringify({
                    type: 'checkout.session.completed',
                    data: { 
                        object: { 
                            id: session.id, 
                            amount_total: tier === 'C5-REAL' ? 49900 : 4900, 
                            currency: 'eur', 
                            payment_method_types: ['sepa_debit'] 
                        } 
                    }
                })
            }).catch(e => console.error("Webhook error:", e));
            return;
        }

        // Redirect to Stripe Checkout (handles Card & SEPA IBAN)
        const result = await stripe.redirectToCheckout({
            sessionId: session.id,
        });

        if (result.error) {
            alert(`[CORTEX-PAYMENT-ERR] ${result.error.message}`);
        }
    } catch (error) {
        console.error('[CORTEX-PAYMENT-ERR]', error);
        alert(`Error al contactar con la pasarela: ${error.message}`);
    } finally {
        document.getElementById('btn-c4').disabled = false;
        document.getElementById('btn-c5').disabled = false;
    }
}
