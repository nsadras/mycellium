import json
import logging
import time
import re
from typing import Dict, Any, Union, Optional
import httpx

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, url: str, model: str, temperature: float = 0.2, timeout: int = 120) -> None:
        self.url = url.rstrip('/')
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self._call_log: list[dict] = []

    def _extract_json(self, content: str) -> Union[dict, list]:
        """
        Extracts JSON from a string, handling potential markdown fences.
        """
        content = content.strip()
        
        # Remove markdown code fences if present
        if content.startswith("```"):
            # Find the end of the first line (e.g., ```json)
            first_line_end = content.find("\n")
            if first_line_end != -1:
                content = content[first_line_end:].strip()
            
            # Remove the closing fences
            if content.endswith("```"):
                content = content[:-3].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # If standard parsing fails, try a simple regex for the first { or [ to the last } or ]
            # as a last resort fallback for models that still add preambles.
            match = re.search(r'([\[{].*[\]}])', content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            raise

    async def call(
        self,
        system: str,
        user: str,
        expect_json: Union[bool, dict] = False,
        max_retries: int = 3,
        temperature: Optional[float] = None
    ) -> Union[str, dict]:
        """
        Makes a chat completion call to Ollama.
        If expect_json is a dict, it is passed as a JSON Schema to constrain output.
        """
        sys_prompt = system
        if expect_json is True:
            sys_prompt += "\n\nRespond with valid JSON only. No markdown, no explanation, no preamble."
            
        temp = temperature if temperature is not None else self.temperature
            
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user}
            ],
            "stream": False,
            "options": {
                "temperature": temp
            }
        }
        
        if expect_json:
            if isinstance(expect_json, dict):
                payload["format"] = expect_json
            else:
                payload["format"] = "json"

        endpoint = f"{self.url}/api/chat"
        
        for attempt in range(max_retries):
            start_time = time.time()
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(endpoint, json=payload)
                    response.raise_for_status()
                    
                data = response.json()
                content = data.get("message", {}).get("content", "").strip()
                
                latency_ms = int((time.time() - start_time) * 1000)
                
                if expect_json:
                    try:
                        parsed = self._extract_json(content)
                        self._log_call(sys_prompt, user, content, latency_ms, True)
                        return parsed
                    except (json.JSONDecodeError, ValueError):
                        self._log_call(sys_prompt, user, content, latency_ms, False)
                        if attempt == max_retries - 1:
                            raise ValueError(f"Failed to parse JSON response from Ollama after {max_retries} attempts: {content}")
                        continue # Retry
                        
                self._log_call(sys_prompt, user, content, latency_ms, True)
                return content
                
            except httpx.HTTPError as e:
                latency_ms = int((time.time() - start_time) * 1000)
                self._log_call(sys_prompt, user, str(e), latency_ms, False)
                if attempt == max_retries - 1:
                    raise
                    
    async def call_structured(
        self,
        system: str,
        user: str,
        schema: dict,
        max_retries: int = 3,
    ) -> dict:
        """
        Uses Ollama's native JSON Schema support to constrain output.
        """
        return await self.call(
            system=system,
            user=user,
            expect_json=schema,
            max_retries=max_retries
        )

    def _log_call(self, system: str, user: str, response: str, latency_ms: int, success: bool):
        entry = {
            "timestamp": time.time(),
            "system": system[:200] + ("..." if len(system) > 200 else ""),
            "user": user[:200] + ("..." if len(user) > 200 else ""),
            "response": response[:200] + ("..." if len(response) > 200 else ""),
            "latency_ms": latency_ms,
            "success": success
        }
        self._call_log.append(entry)
