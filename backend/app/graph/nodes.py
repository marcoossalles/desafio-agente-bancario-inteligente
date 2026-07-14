import ast
import json
import logging
from typing import Any

from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    ToolMessage,
)

from app.agents.credit_agent import get_credit_agent
from app.agents.credit_interview_agent import (
    get_credit_interview_agent,
)
from app.agents.exchange_agent import get_exchange_agent
from app.agents.triage_agent import get_triage_agent
from app.core.customer_context import customer_context
from app.graph.routers import classify_route
from app.graph.state import BankingState


logger = logging.getLogger(__name__)


AUTHENTICATION_ERRORS = {
    "invalid_cpf",
    "invalid_birth_date",
    "invalid_credentials",
}


def supervisor_node(
    state: BankingState,
) -> dict:
    decision = classify_route(state)

    logger.info(
        "Supervisor roteou para '%s' (intent=%s)",
        decision.destination,
        decision.intent,
    )

    update: dict[str, Any] = {
        "route": decision.destination,
        "intent": decision.intent,
    }

    if decision.destination == "credit_interview":
        update["interview_accepted"] = True

    return update


def triage_node(
    state: BankingState,
) -> dict:
    new_messages = _invoke_agent(
        agent=get_triage_agent(),
        state=state,
        node_name="triage",
    )

    update: dict[str, Any] = {
        "messages": new_messages,
        "current_agent": "triage",
        "error_message": None,
    }

    tool_arguments = _find_tool_arguments(
        messages=new_messages,
        tool_name="authenticate_customer",
    )

    if tool_arguments:
        cpf = tool_arguments.get("cpf")
        birth_date = tool_arguments.get("birth_date")

        if isinstance(cpf, str):
            update["cpf"] = _normalize_cpf(cpf)

        if isinstance(birth_date, str):
            update["birth_date"] = birth_date

    authentication_result = _find_tool_result(
        messages=new_messages,
        tool_name="authenticate_customer",
    )

    if authentication_result is None:
        finish_result = _find_tool_result(
            messages=new_messages,
            tool_name="finish_conversation",
        )

        if finish_result:
            update.update(
                _build_finish_update(finish_result)
            )

        return update

    if authentication_result.get("authenticated") is True:
        customer = authentication_result.get("customer", {})

        update.update(
            {
                "authenticated": True,
                "authentication_attempts": 0,
                "cpf": customer.get(
                    "cpf",
                    update.get("cpf"),
                ),
                "customer_name": customer.get("name"),
                "current_score": customer.get(
                    "credit_score"
                ),
                "current_credit_limit": customer.get(
                    "credit_limit"
                ),
                "conversation_finished": False,
            }
        )

        return update

    error_code = authentication_result.get("error")

    if error_code in AUTHENTICATION_ERRORS:
        attempts = (
            state.get("authentication_attempts", 0) + 1
        )

        update.update(
            {
                "authenticated": False,
                "authentication_attempts": attempts,
                "cpf": None,
                "birth_date": None,
                "error_message": authentication_result.get(
                    "message"
                ),
            }
        )

        if attempts >= 3:
            update.update(
                {
                    "conversation_finished": True,
                    "current_agent": "finish",
                    "messages": [
                        *new_messages,
                        AIMessage(
                            content=(
                                "Não foi possível autenticar seus "
                                "dados após três tentativas. "
                                "Por segurança, o atendimento será "
                                "encerrado. Você poderá iniciar um "
                                "novo atendimento mais tarde."
                            )
                        ),
                    ],
                }
            )

        return update

    update["error_message"] = authentication_result.get(
        "message"
    )

    return update


