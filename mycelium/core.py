from pathlib import Path
from typing import List, Optional, Literal
import uuid

from mycelium.models import WikiPage, LogEntry, DreamReport
from mycelium.store import WikiStore, LogStore
from mycelium.config import Config
from mycelium.ollama import OllamaClient
from mycelium.encoder import Encoder
from mycelium.budget import ContextBudget
from mycelium.session import Session
from mycelium import prompts
from mycelium.structured_outputs import RoutingOutput

class Mycelium:
    def __init__(
        self,
        store_path: str | Path,
        ollama_model: str = 'gemma3:12b',
        ollama_url: str = 'http://localhost:11434',
        context_budget_tokens: int = 8192,
        lability_threshold: float = 0.35,
        dream_schedule: Literal['post_session', 'cron', 'manual'] = 'post_session',
        decay_interval_hours: int = 6,
        conflict_policy: Literal['fork', 'override', 'merge'] = 'fork',
        git_commits: bool = False,
        config_path: str | Path | None = None,
    ):
        self.store_path = Path(store_path)
        
        if config_path and Path(config_path).exists():
            self.config = Config.from_toml(Path(config_path))
        else:
            self.config = Config.defaults()
            self.config.store_path = self.store_path
            self.config.llm.model = ollama_model
            self.config.llm.url = ollama_url
            self.config.context_budget_tokens = context_budget_tokens
            self.config.reconsolidation.lability_threshold = lability_threshold
            self.config.dream.schedule = dream_schedule
            self.config.decay.interval_hours = decay_interval_hours
            self.config.dream.conflict_policy = conflict_policy
            self.config.git_commits = git_commits

        if not self.store_path.exists():
            self._init_store()
            
        self._wiki = WikiStore(self.store_path / "wiki")
        self._log_store = LogStore(self.store_path / "logs")
        self.llm = OllamaClient(
            url=self.config.llm.url,
            model=self.config.llm.model,
            temperature=self.config.llm.temperature,
            timeout=self.config.timeout_seconds if hasattr(self.config, 'timeout_seconds') else self.config.llm.timeout_seconds
        )
        from mycelium.reconsolidation import ReconsolidationEngine
        self.reconsolidation_engine = ReconsolidationEngine(self.llm, self._wiki, self.config)
        self.encoder = Encoder(self.llm, self._wiki, self._log_store, self.config)
        
        from mycelium.dream import DreamProcess
        self.dream_process = DreamProcess(self.llm, self._wiki, self._log_store, self.config)

    def _init_store(self) -> None:
        self.store_path.mkdir(parents=True, exist_ok=True)
        (self.store_path / "wiki").mkdir(exist_ok=True)
        (self.store_path / "logs").mkdir(exist_ok=True)
        (self.store_path / "labile").mkdir(exist_ok=True)
        (self.store_path / "wiki" / "_archive").mkdir(exist_ok=True)
        
        index_path = self.store_path / "wiki" / "_index.md"
        if not index_path.exists():
            with open(index_path, "w", encoding="utf-8") as f:
                f.write("# Wiki Index\n\n_last updated: never_\n\n## Pages\n")

    @property
    def wiki(self) -> WikiStore:
        return self._wiki

    @property
    def log_store(self) -> LogStore:
        return self._log_store

    async def load_context(
        self,
        query: str,
        budget_tokens: Optional[int] = None,
        reconsolidate: bool = True,
        session_id: Optional[str] = None
    ) -> List[WikiPage]:
        
        budget_tokens = budget_tokens or self.config.context_budget_tokens
        budget = ContextBudget(budget_tokens)
        
        index_content = self.wiki.get_index()
        budget.consume(index_content)
        
        if budget.remaining() <= 0:
            return []
            
        system, user = prompts.routing_prompt(index_content, query, budget.remaining())
        response = await self.llm.call_structured(system, user, RoutingOutput)
        if not isinstance(response, list):
            response = [response] if isinstance(response, dict) else []
            
        selections = []
        for item in response:
            if isinstance(item, dict) and "page" in item:
                priority = int(item.get("priority", 5))
                selections.append((priority, item["page"]))
                
        selections.sort(key=lambda x: x[0])
        
        loaded_pages = []
        for priority, slug in selections:
            if not self.wiki.exists(slug):
                continue
                
            page = self.wiki.get(slug)
            content = f"=== MEMORY: {page.title} (confidence: {page.confidence:.2f}, v{page.version}) ===\n{page.content}\n=== END MEMORY ==="
            
            if budget.fits(content):
                budget.consume(content)
                
                if reconsolidate and self.config.reconsolidation.check_on_load:
                    error = await self.reconsolidation_engine.check(page, query)
                    if error.discrepancy_score > self.config.reconsolidation.lability_threshold:
                        page.was_flagged = True
                        page.discrepancy_score = error.discrepancy_score
                        page.discrepancy_explanation = error.explanation
                        if session_id:
                            await self.reconsolidation_engine.flag_labile(page, session_id)
                            await self.reconsolidation_engine.accumulate_signal(page.slug, session_id, error)
                            
                loaded_pages.append(page)
                
        return loaded_pages

    from contextlib import asynccontextmanager
    
    @asynccontextmanager
    async def session(self, query: str, session_id: Optional[str] = None):
        session_id = session_id or str(uuid.uuid4())
        
        sess = Session(mycelium=self, session_id=session_id, query=query)
        sess.loaded_pages = await self.load_context(query, session_id=session_id)
        
        try:
            yield sess
        finally:
            if sess.transcript:
                transcript_str = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in sess.transcript])
                await self.encoder.encode_session(transcript_str, session_id)
            
            await self.reconsolidation_engine.resolve_labile_pages(session_id)
            
            if self.config.dream.schedule == 'post_session':
                await self.dream()

    async def dream(self, **kwargs) -> DreamReport:
        return await self.dream_process.run(**kwargs)

    async def encode(self, content: str, **kwargs) -> LogEntry:
        return await self.encoder.encode(content, **kwargs)
