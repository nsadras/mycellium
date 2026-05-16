from fastapi import APIRouter, HTTPException
from pathlib import Path

from pydantic import BaseModel

from server.runtime import (
    flush_idle_episodes,
    flush_session_episode,
    get_mem,
    resolve_session_reconsolidation,
    run_decay,
    run_dream as run_dream_process,
)

router = APIRouter()


class FlushRequest(BaseModel):
    session_id: str | None = None


class IdleFlushRequest(BaseModel):
    idle_minutes: int = 20
    max_turns: int = 25
    force: bool = False

@router.get("/wiki")
async def list_wiki():
    mem = get_mem()
    pages = mem.wiki.list_all()
    return [{"slug": p.slug, "title": p.title, "confidence": p.confidence, "tags": p.tags} for p in pages]

@router.get("/wiki/{slug}")
async def get_wiki_page(slug: str):
    mem = get_mem()
    try:
        page = mem.wiki.get(slug)
        # Convert dataclass to dict
        return {
            "slug": page.slug,
            "title": page.title,
            "content": page.content,
            "version": page.version,
            "confidence": page.confidence,
            "tags": page.tags,
            "related": [{"target": r.target, "relation": r.relation} for r in page.related],
            "update_log": [{"version": u.version, "reason": u.reason, "date": u.date.isoformat()} for u in page.update_log]
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Page not found")

@router.get("/logs")
async def list_logs():
    logs_dir = Path("./mnemos_store/logs")
    if not logs_dir.exists():
        return []
    return [f.name for f in logs_dir.glob("*.md")]

@router.get("/logs/{filename}")
async def get_log_content(filename: str):
    if "/" in filename or "\\" in filename or not filename.endswith(".md"):
        raise HTTPException(status_code=400, detail="Invalid log filename")
    log_path = Path("./mnemos_store/logs") / filename
    if not log_path.exists():
        raise HTTPException(status_code=404, detail="Log not found")
    with open(log_path, "r", encoding="utf-8") as f:
        return {"filename": filename, "content": f.read()}

@router.post("/dream")
async def run_dream():
    return await run_dream_process()


@router.post("/decay")
async def decay():
    return await run_decay()


@router.post("/episodes/flush")
async def flush_episode(req: FlushRequest):
    if not req.session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    result = await flush_session_episode(req.session_id, reason="manual")
    if result["status"] == "missing":
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@router.post("/episodes/flush-idle")
async def flush_idle(req: IdleFlushRequest):
    return await flush_idle_episodes(
        idle_minutes=req.idle_minutes,
        max_turns=req.max_turns,
        force=req.force,
    )


@router.post("/episodes/flush-all")
async def flush_all():
    return await flush_idle_episodes(force=True)


@router.post("/reconsolidation/resolve")
async def resolve_reconsolidation(req: FlushRequest):
    if not req.session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    result = await resolve_session_reconsolidation(req.session_id)
    if result["status"] == "missing":
        raise HTTPException(status_code=404, detail="Session not found")
    return result
