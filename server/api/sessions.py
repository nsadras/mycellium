from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid

from server.runtime import (
    DEFAULT_MAX_TURNS,
    append_turn,
    ensure_session_record,
    flush_session_episode,
    get_mem,
    load_meta,
    recent_thread_context,
    save_meta,
)

router = APIRouter()

class SessionCreate(BaseModel):
    query: Optional[str] = "New session"

class SessionUpdate(BaseModel):
    query: str

class ChatRequest(BaseModel):
    message: str

class Message(BaseModel):
    role: str
    content: str

class SessionInfo(BaseModel):
    id: str
    query: str
    transcript: List[Message]

@router.get("/", response_model=List[dict])
async def list_sessions():
    meta = load_meta()
    for session_id, record in meta.items():
        ensure_session_record(record, session_id)
    save_meta(meta)
    return [{"id": k, "query": v["query"]} for k, v in meta.items()]

@router.post("/", response_model=dict)
async def create_session(req: SessionCreate):
    session_id = str(uuid.uuid4())[:8]
    meta = load_meta()
    meta[session_id] = {"query": req.query, "transcript": []}
    ensure_session_record(meta[session_id], session_id)
    save_meta(meta)
    return {"id": session_id, "query": req.query}

@router.get("/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    meta = load_meta()
    if session_id not in meta:
        raise HTTPException(status_code=404, detail="Session not found")
    ensure_session_record(meta[session_id], session_id)
    save_meta(meta)
    return {"id": session_id, **meta[session_id]}

@router.patch("/{session_id}", response_model=dict)
async def update_session(session_id: str, req: SessionUpdate):
    meta = load_meta()
    if session_id not in meta:
        raise HTTPException(status_code=404, detail="Session not found")
    record = ensure_session_record(meta[session_id], session_id)
    name = req.query.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Session name cannot be empty")
    record["query"] = name
    save_meta(meta)
    return {"id": session_id, "query": name}

@router.post("/{session_id}/chat")
async def chat(session_id: str, req: ChatRequest):
    meta = load_meta()
    if session_id not in meta:
        raise HTTPException(status_code=404, detail="Session not found")
    
    record = ensure_session_record(meta[session_id], session_id)
    episode_id = record["active_episode"]["id"]
    mem = get_mem()
    thread_context = recent_thread_context(record)
    retrieval_query = (
        f"CHAT TOPIC:\n{record['query']}\n\n"
        f"RECENT THREAD:\n{thread_context or '(no prior turns)'}\n\n"
        f"USER MESSAGE:\n{req.message}"
    )
    
    loaded_pages = await mem.load_context(retrieval_query, session_id=episode_id)
    memory_context = ""
    if loaded_pages:
        blocks = []
        for page in loaded_pages:
            header = f"=== MEMORY: {page.title} (confidence: {page.confidence:.2f}, v{page.version}) ==="
            blocks.append(f"{header}\n{page.content}")
        memory_context = "\n\n".join(blocks) + "\n\n=== END MEMORY ==="

    system_prompt = (
        "You are a helpful and intelligent AI assistant. "
        "You have access to a long-term memory wiki that contains information you've learned from previous interactions. "
        "Use the following memory context and recent thread context to inform your response if relevant.\n\n"
        f"MEMORY CONTEXT:\n{memory_context or 'No relevant long-term memory context was found.'}\n\n"
        f"RECENT THREAD:\n{thread_context or '(no prior turns)'}"
    )
    response_text = await mem.llm.call(system=system_prompt, user=req.message)

    append_turn(meta, session_id, req.message, response_text)
    turn_count = int(meta[session_id]["active_episode"].get("turn_count", 0))
    save_meta(meta)
    auto_flush = None
    if turn_count >= DEFAULT_MAX_TURNS:
        auto_flush = await flush_session_episode(session_id, reason="max_turns")

    return {
        "response": response_text,
        "loaded_pages": [p.slug for p in loaded_pages],
        "episode_id": episode_id,
        "auto_flush": auto_flush,
    }
