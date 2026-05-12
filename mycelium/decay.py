from datetime import datetime, timezone

def compute_decay_score(
    current_score: float,
    last_accessed: datetime,
    importance: float,
    access_count: int,
    now: datetime | None = None,
) -> float:
    """
    Computes the new decay score based on elapsed time, importance, and access frequency.
    """
    if now is None:
        now = datetime.now(timezone.utc)
        
    # Handle naive vs aware datetime
    if last_accessed.tzinfo is None:
        last_accessed = last_accessed.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
        
    hours_elapsed = (now - last_accessed).total_seconds() / 3600.0
    if hours_elapsed < 0:
        hours_elapsed = 0
        
    recency = 0.995 ** hours_elapsed
    adjusted = recency ** (1.0 - importance * 0.5)
    freq_boost = min(0.3, access_count * 0.02)
    
    return min(1.0, adjusted + freq_boost)

class DecayEngine:
    def __init__(self, wiki, logs, config):
        self.wiki = wiki
        self.logs = logs
        self.config = config

    async def run_pass(self) -> dict[str, float]:
        now = datetime.now(timezone.utc)
        changed_scores = {}
        
        # 1. Load all wiki pages
        pages = self.wiki.list_all()
        for page in pages:
            # 2. Recompute decay_score
            # We don't have access_count natively tracked yet, assuming 1 for now
            new_score = compute_decay_score(
                page.decay_score,
                page.last_updated,
                page.importance,
                access_count=1,
                now=now
            )
            
            if new_score != page.decay_score:
                page.decay_score = new_score
                changed_scores[page.slug] = new_score
                
                # 3. Save updated pages
                # 4. Archive pages below config.decay.archive_threshold
                if new_score < self.config.decay.archive_threshold:
                    self.wiki.archive(page.slug)
                else:
                    self.wiki.save(page)
                    
        # 5. Update log entry decay scores
        # We only apply decay to unconsolidated entries for simplicity
        entries = self.logs.get_unconsolidated(days=30)
        for entry in entries:
            new_score = compute_decay_score(
                entry.decay_score,
                entry.timestamp,
                entry.importance,
                access_count=1,
                now=now
            )
            
            if new_score != entry.decay_score:
                self.logs.update_decay(entry.entry_id, new_score)
                # 6. Soft-delete handled by query mechanisms skipping below log_threshold
                if new_score < self.config.decay.log_threshold:
                    # In a full implementation, we'd mark this as archived/soft-deleted
                    pass
                    
        return changed_scores
