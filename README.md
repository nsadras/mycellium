# Mycelium (MnemOS)

A neurobiologically-inspired, dependency-light memory system for LLM agents. Built on the **Karpathy Wiki Pattern**, Mycelium uses plain markdown files and a local LLM (via Ollama) to manage the full cognitive lifecycle of agent memory.

## Key Features

- **Plain-Text First:** Memories are stored as readable Markdown files with YAML frontmatter. No vector DB or embedding models required.
- **Reconsolidation:** Implements retrieval-triggered memory updates. When stored knowledge contradicts new context, the memory enters a "labile" state to be updated.
- **Dream Process:** Asynchronous consolidation of raw episodic logs into structured semantic wiki pages.
- **Local Intelligence:** All routing, ranking, and synthesis are performed by local LLM calls via Ollama.
- **Framework Agnostic:** Easily integrates with LangGraph, AutoGen, or custom agent loops.

## Project Structure

```text
mycelium/
├── mycelium/           # Core Library
│   ├── core.py         # Main Client (Mycelium)
│   ├── session.py      # Session Context Manager
│   ├── store.py        # File I/O (Wiki & Logs)
│   ├── encoder.py      # Raw event encoding
│   ├── reconsolidation.py # Prediction error & lability logic
│   ├── dream.py        # Consolidation & Dream process
│   └── decay.py        # Forgetting curve engine
├── tests/              # Comprehensive test suite
├── examples/           # Integration examples
└── pyproject.toml      # uv/hatchling configuration
```

## Quick Start

### 1. Requirements
- Python 3.11+
- [Ollama](https://ollama.ai/) running locally (recommended model: `gemma3:12b`)

### 2. Basic Usage

```python
import asyncio
import mycelium

async def main():
    # Initialize the memory store
    mem = mycelium.Mycelium(
        store_path='./agent_memory',
        ollama_model='gemma3:12b'
    )

    # Start a session to load relevant context
    query = "What do we know about the project architecture?"
    async with mem.session(query=query) as session:
        # 1. Get memory-injected prompt
        prompt = session.build_prompt(query)
        
        # 2. Run your agent logic...
        response = "We use a plain-text wiki pattern."
        
        # 3. Record interaction (auto-encoded to logs on exit)
        session.record('user', query)
        session.record('assistant', response)

    # Manually trigger a dream pass to consolidate logs into wiki pages
    await mem.dream()

if __name__ == "__main__":
    asyncio.run(main())
```

## Core Processes

1.  **Encoding:** Extracting key facts from transcripts into episodic logs.
2.  **Retrieval:** LLM-driven routing to select the most relevant wiki pages for the current task.
3.  **Reconsolidation:** Detecting discrepancies between retrieved memory and current reality to update the wiki.
4.  **Decay:** Gradually lowering the "strength" of memories based on time and importance.
