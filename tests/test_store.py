import pytest
from datetime import datetime
from pathlib import Path
from mycelium.models import WikiPage, LogEntry, Edge, UpdateLogEntry
from mycelium.store import WikiStore, LogStore

def test_wiki_store_save_and_get(tmp_path):
    store = WikiStore(tmp_path / "wiki")
    
    page = WikiPage(
        slug="test-page",
        title="Test Page",
        content="This is the content.",
        created=datetime(2026, 5, 10, 10, 0, 0),
        last_updated=datetime(2026, 5, 10, 10, 0, 0),
        version=1,
        confidence=0.9,
        decay_score=0.95,
        importance=0.8,
        tags=["test"],
        related=[Edge(target="other-page", relation="causes", weight=0.5)],
        update_log=[
            UpdateLogEntry(
                version=1,
                date=datetime(2026, 5, 10, 10, 0, 0),
                session_id="ses-123",
                trigger="manual",
                discrepancy_score=0.0,
                reason="Initial creation",
                previous_confidence=0.0,
                new_confidence=0.9
            )
        ]
    )
    
    store.save(page)
    
    loaded = store.get("test-page")
    assert loaded.slug == "test-page"
    assert loaded.title == "Test Page"
    assert loaded.content == "This is the content."
    assert loaded.version == 1
    assert loaded.confidence == 0.9
    assert len(loaded.related) == 1
    assert loaded.related[0].target == "other-page"
    assert len(loaded.update_log) == 1
    assert loaded.update_log[0].session_id == "ses-123"

def test_wiki_store_list_all(tmp_path):
    store = WikiStore(tmp_path / "wiki")
    
    store.save(WikiPage(slug="page1", title="1", content="", created=datetime.now(), last_updated=datetime.now(), version=1, confidence=1.0, decay_score=1.0, importance=1.0))
    store.save(WikiPage(slug="page2", title="2", content="", created=datetime.now(), last_updated=datetime.now(), version=1, confidence=1.0, decay_score=1.0, importance=1.0))
    store.save_index("# Index")
    
    pages = store.list_all()
    assert len(pages) == 2
    slugs = [p.slug for p in pages]
    assert "page1" in slugs
    assert "page2" in slugs

def test_wiki_store_archive(tmp_path):
    store = WikiStore(tmp_path / "wiki")
    store.save(WikiPage(slug="archive-me", title="A", content="", created=datetime.now(), last_updated=datetime.now(), version=1, confidence=1.0, decay_score=1.0, importance=1.0))
    assert store.exists("archive-me")
    store.archive("archive-me")
    assert not store.exists("archive-me")
    assert (tmp_path / "wiki" / "_archive" / "archive-me.md").exists()

def test_wiki_store_labile(tmp_path):
    store = WikiStore(tmp_path / "wiki")
    store.save(WikiPage(slug="labile-page", title="L", content="", created=datetime.now(), last_updated=datetime.now(), version=1, confidence=1.0, decay_score=1.0, importance=1.0))
    
    store.mark_labile("labile-page", "ses-123")
    assert (tmp_path / "labile" / "labile-page.ses-123.md").exists()
    page = store.get("labile-page")
    assert page.labile
    assert page.labile_session == "ses-123"
    
    store.resolve_labile("labile-page", "ses-123")
    assert not (tmp_path / "labile" / "labile-page.ses-123.md").exists()
    page = store.get("labile-page")
    assert not page.labile
    assert page.labile_session is None

def test_log_store_append_and_get(tmp_path):
    store = LogStore(tmp_path / "logs")
    
    entry = LogEntry(
        entry_id="2026-05-10#Entry 1",
        session_id="ses-123",
        timestamp=datetime(2026, 5, 10, 10, 0, 0),
        content="User said hello.",
        importance=0.5,
        tags=["test"],
        status="raw",
        memory_type="user_profile",
        durability="durable",
        consolidated=False,
        decay_score=1.0
    )
    
    store.append(entry)
    
    unconsolidated = store.get_unconsolidated()
    assert len(unconsolidated) == 1
    assert unconsolidated[0].content == "User said hello."
    assert unconsolidated[0].session_id == "ses-123"
    assert unconsolidated[0].memory_type == "user_profile"
    assert unconsolidated[0].durability == "durable"
    assert not unconsolidated[0].consolidated

def test_log_store_mark_consolidated(tmp_path):
    store = LogStore(tmp_path / "logs")
    
    entry = LogEntry(
        entry_id="2026-05-10#Entry 1",
        session_id="ses-123",
        timestamp=datetime(2026, 5, 10, 10, 0, 0),
        content="User said hello.",
        importance=0.5,
        tags=["test"],
        status="raw",
        consolidated=False,
        decay_score=1.0
    )
    
    store.append(entry)
    store.mark_consolidated(["2026-05-10#Entry 1"])
    
    unconsolidated = store.get_unconsolidated()
    assert len(unconsolidated) == 0

def test_log_store_update_decay(tmp_path):
    store = LogStore(tmp_path / "logs")
    
    entry = LogEntry(
        entry_id="2026-05-10#Entry 1",
        session_id="ses-123",
        timestamp=datetime(2026, 5, 10, 10, 0, 0),
        content="User said hello.",
        importance=0.5,
        tags=["test"],
        status="raw",
        consolidated=False,
        decay_score=1.0
    )
    
    store.append(entry)
    store.update_decay("2026-05-10#Entry 1", 0.75)
    
    unconsolidated = store.get_unconsolidated()
    assert len(unconsolidated) == 1
    assert unconsolidated[0].decay_score == 0.75
