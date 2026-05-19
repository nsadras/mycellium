from server.runtime import ensure_session_record


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
