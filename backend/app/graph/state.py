from typing import Annotated, Literal

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


AgentName = Literal[
    "triage",
    "credit",
    "credit_interview",
    "exchange",
    "finish",
]

IntentName = Literal[
    "credit",
    "credit_interview",
    "exchange",
    "finish",
    "unknown",
]

RouteName = Literal[
    "triage",
    "credit",
    "credit_interview",
    "exchange",
    "clarification",
    "finish",
]


class BankingState(TypedDict, total=False):
    # Histórico da conversa
    messages: Annotated[list[AnyMessage], add_messages]

    # Roteamento
    route: RouteName
    intent: IntentName
    current_agent: AgentName

    # Autenticação
    authenticated: bool
    authentication_attempts: int
    cpf: str | None
    birth_date: str | None
    customer_name: str | None

    # Dados bancários do cliente
    current_score: int | None
    current_credit_limit: float | None

    # Solicitação de crédito
    requested_credit_limit: float | None
    credit_request_status: Literal[
        "pendente",
        "aprovado",
        "rejeitado",
    ] | None

    # Entrevista de crédito
    interview_accepted: bool
    interview_completed: bool

    # Conversa
    conversation_finished: bool
    error_message: str | None
