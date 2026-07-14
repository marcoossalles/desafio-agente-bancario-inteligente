import json
import os
from collections.abc import Iterable, Iterator
from typing import Any

import httpx


DEFAULT_API_URL = "http://localhost:8000/api/v1"


class BankingAPIError(RuntimeError):
    """Representa uma falha controlada na comunicação com o backend."""


def iter_sse_events(
    lines: Iterable[str],
) -> Iterator[tuple[str, dict[str, Any]]]:
    """Converte as linhas do protocolo SSE em eventos estruturados."""
    event_name = "message"
    data_lines: list[str] = []

    for line in lines:
        if not line:
            if data_lines:
                yield event_name, json.loads("\n".join(data_lines))
            event_name = "message"
            data_lines = []
            continue

        if line.startswith("event:"):
            event_name = line.removeprefix("event:").strip()
        elif line.startswith("data:"):
            data_lines.append(line.removeprefix("data:").strip())

    if data_lines:
        yield event_name, json.loads("\n".join(data_lines))


def stream_chat(
    message: str,
    thread_id: str | None,
    result: dict[str, Any],
    api_url: str | None = None,
) -> Iterator[str]:
    """Envia uma mensagem e produz os trechos recebidos do backend."""
    base_url = (
        api_url
        or os.getenv("BACKEND_API_URL")
        or DEFAULT_API_URL
    ).rstrip("/")
    payload: dict[str, Any] = {"message": message}

    if thread_id:
        payload["thread_id"] = thread_id

    timeout = httpx.Timeout(120.0, connect=5.0)

    try:
        with httpx.stream(
            "POST",
            f"{base_url}/chat/stream",
            json=payload,
            timeout=timeout,
        ) as response:
            if response.is_error:
                response.read()
                detail = _extract_error_detail(response)
                raise BankingAPIError(detail)

            for event_name, data in iter_sse_events(
                response.iter_lines()
            ):
                if event_name == "metadata":
                    result["thread_id"] = data.get("thread_id")
                elif event_name == "token":
                    content = data.get("content", "")
                    if content:
                        yield content
                elif event_name == "final":
                    result.update(data)
                elif event_name == "error":
                    raise BankingAPIError(
                        data.get(
                            "detail",
                            "O atendimento encontrou um erro inesperado.",
                        )
                    )

    except httpx.RequestError as error:
        raise BankingAPIError(
            "Não foi possível conectar ao atendimento do Banco Ágil."
        ) from error


def _extract_error_detail(response: httpx.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        return "O backend retornou uma resposta inválida."

    return data.get(
        "detail",
        "Não foi possível processar a mensagem.",
    )
