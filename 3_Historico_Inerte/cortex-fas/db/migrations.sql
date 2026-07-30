-- migrations.sql

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users
CREATE TABLE IF NOT EXISTS users (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email            VARCHAR(255) UNIQUE NOT NULL,
    api_key          VARCHAR(64)  UNIQUE NOT NULL DEFAULT encode(gen_random_bytes(32), 'hex'),
    tier             VARCHAR(20)  NOT NULL DEFAULT 'free',
    requests_used    INTEGER NOT NULL DEFAULT 0,
    requests_limit   INTEGER NOT NULL DEFAULT 10,
    activated_at     TIMESTAMP,
    last_request_at  TIMESTAMP,
    created_at       TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Usage logs
CREATE TABLE IF NOT EXISTS usage_logs (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID REFERENCES users(id) ON DELETE CASCADE,
    endpoint     VARCHAR(50) NOT NULL,
    energy_score FLOAT,
    lyapunov     FLOAT,
    regime       VARCHAR(30),
    created_at   TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Events (Stripe + lifecycle)
CREATE TABLE IF NOT EXISTS events (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_email VARCHAR(255) NOT NULL,
    event_type VARCHAR(50)  NOT NULL,
    payload    JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_usage_user     ON usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_created  ON usage_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_events_email   ON events(user_email);
CREATE INDEX IF NOT EXISTS idx_events_type    ON events(event_type);

-- Retention view (7-day)
CREATE OR REPLACE VIEW retention_7d AS
SELECT
    u.id,
    u.email,
    u.tier,
    u.activated_at,
    COUNT(l.id)                                    AS total_requests,
    MAX(l.created_at)                              AS last_seen,
    (MAX(l.created_at) > NOW() - INTERVAL '7 days') AS retained
FROM users u
LEFT JOIN usage_logs l ON l.user_id = u.id
WHERE u.activated_at IS NOT NULL
GROUP BY u.id;

-- Conversion view (free → paid)
CREATE OR REPLACE VIEW conversion_funnel AS
SELECT
    COUNT(*) FILTER (WHERE tier = 'free')         AS free_users,
    COUNT(*) FILTER (WHERE tier != 'free')        AS paid_users,
    ROUND(
        COUNT(*) FILTER (WHERE tier != 'free')::numeric
        / NULLIF(COUNT(*), 0) * 100, 2
    )                                             AS conversion_pct
FROM users;
