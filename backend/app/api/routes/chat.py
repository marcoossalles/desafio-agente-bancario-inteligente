import logging
import json
from collections.abc import Iterator
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    HumanMessage,
)

from app.api.schemas.chat import ChatRequest
from app.graph.builder import get_banking_graph


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.post(
    "/stream",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
)
def chat_stream(request: ChatRequest) -> StreamingResponse:
    """Transmite a resposta do atendimento em eventos SSE."""
    thread_id = request.thread_id or str(uuid4())

    return StreamingResponse(
        _stream_chat_events(request, thread_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _stream_chat_events(
    request: ChatRequest,
    thread_id: str,
) -> Iterator[str]:
    config = {"configurable": {"thread_id": thread_id}}
    graph_input = {
        "messages": [HumanMessage(content=request.message.strip())]
    }
    final_state: dict[str, Any] = {}
    transmitted_content = False

    yield _encode_sse(
        "metadata",
        {"thread_id": thread_id},
    )

    try:
        graph = get_banking_graph()

        for part in graph.stream(
            graph_input,
            config,
            stream_mode=["messages", "values"],
            version="v2",
        ):
            if part["type"] == "values":
                final_state = part["data"]
                continue

            if part["type"] != "messages":
                continue

            message_chunk, metadata = part["data"]

            if not isinstance(message_chunk, AIMessageChunk):
                continue

            if "roteamento-interno" in metadata.get("tags", []):
                continue

            content = _extract_message_content(message_chunk)
            if not content:
                continue

            transmitted_content = True
            yield _encode_sse("token", {"content": content})

    except Exception:
        logger.exception(
            "Erro ao transmitir a conversa bancária.",
            extra={"thread_id": thread_id},
        )
        yield _encode_sse(
            "error",
            {
                "detail": (
                    "Não foi possível processar sua mensagem neste momento."
                )
            },
        )
        return

    response_message = _get_last_ai_message(
        messages=final_state.get("messages", []),
    )

    if response_message is None:
        logger.error(
            "O streaming não encontrou a resposta final da IA.",
            extra={"thread_id": thread_id},
        )
        yield _encode_sse(
            "error",
            {"detail": "O atendimento não conseguiu gerar uma resposta."},
        )
        return

    final_content = _extract_message_content(response_message)

    if final_content and not transmitted_content:
        yield _encode_sse("token", {"content": final_content})

    yield _encode_sse(
        "final",
        {
            "message": final_content,
            "thread_id": thread_id,
            "finished": final_state.get("conversation_finished", False),
            "current_agent": final_state.get("current_agent"),
        },
    )


def _encode_sse(event: str, data: dict[str, Any]) -> str:
    serialized_data = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {serialized_data}\n\n"


def _get_last_ai_message(
    messages: list,
) -> AIMessage | None:
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            return message

    return None


def _extract_message_content(
    message: AIMessage | AIMessageChunk,
) -> str:
    content = message.content

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts: list[str] = []

        for item in content:
            if isinstance(item, str):
                text_parts.append(item)
                continue

            if isinstance(item, dict):
                text = item.get("text")

                if isinstance(text, str):
                    text_parts.append(text)

        return "\n".join(text_parts)

    if content is None:
        return ""

    return str(content)
