# api/webhook_handler.py
import stripe
import os
import json
from fastapi import APIRouter, Request, HTTPException
from api.database import (
    get_db, upgrade_user_tier,
    downgrade_user_tier, log_event
)

router = APIRouter()
stripe.api_key = os.getenv("STRIPE_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

TIER_LIMITS = {
    "free":         10,
    "starter":     500,
    "professional": 5000,
}

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    db = get_db()
    try:
        # Subscription activated
        if event["type"] == "customer.subscription.created":
            sub = event["data"]["object"]
            customer = stripe.Customer.retrieve(sub["customer"])
            email = customer["email"]
            tier = resolve_tier(sub["items"]["data"][0]["price"]["id"])
            upgrade_user_tier(email, tier, TIER_LIMITS[tier], db)
            log_event(email, "subscription_created", {"tier": tier}, db)

        # Payment succeeded (renewal)
        elif event["type"] == "invoice.payment_succeeded":
            invoice = event["data"]["object"]
            customer = stripe.Customer.retrieve(invoice["customer"])
            email = customer["email"]
            log_event(email, "payment_succeeded", {"amount": invoice["amount_paid"]}, db)

        # Subscription cancelled
        elif event["type"] == "customer.subscription.deleted":
            sub = event["data"]["object"]
            customer = stripe.Customer.retrieve(sub["customer"])
            email = customer["email"]
            downgrade_user_tier(email, "free", TIER_LIMITS["free"], db)
            log_event(email, "subscription_cancelled", {}, db)
            
    finally:
        db.close()

    return {"status": "ok"}

def resolve_tier(price_id: str) -> str:
    return {
        os.getenv("STRIPE_PRICE_STARTER"):      "starter",
        os.getenv("STRIPE_PRICE_PROFESSIONAL"): "professional",
    }.get(price_id, "free")
