from types import SimpleNamespace

from mycelium.store import LogStore
from server import runtime
from server.runtime import append_tool_event_logs, ensure_session_record


def test_ensure_session_record_initializes_episode():
    record = {"query": "Test", "transcript": []}

    ensure_session_record(record, "ses")

    assert record["encoded_episodes"] == []
    assert record["active_episode"]["id"] == "ses-ep-1"
    assert record["active_episode"]["buffer"] == []


def test_no_entries_flush_should_preserve_buffer_shape():
    record = {
        "query": "Test",
        "transcript": [{"role": "user", "content": "hello"}],
        "episode_seq": 1,
        "encoded_episodes": [],
        "active_episode": {
            "id": "ses-ep-1",
            "started_at": "2026-05-19T00:00:00+00:00",
            "last_activity_at": "2026-05-19T00:00:00+00:00",
            "buffer": [{"role": "user", "content": "hello"}],
            "turn_count": 1,
        },
    }

    ensure_session_record(record, "ses")

    assert record["active_episode"]["turn_count"] == 1
    assert record["encoded_episodes"] == []


def test_append_tool_event_logs_creates_unconsolidated_entries(tmp_path, monkeypatch):
    log_store = LogStore(tmp_path / "logs")
    monkeypatch.setattr(runtime, "get_mem", lambda: SimpleNamespace(log_store=log_store))

    created = append_tool_event_logs(
        "chat-123",
        "chat-123-ep-1",
        [
            {
                "tool_name": "web_search",
                "arguments": {"query": "local llm news"},
                "result": "1. Result\nhttps://example.com\nUseful new information.",
                "failed": False,
                "truncated": True,
            }
        ],
        turn_count=2,
    )

    entries = log_store.get_unconsolidated()
    assert len(created) == 1
    assert len(entries) == 1
    assert entries[0].entry_id.startswith(created[0].entry_id.split("#")[0] + "#tool-")
    assert entries[0].session_id == "chat-123-ep-1"
    assert "Tool observation from chat." in entries[0].content
    assert "- chat_session_id: chat-123" in entries[0].content
    assert "- tool_name: web_search" in entries[0].content
    assert '"query": "local llm news"' in entries[0].content
    assert "Useful new information." in entries[0].content
