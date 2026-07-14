from langchain.tools import tool

from app.core.customer_context import authorize_customer
from app.repositories.credit_request_repository import CreditRequestRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.score_limit_repository import ScoreLimitRepository
from app.services.credit_service import CreditService


customer_repository = CustomerRepository()
score_limit_repository = ScoreLimitRepository()
credit_request_repository = CreditRequestRepository()

credit_service = CreditService(
    customer_repository=customer_repository,
    score_limit_repository=score_limit_repository,
    credit_request_repository=credit_request_repository,
)


@tool
def get_customer_credit_limit(cpf: str) -> dict:
    """Consulta o limite de crédito atual de um cliente autenticado.

    Argumentos:
        cpf: CPF do cliente autenticado.

    Retorno:
        Limite atual ou um erro controlado.
    """

    try:
        authorized_cpf = authorize_customer(cpf)
        customer = customer_repository.find_by_cpf(authorized_cpf)

        if customer is None:
            return {
                "success": False,
                "error": "customer_not_found",
                "message": "Cliente não encontrado.",
            }

        return {
            "success": True,
            "cpf": customer.cpf,
            "credit_limit": customer.credit_limit,
            "message": "Limite de crédito consultado com sucesso.",
        }

    except PermissionError as error:
        return {
            "success": False,
            "error": "unauthorized_customer",
            "message": str(error),
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "customer_database_unavailable",
            "message": "A base de clientes está indisponível.",
        }
    except Exception:
        return {
            "success": False,
            "error": "unexpected_error",
            "message": "Não foi possível consultar o limite neste momento.",
        }


@tool
def request_credit_limit_increase(
    cpf: str,
    requested_limit: float,
) -> dict:
    """Cria e avalia uma solicitação de novo limite total de crédito.

    Argumentos:
        cpf: CPF do cliente autenticado.
        requested_limit: Novo limite total solicitado pelo cliente.

    Retorno:
        Status, limite atual, limite solicitado e resultado da análise.
    """

    if requested_limit <= 0:
        return {
            "success": False,
            "error": "invalid_requested_limit",
            "message": "O limite solicitado deve ser maior que zero.",
        }

    try:
        authorized_cpf = authorize_customer(cpf)
        result = credit_service.request_limit_increase(
            cpf=authorized_cpf,
            requested_limit=requested_limit,
        )

        return {
            "success": True,
            "request_id": result.request_id,
            "cpf": result.cpf,
            "current_limit": result.current_limit,
            "requested_limit": result.requested_limit,
            "status": result.status,
            "interview_available": result.status == "rejeitado",
            "message": result.message,
        }

    except PermissionError as error:
        return {
            "success": False,
            "error": "unauthorized_customer",
            "message": str(error),
        }
    except ValueError as error:
        return {
            "success": False,
            "error": "invalid_credit_request",
            "message": str(error),
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "credit_database_unavailable",
            "message": "Não foi possível acessar os dados de crédito.",
        }
    except Exception:
        return {
            "success": False,
            "error": "unexpected_error",
            "message": (
                "Não foi possível processar a solicitação de aumento."
            ),
        }
