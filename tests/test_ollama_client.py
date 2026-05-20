from types import SimpleNamespace
from copy import deepcopy

import pytest
from pydantic import BaseModel, RootModel

from mycelium.ollama import OllamaClient


def snapshot_call(kwargs):
    snap = dict(kwargs)
    if "messages" in snap:
        snap["messages"] = deepcopy(snap["messages"])
    if "tools" in snap and snap["tools"] is not None:
        snap["tools"] = list(snap["tools"])
    return snap


class FakeSdkClient:
    def __init__(self, content: str):
        self.content = content
        self.chat_calls = []
        self.generate_calls = []

    async def chat(self, **kwargs):
        self.chat_calls.append(snapshot_call(kwargs))
        return SimpleNamespace(message=SimpleNamespace(content=self.content))

    async def generate(self, **kwargs):
        self.generate_calls.append(kwargs)
        return SimpleNamespace(response=self.content)


class FakeToolSdkClient:
    def __init__(self):
        self.chat_calls = []
        self.generate_calls = []

    async def chat(self, **kwargs):
        self.chat_calls.append(snapshot_call(kwargs))
        if len(self.chat_calls) == 1:
            return SimpleNamespace(
                message={
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {"function": {"name": "web_search", "arguments": {"query": "ollama"}}}
                    ],
                }
            )
        return SimpleNamespace(message={"role": "assistant", "content": "final answer"})


class FakeWebClient:
    def web_search(self, query: str, max_results: int = 3):
        return {
            "results": [
                {
                    "title": "Result One",
                    "url": "https://example.com/one",
                    "content": f"result for {query}\\nsecond line",
                }
            ]
        }

    def web_fetch(self, url: str):
        return f"content for {url}"


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
async def test_call_messages_uses_explicit_message_history():
    client = OllamaClient("http://localhost:11434", "test-model", temperature=0.3)
    fake_sdk = FakeSdkClient("hello")
    client.client = fake_sdk
    messages = [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "second"},
        {"role": "user", "content": "third"},
    ]

    response = await client.call_messages(messages)

    assert response.content == "hello"
    assert response.tool_events == []
    assert len(fake_sdk.chat_calls) == 1
    assert fake_sdk.chat_calls[0]["model"] == "test-model"
    assert fake_sdk.chat_calls[0]["messages"] == messages
    assert fake_sdk.chat_calls[0]["stream"] is False
    assert fake_sdk.chat_calls[0]["format"] is None
    assert fake_sdk.chat_calls[0]["options"] == {"temperature": 0.3}
    assert len(fake_sdk.chat_calls[0]["tools"]) == 2
    assert fake_sdk.chat_calls[0]["think"] is True
    assert fake_sdk.generate_calls == []


@pytest.mark.asyncio
async def test_call_messages_executes_web_tools(monkeypatch):
    client = OllamaClient("http://localhost:11434", "test-model")
    fake_sdk = FakeToolSdkClient()
    client.client = fake_sdk
    client.web_client = FakeWebClient()
    messages = [{"role": "user", "content": "search"}]

    response = await client.call_messages(messages)

    assert response.content == "final answer"
    assert len(response.tool_events) == 1
    assert response.tool_events[0].tool_name == "web_search"
    assert response.tool_events[0].arguments == {"query": "ollama"}
    assert response.tool_events[0].result == "1. Result One\nhttps://example.com/one\nresult for ollama\nsecond line"
    assert response.tool_events[0].failed is False
    assert len(fake_sdk.chat_calls) == 2
    assert fake_sdk.chat_calls[1]["messages"][-1] == {
        "role": "tool",
        "content": "1. Result One\nhttps://example.com/one\nresult for ollama\nsecond line",
        "tool_name": "web_search",
    }


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
