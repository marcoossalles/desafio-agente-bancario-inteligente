from datetime import date

from langchain.tools import tool

from app.repositories.customer_repository import CustomerRepository
from app.services.authentication_service import AuthenticationService


customer_repository = CustomerRepository()
authentication_service = AuthenticationService(customer_repository)


@tool
def authenticate_customer(cpf: str, birth_date: str) -> dict:
    """Autentica um cliente usando CPF e data de nascimento.

    Argumentos:
        cpf: CPF do cliente com ou sem pontuação.
        birth_date: Data de nascimento no formato ISO AAAA-MM-DD.

    Retorno:
        Resultado da autenticação e dados do cliente em caso de sucesso.
    """

    normalized_cpf = "".join(character for character in cpf if character.isdigit())

    if len(normalized_cpf) != 11:
        return {
            "authenticated": False,
            "error": "invalid_cpf",
            "message": "O CPF informado deve conter 11 dígitos.",
        }

    try:
        parsed_birth_date = date.fromisoformat(birth_date)
    except ValueError:
        return {
            "authenticated": False,
            "error": "invalid_birth_date",
            "message": "A data de nascimento informada é inválida.",
        }

    try:
        customer = authentication_service.authenticate(
            cpf=normalized_cpf,
            birth_date=parsed_birth_date,
        )
    except FileNotFoundError:
        return {
            "authenticated": False,
            "error": "customer_database_unavailable",
            "message": (
                "Não foi possível acessar a base de clientes neste momento."
            ),
        }
    except Exception:
        return {
            "authenticated": False,
            "error": "unexpected_error",
            "message": "Ocorreu um erro inesperado durante a autenticação.",
        }

    if customer is None:
        return {
            "authenticated": False,
            "error": "invalid_credentials",
            "message": "CPF ou data de nascimento não conferem.",
        }

    return {
        "authenticated": True,
        "customer": {
            "cpf": customer.cpf,
            "name": customer.name,
            "credit_score": customer.credit_score,
            "credit_limit": customer.credit_limit,
        },
        "message": "Cliente autenticado com sucesso.",
    }
