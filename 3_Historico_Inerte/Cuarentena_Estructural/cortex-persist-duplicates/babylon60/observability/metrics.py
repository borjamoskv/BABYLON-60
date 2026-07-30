# [C5-REAL] Exergy-Maximized
"""
Observability and Metrics.

Exposes Prometheus metrics for enterprise monitoring of security events,
cryptographic operations, and compliance gates.
"""

from prometheus_client import Counter, Histogram

# --- Security Metrics ---
CORTEX_TAMPER_ATTEMPTS = Counter(
    "cortex_tamper_attempts_total",
    "Number of detected tampering attempts on the ledger",
    ["tenant_id", "reason"],
)

CORTEX_RISK_EVENTS = Counter(
    "cortex_risk_events_total",
    "Number of high or critical risk events blocked by the Memory Firewall",
    ["tenant_id", "risk_level"],
)

# --- Cryptography Metrics ---
CORTEX_KEY_ROTATIONS = Counter(
    "cortex_key_rotations_total", "Number of Master Key rotations performed", ["provider"]
)

CORTEX_SIGNATURES_GENERATED = Counter(
    "cortex_signatures_generated_total", "Total Ed25519 signatures generated"
)

# --- External Trust Anchors ---
CORTEX_REKOR_LOG_SUCCESS = Counter(
    "cortex_rekor_log_success_total", "Successful log entries to Sigstore Rekor"
)

CORTEX_REKOR_LOG_FAILURE = Counter(
    "cortex_rekor_log_failure_total", "Failed log entries to Sigstore Rekor"
)

CORTEX_RFC3161_SUCCESS = Counter(
    "cortex_rfc3161_success_total", "Successful timestamps acquired from RFC3161 TSA"
)

# --- Compliance Pipeline ---
CORTEX_HUMAN_ESCALATIONS = Counter(
    "cortex_human_escalations_total",
    "Number of autonomous decisions escalated to human oversight",
    ["tenant_id"],
)

# --- Performance Metrics ---
CORTEX_BATCH_COMMIT_TIME = Histogram(
    "cortex_batch_commit_time_seconds", "Time spent committing a micro-batch to SQLite and signing"
)
