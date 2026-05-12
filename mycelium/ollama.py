import json
import logging
import time
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

    async def call(
        self,
        system: str,
        user: str,
        expect_json: bool = False,
        max_retries: int = 3,
        temperature: Optional[float] = None
    ) -> Union[str, dict]:
        """
        Makes a chat completion call to Ollama.
        """
        sys_prompt = system
        if expect_json:
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
                        parsed = json.loads(content)
                        self._log_call(sys_prompt, user, content, latency_ms, True)
                        return parsed
                    except json.JSONDecodeError:
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
        Like call() with expect_json=True, but could optionally validate against JSON schema.
        For now, we just pass the schema into the system prompt and rely on expect_json.
        """
        sys_with_schema = f"{system}\n\nExpected JSON schema:\n{json.dumps(schema, indent=2)}"
        return await self.call(
            system=sys_with_schema,
            user=user,
            expect_json=True,
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
