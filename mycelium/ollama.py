import json
import logging
import time
import re
import uuid
from typing import Any, Union, Optional

from ollama import AsyncClient, RequestError, ResponseError
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, url: str, model: str, temperature: float = 0.1, timeout: int = 120) -> None:
        self.url = url.rstrip('/')
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.client = AsyncClient(host=self.url, timeout=self.timeout)
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
        expect_json: Union[bool, dict, type[BaseModel]] = False,
        max_retries: int = 3,
        temperature: Optional[float] = None
    ) -> Union[str, dict, list]:
        """
        Makes a chat completion call to Ollama.
        If expect_json is a dict, it is passed as a JSON Schema to constrain output.
        """
        call_id = str(uuid.uuid4())[:8]
        sys_prompt = system
            
        temp = temperature if temperature is not None else self.temperature
            
        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user},
        ]
        options = {"temperature": temp}
        output_format: Union[str, dict[str, Any], None] = None
        response_model: type[BaseModel] | None = None
        
        if expect_json:
            if isinstance(expect_json, type) and issubclass(expect_json, BaseModel):
                response_model = expect_json
                output_format = expect_json.model_json_schema()
            elif isinstance(expect_json, dict):
                output_format = expect_json
            else:
                output_format = "json"

        endpoint = f"{self.url}/api/chat"
        
        for attempt in range(max_retries):
            start_time = time.time()
            self._log_request(
                call_id=call_id,
                attempt=attempt + 1,
                max_retries=max_retries,
                endpoint=endpoint,
                model=self.model,
                messages=messages,
                output_format=output_format,
                options=options,
            )
            try:
                response = await self.client.chat(
                    model=self.model,
                    messages=messages,
                    stream=False,
                    format=output_format,
                    options=options,
                )
                content = self._response_content(response)
                
                latency_ms = int((time.time() - start_time) * 1000)
                
                if expect_json:
                    try:
                        parsed = self._parse_structured_response(content, response_model)
                        self._log_call(call_id, attempt + 1, sys_prompt, user, content, latency_ms, True)
                        return parsed
                    except (json.JSONDecodeError, ValidationError, ValueError):
                        self._log_call(call_id, attempt + 1, sys_prompt, user, content, latency_ms, False)
                        if attempt == max_retries - 1:
                            raise ValueError(f"Failed to parse JSON response from Ollama after {max_retries} attempts: {content}")
                        continue # Retry
                        
                self._log_call(call_id, attempt + 1, sys_prompt, user, content, latency_ms, True)
                return content
                
            except (RequestError, ResponseError) as e:
                latency_ms = int((time.time() - start_time) * 1000)
                self._log_call(call_id, attempt + 1, sys_prompt, user, str(e), latency_ms, False)
                if attempt == max_retries - 1:
                    raise

    def _response_content(self, response: Any) -> str:
        message = getattr(response, "message", None)
        if isinstance(message, dict):
            return str(message.get("content", "")).strip()
        content = getattr(message, "content", "")
        return str(content).strip()

    def _parse_structured_response(
        self,
        content: str,
        response_model: type[BaseModel] | None,
    ) -> Union[dict, list]:
        if response_model is None:
            parsed = self._extract_json(content)
            if not isinstance(parsed, (dict, list)):
                raise ValueError("Structured response was not a JSON object or array")
            return parsed

        stripped = content.strip()
        try:
            parsed_model = response_model.model_validate_json(stripped)
        except ValidationError:
            extracted = self._extract_json(stripped)
            parsed_model = response_model.model_validate(extracted)

        if getattr(parsed_model, "__pydantic_root_model__", False):
            return parsed_model.model_dump(exclude_none=True)
        return parsed_model.model_dump(exclude_none=True)
                    
    async def call_structured(
        self,
        system: str,
        user: str,
        schema: Union[dict, type[BaseModel]],
        max_retries: int = 3,
    ) -> Union[dict, list]:
        """
        Uses Ollama's one-shot generate API with native JSON Schema support.
        """
        call_id = str(uuid.uuid4())[:8]
        output_format, response_model = self._structured_format(schema)
        options = {"temperature": 0.0}
        endpoint = f"{self.url}/api/generate"

        for attempt in range(max_retries):
            start_time = time.time()
            self._log_request(
                call_id=call_id,
                attempt=attempt + 1,
                max_retries=max_retries,
                endpoint=endpoint,
                model=self.model,
                messages=None,
                prompt=user,
                system=system,
                output_format=output_format,
                options=options,
            )
            try:
                response = await self.client.generate(
                    model=self.model,
                    system=system,
                    prompt=user,
                    stream=False,
                    format=output_format,
                    options=options,
                )
                content = self._generate_response_content(response)
                latency_ms = int((time.time() - start_time) * 1000)

                try:
                    parsed = self._parse_structured_response(content, response_model)
                    self._log_call(call_id, attempt + 1, system, user, content, latency_ms, True)
                    return parsed
                except (json.JSONDecodeError, ValidationError, ValueError):
                    self._log_call(call_id, attempt + 1, system, user, content, latency_ms, False)
                    if attempt == max_retries - 1:
                        raise ValueError(f"Failed to parse JSON response from Ollama after {max_retries} attempts: {content}")
                    continue

            except (RequestError, ResponseError) as e:
                latency_ms = int((time.time() - start_time) * 1000)
                self._log_call(call_id, attempt + 1, system, user, str(e), latency_ms, False)
                if attempt == max_retries - 1:
                    raise

        raise ValueError("Failed to get structured response from Ollama")

    def _structured_format(
        self,
        schema: Union[dict, type[BaseModel]],
    ) -> tuple[Union[str, dict[str, Any]], type[BaseModel] | None]:
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            return schema.model_json_schema(), schema
        return schema, None

    def _generate_response_content(self, response: Any) -> str:
        content = getattr(response, "response", "")
        if content:
            return str(content).strip()
        if isinstance(response, dict):
            return str(response.get("response", "")).strip()
        return ""

    def _log_request(
        self,
        call_id: str,
        attempt: int,
        max_retries: int,
        endpoint: str,
        model: str,
        messages: list[dict[str, str]] | None,
        output_format: Union[str, dict[str, Any], None],
        options: dict[str, Any],
        prompt: str | None = None,
        system: str | None = None,
    ) -> None:
        logger.info(
            "LLM request\n%s",
            json.dumps(
                {
                    "call_id": call_id,
                    "attempt": attempt,
                    "max_retries": max_retries,
                    "endpoint": endpoint,
                    "model": model,
                    "format": output_format,
                    "options": options,
                    "messages": messages,
                    "system": system,
                    "prompt": prompt,
                },
                indent=2,
                ensure_ascii=False,
            ),
        )

    def _log_call(
        self,
        call_id: str,
        attempt: int,
        system: str,
        user: str,
        response: str,
        latency_ms: int,
        success: bool,
    ) -> None:
        entry = {
            "timestamp": time.time(),
            "call_id": call_id,
            "attempt": attempt,
            "system": system,
            "user": user,
            "response": response,
            "latency_ms": latency_ms,
            "success": success
        }
        self._call_log.append(entry)
        logger.info("LLM response\n%s", json.dumps(entry, indent=2, ensure_ascii=False))
