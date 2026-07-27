from fastapi import APIRouter
from app.services.memory_service import add_memory, query_memory, list_memories, query_memory_detailed
router = APIRouter()

@router.post("/add")
def add(payload: dict):
    add_memory(
        payload["user_id"],
        payload["agent_id"],
        payload["content"]
    )
    return {"status": "ok"}

@router.post("/query")
def query(payload: dict):
    results = query_memory(
        payload["user_id"],
        payload["query"]
    )
    return {"results": results}

@router.get("/list")
def list_all(user_id: str, agent_id: str):
    results = list_memories(user_id, agent_id)
    return {"results": results}

@router.post("/chat")
def chat(payload: dict):
    user_id = payload.get("user_id", "dev_user")
    agent_id = payload.get("agent_id", "copilot_v1")
    message = payload.get("message", "")
    use_memory = payload.get("use_memory", True)
    
    retrieved_memories = []
    if use_memory:
        retrieved_memories = query_memory_detailed(user_id, agent_id, message)
    
    # Core mock logic to generate response based on memories
    response_text = ""
    msg_lower = message.lower()
    
    if not use_memory:
        response_text = "I recommend starting with a simple FastAPI skeleton. (No memory context was provided to me, so I don't know your background or project preferences.)"
    else:
        # Check memories to formulate response
        has_infra = any("infra" in m["content"].lower() or "systems" in m["content"].lower() for m in retrieved_memories)
        has_python = any("python" in m["content"].lower() or "rust" in m["content"].lower() for m in retrieved_memories)
        has_dislike = any("dislike" in m["content"].lower() or "long setup" in m["content"].lower() for m in retrieved_memories)
        
        if "project" in msg_lower or "build" in msg_lower or "languages" in msg_lower or "prefer" in msg_lower:
            if has_infra or has_python:
                response_text = "Based on your background as a senior infrastructure engineer and preference for Python/Rust, you should focus on building high-performance lock-free distributed systems and vector database indexing engines (using pgvector)."
                if has_dislike:
                    response_text += " I will keep it simple and skip complex enterprise frameworks to avoid long setup times."
            else:
                response_text = "I recommend starting with a simple FastAPI skeleton, since I couldn't find specific engineering preferences in your memory."
        elif "who am i" in msg_lower or "my name" in msg_lower or "work" in msg_lower or "about me" in msg_lower:
            about_parts = []
            for m in retrieved_memories:
                c = m["content"].lower()
                if "engineer" in c or "work" in c:
                    about_parts.append("you work as an infrastructure engineer")
                elif "python" in c or "rust" in c:
                    about_parts.append("you prefer python/rust")
                elif "dislike" in c or "setup" in c:
                    about_parts.append("you dislike long setups")
            if about_parts:
                response_text = f"According to your retrieved memories, {', '.join(about_parts)}. How can I help you with your systems today?"
            else:
                response_text = "I don't have enough memories about your profile yet. Try telling me something about yourself like: 'I work as a Rust developer.'"
        else:
            response_text = "Hello! I am your stateful memory-enabled agent. "
            if retrieved_memories:
                response_text += f"I recalled some context about you: '{retrieved_memories[0]['content']}'. How can I help you?"
            else:
                response_text += "I don't have any matching memories for this query, so I'm running with default stateless behavior."

    # Auto-remember logic
    auto_stored = False
    stored_content = ""
    triggers = ["remember that", "i like", "i work as", "i prefer", "my preference is", "dislike"]
    if any(trigger in msg_lower for trigger in triggers):
        stored_content = message
        if msg_lower.startswith("remember that "):
            stored_content = message[14:]
        
        # Check if already exists to avoid duplicates
        existing = list_memories(user_id, agent_id)
        if not any(stored_content.lower() in ext["content"].lower() for ext in existing):
            add_memory(user_id, agent_id, stored_content)
            auto_stored = True

    return {
        "response": response_text,
        "retrieved_memories": retrieved_memories,
        "auto_stored": auto_stored,
        "stored_content": stored_content
    }

