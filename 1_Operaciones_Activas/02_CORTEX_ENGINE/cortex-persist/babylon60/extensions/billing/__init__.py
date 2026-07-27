# [C5-REAL] Exergy-Maximized
"""CORTEX Billing Gateway & Causal Metering Extension."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from babylon60.extensions.billing.gateway import StripeBillingGateway
    from babylon60.extensions.billing.metering import CausalMetering
    from babylon60.extensions.billing.models import BillingEvent, FailureType, StripeInvoice

__all__ = [
    "BillingEvent",
    "FailureType",
    "StripeInvoice",
    "StripeBillingGateway",
    "CausalMetering",
]

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "BillingEvent": ("babylon60.extensions.billing.models", "BillingEvent"),
    "FailureType": ("babylon60.extensions.billing.models", "FailureType"),
    "StripeInvoice": ("babylon60.extensions.billing.models", "StripeInvoice"),
    "StripeBillingGateway": ("babylon60.extensions.billing.gateway", "StripeBillingGateway"),
    "CausalMetering": ("babylon60.extensions.billing.metering", "CausalMetering"),
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        module_path, attr_name = _LAZY_IMPORTS[name]
        module = importlib.import_module(module_path)
        value = getattr(module, attr_name)
        globals()[name] = value
        return value
    raise AttributeError(f"module 'babylon60.extensions.billing' has no attribute {name!r}")
