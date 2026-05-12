import datetime
from typing import List, Optional
import uuid

from mycelium.models import LogEntry
from mycelium.store import WikiStore, LogStore
from mycelium.ollama import OllamaClient
from mycelium.config import Config
from mycelium import prompts

class Encoder:
    def __init__(self, llm: OllamaClient, wiki_store: WikiStore, log_store: LogStore, config: Config):
        self.llm = llm
        self.wiki_store = wiki_store
        self.log_store = log_store
        self.config = config

    async def encode_session(
        self,
        transcript: str,
        session_id: str,
        min_importance: float = 0.3,
    ) -> List[LogEntry]:
        
        index_content = self.wiki_store.get_index()
        system, user = prompts.encoding_prompt(index_content, transcript)
        
        # We expect a JSON list of entries from the LLM
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "importance": {"type": "number"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["content", "importance", "tags"]
            }
        }
        
        response = await self.llm.call_structured(system, user, schema)
        if not isinstance(response, list):
            response = [response] if isinstance(response, dict) else []
            
        created_entries = []
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        
        for idx, item in enumerate(response):
            if not isinstance(item, dict):
                continue
                
            importance = float(item.get("importance", 0.0))
            if importance < min_importance:
                continue
                
            content = item.get("content", "").strip()
            if not content:
                continue
                
            tags = item.get("tags", [])
            
            # Generate a unique entry ID
            short_id = str(uuid.uuid4())[:8]
            entry_id = f"{date_str}#entry-{short_id}"
            
            entry = LogEntry(
                entry_id=entry_id,
                session_id=session_id,
                timestamp=now,
                content=content,
                importance=importance,
                tags=tags,
                status="raw",
                consolidated=False,
                decay_score=1.0
            )
            
            self.log_store.append(entry)
            created_entries.append(entry)
            
        return created_entries

    async def encode(
        self,
        content: str,
        session_id: str,
        importance: Optional[float] = None,
        tags: Optional[List[str]] = None,
    ) -> LogEntry:
        
        final_importance = importance
        final_tags = tags or []
        
        if importance is None:
            system, user = prompts.importance_rating_prompt(content)
            schema = {
                "type": "object",
                "properties": {
                    "importance": {"type": "number"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["importance", "tags"]
            }
            response = await self.llm.call_structured(system, user, schema)
            
            if isinstance(response, dict):
                final_importance = float(response.get("importance", 0.5))
                if tags is None:
                    final_tags = response.get("tags", [])
            else:
                final_importance = 0.5
                
        if final_importance is None:
            final_importance = 0.5
            
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        short_id = str(uuid.uuid4())[:8]
        entry_id = f"{date_str}#entry-{short_id}"
        
        entry = LogEntry(
            entry_id=entry_id,
            session_id=session_id,
            timestamp=now,
            content=content,
            importance=final_importance,
            tags=final_tags,
            status="raw",
            consolidated=False,
            decay_score=1.0
        )
        
        self.log_store.append(entry)
        return entry
