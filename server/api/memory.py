from fastapi import APIRouter, HTTPException
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

from mycelium.models import UpdateLogEntry
from server.runtime import (
    clear_memory_store,
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


class WikiPageUpdate(BaseModel):
    title: str
    content: str
    tags: list[str] = []
    confidence: float | None = None
    importance: float | None = None

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
            "importance": page.importance,
            "tags": page.tags,
            "source_log_entries": page.source_log_entries,
            "related": [{"target": r.target, "relation": r.relation} for r in page.related],
            "update_log": [{"version": u.version, "reason": u.reason, "date": u.date.isoformat()} for u in page.update_log]
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Page not found")


@router.put("/wiki/{slug}")
async def update_wiki_page(slug: str, req: WikiPageUpdate):
    mem = get_mem()
    try:
        page = mem.wiki.get(slug)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Page not found")

    previous_confidence = page.confidence
    page.title = req.title.strip() or page.title
    page.content = req.content
    page.tags = req.tags
    if req.confidence is not None:
        page.confidence = max(0.0, min(1.0, req.confidence))
    if req.importance is not None:
        page.importance = max(0.0, min(1.0, req.importance))
    page.version += 1
    page.last_updated = datetime.now()
    page.update_log.append(
        UpdateLogEntry(
            version=page.version,
            date=page.last_updated,
            session_id="manual",
            trigger="manual",
            discrepancy_score=0.0,
            reason="Manual edit from web UI",
            previous_confidence=previous_confidence,
            new_confidence=page.confidence,
        )
    )
    mem.wiki.save(page)
    return {
        "slug": page.slug,
        "title": page.title,
        "content": page.content,
        "version": page.version,
        "confidence": page.confidence,
        "importance": page.importance,
        "tags": page.tags,
        "source_log_entries": page.source_log_entries,
        "related": [{"target": r.target, "relation": r.relation} for r in page.related],
        "update_log": [{"version": u.version, "reason": u.reason, "date": u.date.isoformat()} for u in page.update_log],
    }

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


@router.post("/dev/clear")
async def clear_memory():
    return clear_memory_store()


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
