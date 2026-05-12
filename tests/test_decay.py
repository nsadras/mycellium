import pytest
from datetime import datetime, timedelta, timezone
from mycelium.decay import compute_decay_score, DecayEngine
from mycelium.models import WikiPage, LogEntry
from mycelium.config import Config
from unittest.mock import MagicMock

def test_compute_decay_score():
    now = datetime.now(timezone.utc)
    
    # 0 hours elapsed -> score should be 1.0 (or close, boosted by freq)
    score = compute_decay_score(1.0, now, importance=0.5, access_count=1, now=now)
    assert score <= 1.0
    
    # High importance decays slower
    past = now - timedelta(hours=168) # 1 week
    score_low_imp = compute_decay_score(1.0, past, importance=0.0, access_count=0, now=now)
    score_high_imp = compute_decay_score(1.0, past, importance=1.0, access_count=0, now=now)
    
    assert score_high_imp > score_low_imp

@pytest.mark.asyncio
async def test_decay_engine_run_pass():
    mock_wiki = MagicMock()
    mock_logs = MagicMock()
    config = Config.defaults()
    config.decay.archive_threshold = 0.5
    
    # Page that will NOT be archived
    p1 = WikiPage(
        slug="p1", title="p1", content="",
        created=datetime.now(), last_updated=datetime.now(),
        version=1, confidence=1.0, decay_score=0.9, importance=1.0
    )
    # Page that WILL be archived (old, low importance)
    p2 = WikiPage(
        slug="p2", title="p2", content="",
        created=datetime.now() - timedelta(days=365), 
        last_updated=datetime.now() - timedelta(days=365),
        version=1, confidence=1.0, decay_score=1.0, importance=0.0
    )
    
    mock_wiki.list_all.return_value = [p1, p2]
    mock_logs.get_unconsolidated.return_value = []
    
    engine = DecayEngine(mock_wiki, mock_logs, config)
    changed = await engine.run_pass()
    
    assert "p1" in changed
    assert "p2" in changed
    
    # p1 should be saved, p2 should be archived
    mock_wiki.save.assert_called_once_with(p1)
    mock_wiki.archive.assert_called_once_with("p2")
