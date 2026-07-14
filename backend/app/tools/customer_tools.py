from langchain.tools import tool

from app.core.customer_context import authorize_customer
from app.repositories.customer_repository import CustomerRepository


customer_repository = CustomerRepository()


@tool
def get_customer_profile(cpf: str) -> dict:
    """Consulta o perfil de um cliente autenticado.

    Esta ferramenta é destinada às operações bancárias internas.

    Argumentos:
        cpf: CPF do cliente autenticado.

    Retorno:
        Nome, score e limite de crédito do cliente.
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
            "customer": {
                "cpf": customer.cpf,
                "name": customer.name,
                "credit_score": customer.credit_score,
                "credit_limit": customer.credit_limit,
            },
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
            "message": "Não foi possível consultar os dados do cliente.",
        }
