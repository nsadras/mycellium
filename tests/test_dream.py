import pytest
from unittest.mock import AsyncMock, MagicMock
from mycelium.dream import DreamProcess
from mycelium.models import LogEntry, WikiPage
from mycelium.config import Config
from datetime import datetime

@pytest.fixture
def mock_llm():
    return AsyncMock()

@pytest.fixture
def mock_wiki():
    return MagicMock()

@pytest.fixture
def mock_logs():
    return MagicMock()

@pytest.fixture
def dream_process(mock_llm, mock_wiki, mock_logs):
    config = Config.defaults()
    return DreamProcess(mock_llm, mock_wiki, mock_logs, config)

@pytest.mark.asyncio
async def test_dream_process_run(dream_process, mock_llm, mock_wiki, mock_logs):
    # Setup state
    entry = LogEntry(
        entry_id="2026-05-10#Entry1",
        session_id="ses-123",
        timestamp=datetime.now(),
        content="New experience",
        importance=0.8,
        status="raw"
    )
    mock_logs.get_unconsolidated.return_value = [entry]
    mock_wiki.get_index.return_value = "# Index"
    
    # LLM responses
    mock_llm.call_structured.side_effect = [
        # Identify
        [{"page": "new-page", "action": "create"}, {"page": "existing-page", "action": "update"}],
        # Rewrite existing
        {"title": "Existing Title", "content": "Updated content", "confidence": 0.9, "importance": 0.8},
        # Rewrite new
        {"title": "New Title", "content": "New content", "confidence": 0.8, "importance": 0.7},
        # Update index
        {"index": "# Updated Index"}
    ]
    
    mock_wiki.exists.side_effect = lambda slug: slug == "existing-page"
    
    existing = WikiPage(
        slug="existing-page", title="Existing", content="Old",
        created=datetime.now(), last_updated=datetime.now(),
        version=1, confidence=0.8, decay_score=1.0, importance=0.5
    )
    mock_wiki.get.return_value = existing
    
    report = await dream_process.run(strategy="full", conflict_policy="override")
    
    assert report.pages_updated == 1
    assert report.pages_created == 1
    assert report.entries_consolidated == 1
    
    # Verify saves
    assert mock_wiki.save.call_count == 2
    saved_pages = [call.args[0] for call in mock_wiki.save.call_args_list]
    assert all("2026-05-10#Entry1" in page.source_log_entries for page in saved_pages)
    mock_wiki.save_index.assert_called_once_with("# Updated Index")
    mock_logs.mark_consolidated.assert_called_once_with(["2026-05-10#Entry1"])


@pytest.mark.asyncio
async def test_dream_process_dedupes_duplicate_identification(dream_process, mock_llm, mock_wiki, mock_logs):
    entry = LogEntry(
        entry_id="2026-05-10#Entry1",
        session_id="ses-123",
        timestamp=datetime.now(),
        content="New experience",
        importance=0.8,
        status="raw"
    )
    mock_logs.get_unconsolidated.return_value = [entry]
    mock_wiki.get_index.return_value = "# Index"
    mock_wiki.exists.return_value = False
    mock_wiki.list_all.return_value = []
    mock_llm.call_structured.side_effect = [
        [
            {"page": "RLHF", "action": "create"},
            {"page": "[[rlhf]]", "action": "create"},
            {"page": "rlhf.md", "action": "create"},
        ],
        {"title": "RLHF", "content": "One page", "confidence": 0.8, "importance": 0.7},
        {"index": "# Updated Index"},
    ]

    report = await dream_process.run(strategy="full", conflict_policy="override")

    assert report.pages_created == 1
    assert mock_wiki.save.call_count == 1


@pytest.mark.asyncio
async def test_dream_process_merges_same_title_creates(dream_process, mock_llm, mock_wiki, mock_logs):
    entry = LogEntry(
        entry_id="2026-05-10#Entry1",
        session_id="ses-123",
        timestamp=datetime.now(),
        content="New experience",
        importance=0.8,
        status="raw"
    )
    mock_logs.get_unconsolidated.return_value = [entry]
    mock_wiki.get_index.return_value = "# Index"
    mock_wiki.list_all.return_value = []
    saved_pages = {}

    def exists(slug):
        return slug in saved_pages

    def save(page):
        saved_pages[page.slug] = page

    def get(slug):
        return saved_pages[slug]

    mock_wiki.exists.side_effect = exists
    mock_wiki.save.side_effect = save
    mock_wiki.get.side_effect = get
    mock_llm.call_structured.side_effect = [
        [
            {"page": "rlhf", "action": "create"},
            {"page": "dpo", "action": "create"},
        ],
        {"title": "Reinforcement Learning and Cognitive Modeling", "content": "First", "confidence": 0.8, "importance": 0.7},
        {"title": "Reinforcement Learning and Cognitive Modeling", "content": "Second", "confidence": 0.85, "importance": 0.75},
        {"index": "# Updated Index"},
    ]

    report = await dream_process.run(strategy="full", conflict_policy="override")

    assert report.pages_created == 1
    assert report.pages_updated == 1
    assert list(saved_pages) == ["rlhf"]
    assert saved_pages["rlhf"].content == "Second"
