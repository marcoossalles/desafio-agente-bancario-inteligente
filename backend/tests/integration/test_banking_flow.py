import json
from types import SimpleNamespace
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.messages import AIMessageChunk
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import ValidationError

from app.api.schemas.chat import ChatRequest
from app.api.routes import chat as chat_routes
from app.config.settings import Settings
from app.graph import nodes
from app.graph.builder import build_banking_graph


class SuccessfulExchangeAgentStub:
    def invoke(self, payload):
        return {
            "messages": [
                *payload["messages"],
                ToolMessage(
                    content=json.dumps(
                        {
                            "success": True,
                            "source_currency": "USD",
                            "target_currency": "BRL",
                            "rate": 5.25,
                        }
                    ),
                    name="get_exchange_rate",
                    tool_call_id="exchange-call",
                ),
                AIMessage(
                    content=(
                        "A cotação de USD para BRL é 5,25. "
                        "Obrigado por utilizar o Banco Ágil!"
                    )
                ),
            ]
        }


class StreamingBankGraphStub:
    def stream(self, *args, **kwargs):
        yield {
            "type": "messages",
            "data": (
                AIMessageChunk(content='{"destination":"triage"}'),
                {"tags": ["roteamento-interno"]},
            ),
        }
        yield {
            "type": "messages",
            "data": (
                AIMessageChunk(content="Olá"),
                {"tags": []},
            ),
        }
        yield {
            "type": "values",
            "data": {
                "messages": [AIMessage(content="Olá")],
                "conversation_finished": False,
                "current_agent": "triage",
            },
        }


def test_graph_can_finish_without_calling_the_llm(monkeypatch):
    monkeypatch.setattr(
        nodes,
        "classify_route",
        lambda state: SimpleNamespace(destination="finish", intent="finish"),
    )
    graph = build_banking_graph(InMemorySaver())

    result = graph.invoke(
        {"messages": [HumanMessage(content="Quero encerrar")]},
        {"configurable": {"thread_id": str(uuid4())}},
    )

    assert result["conversation_finished"] is True
    assert result["current_agent"] == "finish"
    assert result["messages"][-1].content.startswith("Atendimento encerrado")


def test_chat_request_rejects_blank_message():
    with pytest.raises(ValidationError):
        ChatRequest(message="   ")


def test_release_debug_value_is_parsed_as_false():
    settings = Settings(
        _env_file=None,
        groq_api_key="test-key",
        debug="release",
    )

    assert settings.debug is False


def test_successful_exchange_quote_does_not_force_conversation_end(
    monkeypatch,
):
    monkeypatch.setattr(
        nodes,
        "get_exchange_agent",
        lambda: SuccessfulExchangeAgentStub(),
    )

    result = nodes.exchange_node(
        {
            "messages": [HumanMessage(content="Cotação do dólar")],
            "authenticated": True,
            "cpf": "11111111111",
        }
    )

    assert result["current_agent"] == "exchange"
    assert result.get("conversation_finished") is None
    assert result["error_message"] is None


def test_chat_stream_transmits_tokens_without_internal_routing(monkeypatch):
    monkeypatch.setattr(
        chat_routes,
        "get_banking_graph",
        lambda: StreamingBankGraphStub(),
    )

    events = "".join(
        chat_routes._stream_chat_events(
            ChatRequest(message="Olá"),
            "thread-1",
        )
    )

    assert 'event: metadata' in events
    assert '"content": "Olá"' in events
    assert 'event: final' in events
    assert '"destination"' not in events
