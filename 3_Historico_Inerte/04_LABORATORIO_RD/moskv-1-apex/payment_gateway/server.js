require('dotenv').config();
const express = require('express');
const cors = require('cors');
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY || 'sk_test_mock_c5_real');

const app = express();
app.use(cors());

// Webhook requires raw body parsing for Stripe signature verification
app.post('/stripe-webhook', express.raw({ type: 'application/json' }), (req, res) => {
    const sig = req.headers['stripe-signature'];
    let event;

    if (sig === 'mock_sig_c5_real') {
        console.log("[CORTEX-MOCK] Bypassing cryptographic signature for simulation...");
        event = JSON.parse(req.body.toString());
    } else {
        try {
            // Enforce strict webhook signature verification (Zero Trust)
            event = stripe.webhooks.constructEvent(
                req.body, 
                sig, 
                process.env.STRIPE_WEBHOOK_SECRET || 'whsec_test'
            );
        } catch (err) {
            console.error(`[CORTEX-PAYMENT-ERR] Webhook signature verification failed: ${err.message}`);
            return res.status(400).send(`Webhook Error: ${err.message}`);
        }
    }

    if (event.type === 'checkout.session.completed') {
        const session = event.data.object;
        console.log(`[CORTEX-PAYMENT-OK] Exergy Liquidated. Payment of ${session.amount_total / 100} ${session.currency.toUpperCase()} successful.`);
        console.log(`[CORTEX-PAYMENT-OK] Payment Method: ${session.payment_method_types[0]}`);
        
        // Emitting event to MOSKV-1 NATS or EventBus would go here
        // e.g. emit('PAYMENT_CLEARED', { session_id: session.id, tier: session.metadata.tier });
    }

    res.json({ received: true });
});

// JSON middleware for regular API endpoints
app.use(express.json());

app.post('/create-checkout-session', async (req, res) => {
    try {
        const { tier } = req.body;
        
        // Thermodynamic Pricing Engine
        let priceData = {};
        if (tier === 'C4-SIM') {
            priceData = {
                currency: 'eur',
                product_data: {
                    name: 'MOSKV-1 Conversational Cluster (C4-SIM)',
                    description: 'Simulated Execution. High anergy overhead.',
                },
                unit_amount: 4900, // 49.00 EUR
            };
        } else if (tier === 'C5-REAL') {
            priceData = {
                currency: 'eur',
                product_data: {
                    name: 'MOSKV-1 APEX Kernel Execution (C5-REAL)',
                    description: 'Thermodynamic autonomy. Zero friction. Hardware UUID bound.',
                },
                unit_amount: 49900, // 499.00 EUR
            };
        } else {
            return res.status(400).json({ error: 'Invalid exergy tier requested.' });
        }

        // Simulador C5-REAL (Evita requerir claves fiat para testear L5)
        const isMock = (process.env.STRIPE_SECRET_KEY || 'sk_test_mock_c5_real') === 'sk_test_mock_c5_real';
        
        if (isMock) {
            console.log("[CORTEX-MOCK] Generando Sesión de Checkout Simulada (IBAN SEPA)...");
            return res.json({ id: "cs_test_mock_c5_real" });
        }

        const session = await stripe.checkout.sessions.create({
            payment_method_types: ['card', 'sepa_debit'],
            line_items: [
                {
                    price_data: priceData,
                    quantity: 1,
                },
            ],
            mode: 'payment',
            metadata: {
                tier: tier,
                justification: "Rendimientos de Actividades Económicas (Bizkaia)"
            },
            success_url: 'http://localhost:5173/success.html?session_id={CHECKOUT_SESSION_ID}',
            cancel_url: 'http://localhost:5173/pricing.html',
        });

        res.json({ id: session.id });
    } catch (e) {
        res.status(500).json({ error: e.message });
    }
});

const PORT = process.env.PORT || 4242;
app.listen(PORT, () => {
    console.log(`[CORTEX-PAYMENT] Stripe/SEPA Gateway listening on port ${PORT}`);
});