def credit_node(
    state: BankingState,
) -> dict:
    new_messages = _invoke_agent(
        agent=get_credit_agent(),
        state=state,
        node_name="credit",
    )

    update: dict[str, Any] = {
        "messages": new_messages,
        "current_agent": "credit",
        "error_message": None,
    }

    finish_result = _find_tool_result(
        messages=new_messages,
        tool_name="finish_conversation",
    )

    if finish_result:
        update.update(
            _build_finish_update(finish_result)
        )
        return update

    limit_result = _find_tool_result(
        messages=new_messages,
        tool_name="get_customer_credit_limit",
    )

    if (
        limit_result
        and limit_result.get("success") is True
    ):
        update["current_credit_limit"] = (
            limit_result.get("credit_limit")
        )

    request_arguments = _find_tool_arguments(
        messages=new_messages,
        tool_name="request_credit_limit_increase",
    )

    if request_arguments:
        requested_limit = request_arguments.get(
            "requested_limit"
        )

        if isinstance(requested_limit, (int, float)):
            update["requested_credit_limit"] = float(
                requested_limit
            )

    request_result = _find_tool_result(
        messages=new_messages,
        tool_name="request_credit_limit_increase",
    )

    if request_result is None:
        return update

    if request_result.get("success") is not True:
        update["error_message"] = request_result.get(
            "message"
        )
        return update

    status = request_result.get("status")

    if hasattr(status, "value"):
        status = status.value

    update.update(
        {
            "credit_request_status": status,
            "requested_credit_limit": (
                request_result.get("requested_limit")
            ),
        }
    )

    if status == "aprovado":
        update.update(
            {
                "current_credit_limit": (
                    request_result.get("requested_limit")
                ),
                "interview_accepted": False,
                "interview_completed": False,
            }
        )

    if status == "rejeitado":
        update.update(
            {
                "interview_accepted": False,
                "interview_completed": False,
            }
        )

    return update


def credit_interview_node(
    state: BankingState,
) -> dict:
    new_messages = _invoke_agent(
        agent=get_credit_interview_agent(),
        state=state,
        node_name="credit_interview",
    )

    update: dict[str, Any] = {
        "messages": new_messages,
        "current_agent": "credit_interview",
        "interview_accepted": True,
        "error_message": None,
    }

    finish_result = _find_tool_result(
        messages=new_messages,
        tool_name="finish_conversation",
    )

    if finish_result:
        update.update(
            _build_finish_update(finish_result)
        )
        return update

    score_result = _find_tool_result(
        messages=new_messages,
        tool_name="calculate_and_update_credit_score",
    )

    if score_result is None:
        return update

    if score_result.get("success") is not True:
        update["error_message"] = score_result.get(
            "message"
        )
        return update

    update.update(
        {
            "current_score": score_result.get("new_score"),
            "interview_completed": True,
            "current_agent": "credit",
        }
    )

    return update


def exchange_node(
    state: BankingState,
) -> dict:
    new_messages = _invoke_agent(
        agent=get_exchange_agent(),
        state=state,
        node_name="exchange",
    )

    update: dict[str, Any] = {
        "messages": new_messages,
        "current_agent": "exchange",
        "error_message": None,
    }

    finish_result = _find_tool_result(
        messages=new_messages,
        tool_name="finish_conversation",
    )

    if finish_result:
        update.update(
            _build_finish_update(finish_result)
        )
        return update

    exchange_result = _find_tool_result(
        messages=new_messages,
        tool_name="get_exchange_rate",
    )

    if exchange_result:
        if exchange_result.get("success") is True:
            update.update(
                {
                    "conversation_finished": True,
                    "current_agent": "finish",
                }
            )
        else:
            update["error_message"] = exchange_result.get(
                "message"
            )

    return update


def clarification_node(
    state: BankingState,
) -> dict:
    logger.info("Nó 'clarification' executado.")

    return {
        "messages": [
            AIMessage(
                content=(
                    "Posso ajudar com consulta ou aumento de "
                    "limite de crédito e também com cotação de "
                    "moedas. Qual desses serviços você deseja?"
                )
            )
        ],
        "error_message": None,
    }


