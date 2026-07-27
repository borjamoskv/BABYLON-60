CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE memories (
    id SERIAL PRIMARY KEY,
    user_id TEXT,
    agent_id TEXT,
    content TEXT,
    embedding vector(384),
    created_at TIMESTAMP DEFAULT NOW()
);
