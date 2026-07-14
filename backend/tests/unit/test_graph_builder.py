from langgraph.checkpoint.memory import InMemorySaver

from app.graph import builder


def test_graph_can_be_built_with_explicit_checkpointer():
    checkpointer = InMemorySaver()

    graph = builder.build_banking_graph(checkpointer)

    assert graph.checkpointer is checkpointer
