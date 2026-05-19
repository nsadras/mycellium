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
    mock_llm.call_structured.return_value = {
        "entries": [
            {
                "content": "Important detail 1",
                "durability": "durable",
                "importance": "high",
            },
            {
                "content": "Durable user detail",
                "durability": "durable",
                "importance": "low",
            },
            {
                "content": "Trivial detail",
                "durability": "ephemeral",
                "importance": "low",
            },
            {
                "content": "The assistant recommended model-based RL projects tailored to the user's neuroscience background.",
                "durability": "session",
                "importance": "low",
            },
            {
                "content": "Important detail 2",
                "durability": "session",
                "importance": "medium",
            },
        ]
    }
    
    entries = await encoder.encode_session("some transcript", "ses-123")
    
    assert len(entries) == 5
    assert entries[0].content == "Important detail 1"
    assert entries[0].importance == 0.9
    assert entries[1].content == "Durable user detail"
    assert entries[1].importance == 0.25
    assert entries[2].content == "Trivial detail"
    assert entries[2].importance == 0.25
    assert entries[3].content.startswith("The assistant recommended")
    assert entries[3].importance == 0.25
    assert entries[4].content == "Important detail 2"
    assert entries[4].importance == 0.6
    
    assert mock_log_store.append.call_count == 5
    args, _ = mock_log_store.append.call_args_list[0]
    assert isinstance(args[0], LogEntry)
    assert args[0].session_id == "ses-123"

@pytest.mark.asyncio
async def test_encode_direct_with_importance(encoder, mock_llm, mock_log_store):
    entry = await encoder.encode(
        content="Direct entry",
        session_id="ses-123",
        importance=0.9
    )
    
    assert entry.content == "Direct entry"
    assert entry.importance == 0.9
    
    mock_llm.call_structured.assert_not_called()
    mock_log_store.append.assert_called_once_with(entry)

@pytest.mark.asyncio
async def test_encode_direct_without_importance(encoder, mock_llm, mock_log_store):
    mock_llm.call_structured.return_value = {"importance": 0.75}
    
    entry = await encoder.encode(
        content="Direct entry no importance",
        session_id="ses-123"
    )
    
    assert entry.content == "Direct entry no importance"
    assert entry.importance == 0.75
    
    mock_llm.call_structured.assert_called_once()
    mock_log_store.append.assert_called_once_with(entry)
