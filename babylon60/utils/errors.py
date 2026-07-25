from __future__ import annotations

__all__ = [
    "CortexError",
    "CriticalSubsystemError",
    "CortexDatabaseError",
    "DatabaseTransactionError",
    "ConnectionPoolExhausted",
    "DBLockError",
    "FactNotFound",
    "ProjectNotFound",
    "ThreadPoolExhausted",
    "LLMRoutingError",
    "LLMProviderError",
    "MemorySubsystemError",
    "ValidationBoundaryError",
    "ConsensusFailure",
    "WriteWorkerError",
    "AuthError",
    "PermissionDeniedError",
    "SovereignViolation",
    "DecryptionPolicyError",
]


class CortexError(Exception):
    pass


class CriticalSubsystemError(CortexError):
    pass


class CortexDatabaseError(CriticalSubsystemError):
    pass


class ConnectionPoolExhausted(CortexDatabaseError):
    pass


class DBLockError(CortexDatabaseError):
    pass


class DatabaseTransactionError(CortexError):
    pass


class FactNotFound(CortexError):
    pass


class ProjectNotFound(CortexError):
    pass


class ThreadPoolExhausted(CortexError):
    pass


class MemorySubsystemError(CortexError):
    pass


class LLMRoutingError(CriticalSubsystemError):
    pass


class LLMProviderError(CortexError):
    pass


class ValidationBoundaryError(CortexError):
    def __init__(self, message: str, validation_errors: list[dict] | None = None):  # type: ignore[type-arg]
        super().__init__(message)
        self.validation_errors = validation_errors or []


class ConsensusFailure(CriticalSubsystemError):
    pass


class WriteWorkerError(CortexDatabaseError):
    pass


class AuthError(CortexError):
    pass


class PermissionDeniedError(AuthError):
    pass


class SovereignViolation(CortexError):
    pass


class DecryptionPolicyError(CortexError, ValueError):
    pass
