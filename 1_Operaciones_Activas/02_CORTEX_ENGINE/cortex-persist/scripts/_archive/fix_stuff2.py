f1 = "~/30_BABYLON60/babylon60/engine/__init__.py"
with open(f1) as f:
    c1 = f.read()

# Instead of complex regex, let's just do a string replace since they are identical duplicates! Wait, are they?
# the previous ruff output showed:
# 234 |                 raise RuntimeError(f"FAIL-CLOSED: HealthGuardAdapter failed: {e}") from e
# 235 |             logger.debug("HealthGuardAdapter unavailable: %s", e)
# 236 |         except Exception as e:
# 237 |             raise RuntimeError(f"FAIL-CLOSED: HealthGuardAdapter failed: {e}") from e

c1 = c1.replace(
    '            logger.debug("HealthGuardAdapter unavailable: %s", e)\n        except Exception as e:\n            raise RuntimeError(f"FAIL-CLOSED: HealthGuardAdapter failed: {e}") from e',
    '            raise RuntimeError(f"FAIL-CLOSED: HealthGuardAdapter failed: {e}") from e',
)
c1 = c1.replace(
    '            logger.debug("ContradictionGuardAdapter unavailable: %s", e)\n        except Exception as e:\n            raise RuntimeError(f"FAIL-CLOSED: ContradictionGuardAdapter failed: {e}") from e',
    '            raise RuntimeError(f"FAIL-CLOSED: ContradictionGuardAdapter failed: {e}") from e',
)
c1 = c1.replace(
    '            logger.debug("VerifierGuardAdapter unavailable: %s", e)\n        except Exception as e:\n            raise RuntimeError(f"FAIL-CLOSED: VerifierGuardAdapter failed: {e}") from e',
    '            raise RuntimeError(f"FAIL-CLOSED: VerifierGuardAdapter failed: {e}") from e',
)
c1 = c1.replace(
    '            logger.debug("ZKGuardAdapter unavailable: %s", e)\n        except Exception as e:\n            raise RuntimeError(f"FAIL-CLOSED: ZKGuardAdapter failed: {e}") from e',
    '            raise RuntimeError(f"FAIL-CLOSED: ZKGuardAdapter failed: {e}") from e',
)
c1 = c1.replace(
    '            logger.debug("LedgerCheckpointHook unavailable: %s", e)\n        except Exception as e:\n            raise RuntimeError(f"FAIL-CLOSED: LedgerCheckpointHook failed: {e}") from e',
    '            raise RuntimeError(f"FAIL-CLOSED: LedgerCheckpointHook failed: {e}") from e',
)
c1 = c1.replace(
    '            logger.debug("SignalEmitHook unavailable: %s", e)\n        except Exception as e:\n            raise RuntimeError(f"FAIL-CLOSED: SignalEmitHook failed: {e}") from e',
    '            raise RuntimeError(f"FAIL-CLOSED: SignalEmitHook failed: {e}") from e',
)
c1 = c1.replace(
    '            logger.debug("EpistemicBreakerHook unavailable: %s", e)\n        except Exception as e:\n            raise RuntimeError(f"FAIL-CLOSED: EpistemicBreakerHook failed: {e}") from e',
    '            raise RuntimeError(f"FAIL-CLOSED: EpistemicBreakerHook failed: {e}") from e',
)

with open(f1, "w") as f:
    f.write(c1)
