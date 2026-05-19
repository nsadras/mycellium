from types import SimpleNamespace

import pytest
from pydantic import BaseModel, RootModel

from mycelium.ollama import OllamaClient


class FakeSdkClient:
    def __init__(self, content: str):
        self.content = content
        self.chat_calls = []
        self.generate_calls = []

    async def chat(self, **kwargs):
        self.chat_calls.append(kwargs)
        return SimpleNamespace(message=SimpleNamespace(content=self.content))

    async def generate(self, **kwargs):
        self.generate_calls.append(kwargs)
        return SimpleNamespace(response=self.content)


@pytest.mark.asyncio
async def test_call_uses_official_sdk_chat():
    client = OllamaClient("http://localhost:11434", "test-model", temperature=0.3)
    fake_sdk = FakeSdkClient("hello")
    client.client = fake_sdk

    response = await client.call("system prompt", "user prompt")

    assert response == "hello"
    assert fake_sdk.chat_calls == [
        {
            "model": "test-model",
            "messages": [
                {"role": "system", "content": "system prompt"},
                {"role": "user", "content": "user prompt"},
            ],
            "stream": False,
            "format": None,
            "options": {"temperature": 0.3},
        }
    ]
    assert fake_sdk.generate_calls == []


@pytest.mark.asyncio
async def test_call_structured_passes_schema_to_sdk_and_parses_content():
    schema = {
        "type": "object",
        "properties": {"answer": {"type": "string"}},
        "required": ["answer"],
    }
    client = OllamaClient("http://localhost:11434", "test-model")
    fake_sdk = FakeSdkClient('{"answer": "yes"}')
    client.client = fake_sdk

    response = await client.call_structured("system prompt", "user prompt", schema)

    assert response == {"answer": "yes"}
    assert fake_sdk.chat_calls == []
    assert fake_sdk.generate_calls == [
        {
            "model": "test-model",
            "system": "system prompt",
            "prompt": "user prompt",
            "stream": False,
            "format": schema,
            "options": {"temperature": 0.0},
        }
    ]


class AnswerOutput(BaseModel):
    answer: str


class AnswerListOutput(RootModel[list[AnswerOutput]]):
    pass


@pytest.mark.asyncio
async def test_call_structured_accepts_pydantic_model():
    client = OllamaClient("http://localhost:11434", "test-model")
    fake_sdk = FakeSdkClient('{"answer": "yes"}')
    client.client = fake_sdk

    response = await client.call_structured("system prompt", "user prompt", AnswerOutput)

    assert response == {"answer": "yes"}
    assert fake_sdk.generate_calls[0]["format"] == AnswerOutput.model_json_schema()


@pytest.mark.asyncio
async def test_call_structured_accepts_pydantic_root_model():
    client = OllamaClient("http://localhost:11434", "test-model")
    fake_sdk = FakeSdkClient('[{"answer": "yes"}]')
    client.client = fake_sdk

    response = await client.call_structured("system prompt", "user prompt", AnswerListOutput)

    assert response == [{"answer": "yes"}]
    assert fake_sdk.generate_calls[0]["format"] == AnswerListOutput.model_json_schema()