def finish_node(
    state: BankingState,
) -> dict:
    logger.info("Nó 'finish' executado.")

    messages = state.get("messages", [])

    last_message = messages[-1] if messages else None

    # Evita duplicar a despedida quando um agente já retornou
    # uma mensagem após chamar finish_conversation.
    if (
        isinstance(last_message, AIMessage)
        and last_message.content
    ):
        return {
            "conversation_finished": True,
            "current_agent": "finish",
        }

    return {
        "messages": [
            AIMessage(
                content=(
                    "Atendimento encerrado. Agradecemos por "
                    "utilizar o Banco Ágil!"
                )
            )
        ],
        "conversation_finished": True,
        "current_agent": "finish",
    }


def _invoke_agent(
    agent: Any,
    state: BankingState,
    node_name: str,
) -> list[AnyMessage]:
    logger.info("Nó '%s' iniciado.", node_name)

    current_messages = state.get("messages", [])

    context_cpf = state.get("cpf") if state.get("authenticated") else None

    with customer_context(context_cpf):
        result = agent.invoke(
            {
                "messages": current_messages,
            }
        )

    result_messages = result.get("messages", [])

    # create_agent retorna as mensagens originais junto com
    # as novas mensagens da IA e das ferramentas.
    new_messages = result_messages[
        len(current_messages):
    ]

    if not new_messages:
        if not result_messages:
            raise RuntimeError(
                "O agente não retornou nenhuma mensagem."
            )

        new_messages = [result_messages[-1]]

    _log_agent_activity(node_name, new_messages)

    return new_messages


def _log_agent_activity(
    node_name: str,
    messages: list[AnyMessage],
) -> None:
    final_response: str | None = None

    for message in messages:
        if isinstance(message, AIMessage) and message.tool_calls:
            for tool_call in message.tool_calls:
                logger.info(
                    "[%s] chamou a ferramenta '%s' com argumentos %s",
                    node_name,
                    tool_call.get("name"),
                    tool_call.get("args"),
                )
            continue

        if isinstance(message, ToolMessage):
            logger.info(
                "[%s] resultado da ferramenta '%s': %s",
                node_name,
                message.name,
                _truncate(str(message.content)),
            )
            continue

        if isinstance(message, AIMessage):
            final_response = str(message.content)

    if final_response:
        logger.info(
            "[%s] respondeu: %s",
            node_name,
            _truncate(final_response),
        )


def _truncate(text: str, limit: int = 200) -> str:
    stripped = text.strip()

    if len(stripped) <= limit:
        return stripped

    return f"{stripped[:limit]}…"


def _find_tool_result(
    messages: list[AnyMessage],
    tool_name: str,
) -> dict[str, Any] | None:
    for message in reversed(messages):
        if not isinstance(message, ToolMessage):
            continue

        if message.name != tool_name:
            continue

        return _parse_tool_content(message.content)

    return None


def _find_tool_arguments(
    messages: list[AnyMessage],
    tool_name: str,
) -> dict[str, Any] | None:
    for message in reversed(messages):
        if not isinstance(message, AIMessage):
            continue

        for tool_call in reversed(message.tool_calls):
            if tool_call.get("name") != tool_name:
                continue

            arguments = tool_call.get("args", {})

            if isinstance(arguments, dict):
                return arguments

    return None


def _parse_tool_content(
    content: Any,
) -> dict[str, Any]:
    if isinstance(content, dict):
        return content

    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                if "text" in item:
                    parsed = _parse_tool_content(item["text"])

                    if parsed:
                        return parsed

                return item

        return {}

    if not isinstance(content, str):
        return {}

    stripped_content = content.strip()

    if not stripped_content:
        return {}

    try:
        parsed = json.loads(stripped_content)

        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    try:
        parsed = ast.literal_eval(stripped_content)

        if isinstance(parsed, dict):
            return parsed
    except (ValueError, SyntaxError):
        pass

    return {
        "message": stripped_content,
    }


def _build_finish_update(
    result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "conversation_finished": True,
        "current_agent": "finish",
    }


def _normalize_cpf(cpf: str) -> str:
    return "".join(
        character
        for character in cpf
        if character.isdigit()
    )
