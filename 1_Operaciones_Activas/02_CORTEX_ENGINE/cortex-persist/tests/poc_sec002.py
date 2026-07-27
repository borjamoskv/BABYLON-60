import logging
import asyncio
import sqlite3
from babylon60.routes.facts import get_causal_chain

logging.getLogger(__name__).info("PoC SEC-002 Generated: Verifying signature of get_causal_chain...")
import inspect

sig = inspect.signature(get_causal_chain)
logging.getLogger(__name__).info("Signature:", sig)
if "tenant_id" not in sig.parameters:
    logging.getLogger(__name__).info("VULNERABILITY CONFIRMED: tenant_id is missing from route parameters.")
else:
    logging.getLogger(__name__).info("NOT VULNERABLE.")
