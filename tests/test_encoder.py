import pytest
from unittest.mock import AsyncMock, MagicMock
from mycelium.encoder import Encoder
from mycelium.models import LogEntry
from mycelium.config import Config

@pytest.fixture
def mock_llm():
    return AsyncMock()

@pytest.fixture
def mock_wiki_store():
    store = MagicMock()
    store.get_index.return_value = "# Index"
    return store

@pytest.fixture
def mock_log_store():
    return MagicMock()

@pytest.fixture
def encoder(mock_llm, mock_wiki_store, mock_log_store):
    config = Config.defaults()
    return Encoder(mock_llm, mock_wiki_store, mock_log_store, config)

@pytest.mark.asyncio
async def test_encode_session(encoder, mock_llm, mock_log_store):
    mock_llm.call_structured.return_value = [
        {
            "content": "Important detail 1",
            "memory_type": "project_fact",
            "durability": "durable",
            "importance": 0.8,
            "tags": ["t1"],
        },
        {
            "content": "Durable user detail",
            "memory_type": "user_profile",
            "durability": "durable",
            "importance": 0.1,
            "tags": ["user"],
        },
        {
            "content": "Trivial detail",
            "memory_type": "other",
            "durability": "ephemeral",
            "importance": 0.1,
            "tags": ["t2"],
        },
        {
            "content": "Important detail 2",
            "memory_type": "concept",
            "durability": "session",
            "importance": 0.6,
            "tags": ["t3"],
        },
    ]
    
    entries = await encoder.encode_session("some transcript", "ses-123", min_importance=0.3)
    
    assert len(entries) == 3
    assert entries[0].content == "Important detail 1"
    assert entries[0].importance == 0.8
    assert entries[0].memory_type == "project_fact"
    assert entries[1].content == "Durable user detail"
    assert entries[1].importance == 0.1
    assert entries[1].memory_type == "user_profile"
    assert entries[2].content == "Important detail 2"
    assert entries[2].importance == 0.6
    
    assert mock_log_store.append.call_count == 3
    args, _ = mock_log_store.append.call_args_list[0]
    assert isinstance(args[0], LogEntry)
    assert args[0].session_id == "ses-123"

@pytest.mark.asyncio
async def test_encode_direct_with_importance(encoder, mock_llm, mock_log_store):
    entry = await encoder.encode(
        content="Direct entry",
        session_id="ses-123",
        importance=0.9,
        tags=["direct"]
    )
    
    assert entry.content == "Direct entry"
    assert entry.importance == 0.9
    assert entry.tags == ["direct"]
    
    mock_llm.call_structured.assert_not_called()
    mock_log_store.append.assert_called_once_with(entry)

@pytest.mark.asyncio
async def test_encode_direct_without_importance(encoder, mock_llm, mock_log_store):
    mock_llm.call_structured.return_value = {"importance": 0.75, "tags": ["llm-tag"]}
    
    entry = await encoder.encode(
        content="Direct entry no importance",
        session_id="ses-123"
    )
    
    assert entry.content == "Direct entry no importance"
    assert entry.importance == 0.75
    assert entry.tags == ["llm-tag"]
    
    mock_llm.call_structured.assert_called_once()
    mock_log_store.append.assert_called_once_with(entry)
