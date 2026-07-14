from langchain.tools import tool


@tool
def finish_conversation() -> dict:
    """Encerra a conversa atual de atendimento ao cliente.

    Use esta ferramenta quando o cliente pedir explicitamente para encerrar,
    interromper, cancelar, finalizar ou sair da conversa.
    """

    return {
        "conversation_finished": True,
        "message": (
            "Atendimento encerrado. Agradecemos por utilizar o Banco Ágil!"
        ),
    }
