from __future__ import annotations
__all__ = ['CortexError', 'CriticalSubsystemError', 'CortexDatabaseError', 'DatabaseTransactionError', 'ConnectionPoolExhausted', 'DBLockError', 'FactNotFound', 'ProjectNotFound', 'ThreadPoolExhausted', 'LLMRoutingError', 'LLMProviderError', 'MemorySubsystemError', 'ValidationBoundaryError', 'ConsensusFailure', 'WriteWorkerError', 'AuthError', 'PermissionDeniedError', 'SovereignViolation', 'DecryptionPolicyError']

class CortexError(Exception):

class CriticalSubsystemError(CortexError):

class CortexDatabaseError(CriticalSubsystemError):

class ConnectionPoolExhausted(CortexDatabaseError):

class DBLockError(CortexDatabaseError):

class DatabaseTransactionError(CortexError):

class FactNotFound(CortexError):

class ProjectNotFound(CortexError):

class ThreadPoolExhausted(CortexError):

class MemorySubsystemError(CortexError):

class LLMRoutingError(CriticalSubsystemError):

class LLMProviderError(CortexError):

class ValidationBoundaryError(CortexError):

    def __init__(self, message: str, validation_errors: list[dict] | None=None):
        super().__init__(message)
        self.validation_errors = validation_errors or []

class ConsensusFailure(CriticalSubsystemError):

class WriteWorkerError(CortexDatabaseError):

class AuthError(CortexError):

class PermissionDeniedError(AuthError):

class SovereignViolation(CortexError):

class DecryptionPolicyError(CortexError, ValueError):