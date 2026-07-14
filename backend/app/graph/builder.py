from functools import lru_cache

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    clarification_node,
    credit_interview_node,
    credit_node,
    exchange_node,
    finish_node,
    supervisor_node,
    triage_node,
)
from app.graph.routers import (
    route_after_credit_interview,
    route_after_supervisor,
)
from app.graph.state import BankingState


@lru_cache
def get_banking_graph():
    """Constrói e armazena em cache o grafo bancário com estado."""
    return build_banking_graph(InMemorySaver())


def build_banking_graph(checkpointer: BaseCheckpointSaver):
    """Constrói o grafo usando o checkpointer informado."""
    graph = StateGraph(BankingState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("triage", triage_node)
    graph.add_node("credit", credit_node)
    graph.add_node("credit_interview", credit_interview_node)
    graph.add_node("exchange", exchange_node)
    graph.add_node("clarification", clarification_node)
    graph.add_node("finish", finish_node)

    graph.add_edge(START, "supervisor")
    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "triage": "triage",
            "credit": "credit",
            "credit_interview": "credit_interview",
            "exchange": "exchange",
            "clarification": "clarification",
            "finish": "finish",
        },
    )

    graph.add_edge("triage", END)
    graph.add_edge("credit", END)
    graph.add_edge("exchange", END)
    graph.add_edge("clarification", END)
    graph.add_edge("finish", END)
    graph.add_conditional_edges(
        "credit_interview",
        route_after_credit_interview,
        {
            "credit": "credit",
            "end": END,
        },
    )

    return graph.compile(checkpointer=checkpointer)


def close_banking_graph() -> None:
    get_banking_graph.cache_clear()
