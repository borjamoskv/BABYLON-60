from app.core.db import get_connection
def search_memories(user_id, embedding, limit=5):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT content
        FROM memories
        WHERE user_id = %s
        ORDER BY embedding <-> %s::vector
        LIMIT %s
    """, (user_id, embedding, limit))
    return [row[0] for row in cur.fetchall()]

def search_memories_detailed(user_id, agent_id, embedding, limit=5):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, content, created_at, (1 - (embedding <=> %s::vector)) as similarity
        FROM memories
        WHERE user_id = %s AND agent_id = %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """, (embedding, user_id, agent_id, embedding, limit))
    return [{"id": row[0], "content": row[1], "created_at": row[2].isoformat() if row[2] else None, "similarity": float(row[3]) if row[3] is not None else 1.0} for row in cur.fetchall()]

