from app.core.db import get_connection
from app.core.embeddings import embed
def add_memory(user_id, agent_id, content):
    conn = get_connection()
    cur = conn.cursor()
    vector = embed(content)
    cur.execute("""
        INSERT INTO memories (user_id, agent_id, content, embedding)
        VALUES (%s, %s, %s, %s)
    """, (user_id, agent_id, content, vector))
    conn.commit()
def query_memory(user_id, query):
    from app.core.retrieval import search_memories
    vector = embed(query)
    return search_memories(user_id, vector)

def list_memories(user_id, agent_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, content, created_at
        FROM memories
        WHERE user_id = %s AND agent_id = %s
        ORDER BY created_at DESC
    """, (user_id, agent_id))
    return [{"id": row[0], "content": row[1], "created_at": row[2].isoformat() if row[2] else None} for row in cur.fetchall()]

def query_memory_detailed(user_id, agent_id, query):
    from app.core.retrieval import search_memories_detailed
    vector = embed(query)
    return search_memories_detailed(user_id, agent_id, vector)

