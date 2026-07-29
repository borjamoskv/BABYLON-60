# C5-REAL EXERGY CERTIFIED
"""Configuration module for BABYLON-60 Core and Extensions."""

import os

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_test_mock_123456789")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_mock_123456789")
STRIPE_PRICE_TABLE = {
    "starter": os.getenv("STRIPE_PRICE_STARTER", "price_mock_starter"),
    "pro": os.getenv("STRIPE_PRICE_PRO", "price_mock_pro"),
    "enterprise": os.getenv("STRIPE_PRICE_ENTERPRISE", "price_mock_enterprise"),
}
