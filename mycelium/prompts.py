def encoding_prompt(index_content: str, transcript: str) -> tuple[str, str]:
    system = """You are a memory encoder for an AI agent. Given a session transcript, extract the most significant events, decisions, beliefs, or facts worth remembering. For each, rate importance 0.0–1.0 and assign topic tags. Format as structured log entries.

Filter out: small talk, routine confirmations, anything already well covered in the wiki (which is provided below for reference).

Respond with valid JSON only. No markdown code fences, no explanation, no preamble."""
    user = f"""WIKI INDEX:
{index_content}

TRANSCRIPT:
{transcript}"""
    return system, user

def consolidation_identify_prompt(index_content: str, log_entries: str) -> tuple[str, str]:
    system = """You are a memory consolidation agent. Given recent log entries, identify which existing wiki pages are affected by new information, and whether any new pages need to be created.

Return a JSON list of objects, each with:
- "page": the slug of the wiki page
- "action": one of "update", "create", or "none"

Respond with valid JSON only. No markdown code fences, no explanation, no preamble."""
    user = f"""WIKI INDEX:
{index_content}

RECENT LOG ENTRIES:
{log_entries}"""
    return system, user

def consolidation_rewrite_prompt(existing_page: str, log_entries: str) -> tuple[str, str]:
    system = """You are rewriting a wiki page to incorporate new experience.
Rules:
- Abstract, do not summarize. Extract the principle, not the event.
- Resolve conflicts explicitly: if new info contradicts existing content, choose the more recent/credible version and note the revision.
- Update confidence score based on how much evidence now supports this.
- Update related: links if new connections are apparent.
- Increment version.
- Do NOT include specific dates, people's names, or episodic details unless they are themselves the principle being recorded.

Return the updated page content in JSON format with fields:
- "title": string
- "content": string (markdown body)
- "tags": list of strings
- "related": list of objects {target: str, relation: str, weight: float}
- "confidence": float
- "importance": float

Respond with valid JSON only. No markdown code fences, no explanation, no preamble."""
    user = f"""EXISTING PAGE:
{existing_page}

NEW LOG ENTRIES:
{log_entries}"""
    return system, user

def consolidation_index_prompt(current_index: str, changes_summary: str) -> tuple[str, str]:
    system = """You are updating the wiki index based on recent consolidation changes.
Update the index to reflect new pages, updated descriptions, and new cross-links. Keep it concise.

Return the completely rewritten index markdown as a string inside a JSON object with a single "index" field.

Respond with valid JSON only. No markdown code fences, no explanation, no preamble."""
    user = f"""CURRENT INDEX:
{current_index}

CHANGES:
{changes_summary}"""
    return system, user

def prediction_error_prompt(wiki_page: str, current_context: str) -> tuple[str, str]:
    system = """You are a memory reconsolidation monitor. Given a stored wiki page and the current session context, assess whether the stored belief is still accurate.

Assess the conflict type:
- "none": content matches context well (score < 0.2)
- "additive": context adds nuance not captured (score 0.2–0.35)
- "partial": context partially contradicts stored belief (score 0.35–0.65)
- "major": context strongly contradicts stored belief (score > 0.65)

Return JSON with fields:
- "conflict_type": string ("none"|"additive"|"partial"|"major")
- "discrepancy_score": float
- "explanation": string
- "suggested_update": string or null

Respond with valid JSON only. No markdown code fences, no explanation, no preamble."""
    user = f"""STORED WIKI PAGE:
{wiki_page}

CURRENT CONTEXT:
{current_context}"""
    return system, user

def reconsolidation_rewrite_prompt(original_page: str, update_signals: str) -> tuple[str, str]:
    system = """A wiki page has been flagged for reconsolidation. One or more retrieval events during this session revealed that its content may be outdated or incomplete. Rewrite the page to incorporate the updates.

Rules:
- Maintain the page's abstracted, principle-level voice
- Determine a reason for the update to put in the update_log
- Return the new confidence score

Return the updated page content in JSON format with fields:
- "title": string
- "content": string
- "tags": list of strings
- "related": list of objects {target: str, relation: str, weight: float}
- "confidence": float
- "importance": float
- "update_reason": string

Respond with valid JSON only. No markdown code fences, no explanation, no preamble."""
    user = f"""ORIGINAL PAGE:
{original_page}

ACCUMULATED UPDATE SIGNALS:
{update_signals}"""
    return system, user

def routing_prompt(index_content: str, query: str, budget_tokens: int) -> tuple[str, str]:
    system = f"""You are a memory retrieval agent. Given the user's query and the wiki index, select the pages most relevant to load into context.

Constraints:
- Total loaded content must stay under {budget_tokens} tokens
- Prefer pages with higher confidence and lower decay_score
- Follow related: links to include associated pages if budget allows
- If no pages are clearly relevant, return an empty list

Return JSON: a list of objects, each with:
- "page": string (slug)
- "reason": string
- "priority": integer 1-5 (1 is highest)

Respond with valid JSON only. No markdown code fences, no explanation, no preamble."""
    user = f"""WIKI INDEX:
{index_content}

USER QUERY:
{query}"""
    return system, user

def importance_rating_prompt(content: str) -> tuple[str, str]:
    system = """You are a memory importance rater. Given a piece of information, rate its long-term importance for an AI agent on a scale from 0.0 to 1.0. Also suggest topic tags.

Return JSON with fields:
- "importance": float
- "tags": list of strings

Respond with valid JSON only. No markdown code fences, no explanation, no preamble."""
    user = f"""CONTENT:
{content}"""
    return system, user
