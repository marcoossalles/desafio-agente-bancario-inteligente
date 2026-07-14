from functools import lru_cache
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from app.graph.state import BankingState, RouteName
from app.llm.model import get_llm


class RouteDecision(BaseModel):
    destination: Literal[
        "triage",
        "credit",
        "credit_interview",
        "exchange",
        "clarification",
        "finish",
    ] = Field(
        description="Próximo destino no fluxo de atendimento bancário."
    )

    intent: Literal[
        "credit",
        "credit_interview",
        "exchange",
        "finish",
        "unknown",
    ] = Field(
        description="Intenção identificada na mensagem do cliente."
    )


SUPERVISOR_SYSTEM_PROMPT = """
Você é o supervisor interno de roteamento do Banco Ágil.

Sua única tarefa é determinar qual especialista deve atender a mensagem mais
recente do cliente.

Destinos disponíveis:

- triage:
  Autenticação do cliente, coleta de CPF ou data de nascimento.

- credit:
  Consulta ou aumento do limite, resultado de solicitação ou continuação de
  uma operação de crédito.

- credit_interview:
  Entrevista financeira após uma solicitação rejeitada, somente quando o
  cliente aceitou a entrevista ou já está participando dela.

- exchange:
  Consulta de cotação ou taxa de câmbio.

- clarification:
  A intenção do cliente não está clara ou não corresponde aos serviços
  bancários disponíveis.

- finish:
  O cliente deseja explicitamente encerrar, interromper ou cancelar a conversa.

Regras obrigatórias:

1. Um cliente não autenticado deve sempre ser encaminhado para triage, exceto
   quando solicitar explicitamente o encerramento da conversa.

2. Se uma entrevista de crédito foi iniciada e ainda não terminou, continue
   encaminhando para credit_interview.

3. Se uma solicitação foi rejeitada e o cliente aceitou a entrevista
   financeira oferecida, encaminhe para credit_interview.

4. Nunca encaminhe um cliente não autenticado diretamente para credit,
   exchange ou credit_interview.

5. Encaminhe para finish somente quando o cliente solicitar claramente o fim
   do atendimento.

6. Retorne apenas a decisão estruturada de roteamento.
"""


@lru_cache
def get_route_classifier():
    return get_llm().with_structured_output(RouteDecision)


def classify_route(state: BankingState) -> RouteDecision:
    latest_user_message = get_latest_user_message(state)

    authenticated = state.get("authenticated", False)
    current_agent = state.get("current_agent")
    credit_status = state.get("credit_request_status")
    interview_completed = state.get("interview_completed", False)
    conversation_finished = state.get(
        "conversation_finished",
        False,
    )

    if conversation_finished:
        return RouteDecision(
            destination="finish",
            intent="finish",
        )

    context = f"""
Estado bancário atual:

authenticated: {authenticated}
current_agent: {current_agent}
credit_request_status: {credit_status}
interview_completed: {interview_completed}

Mensagem mais recente do cliente:

{latest_user_message}
"""

    decision = get_route_classifier().invoke(
        [
            SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
            HumanMessage(content=context),
        ],
        config={"tags": ["roteamento-interno"]},
    )

    # Regra determinística de segurança:
    # o modelo não pode ignorar a autenticação.
    if (
        not authenticated
        and decision.destination != "finish"
    ):
        return RouteDecision(
            destination="triage",
            intent=decision.intent,
        )

    # Mantém o cliente em uma entrevista ainda não concluída.
    if (
        current_agent == "credit_interview"
        and not interview_completed
        and decision.destination != "finish"
    ):
        return RouteDecision(
            destination="credit_interview",
            intent="credit_interview",
        )

    return decision


def route_after_supervisor(
    state: BankingState,
) -> RouteName:
    return state.get("route", "clarification")


def route_after_credit_interview(
    state: BankingState,
) -> Literal["credit", "end"]:
    if state.get("conversation_finished", False):
        return "end"

    if state.get("interview_completed", False):
        return "credit"

    return "end"


def get_latest_user_message(
    state: BankingState,
) -> str:
    messages = state.get("messages", [])

    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            content = message.content

            if isinstance(content, str):
                return content

            return str(content)

    return ""
