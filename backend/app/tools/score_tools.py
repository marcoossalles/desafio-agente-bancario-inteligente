from langchain.tools import tool

from app.core.customer_context import authorize_customer
from app.repositories.customer_repository import CustomerRepository
from app.services.score_service import ScoreService


customer_repository = CustomerRepository()

score_service = ScoreService(
    customer_repository=customer_repository,
)


@tool
def calculate_and_update_credit_score(
    cpf: str,
    monthly_income: float,
    employment_type: str,
    fixed_expenses: float,
    dependents: int,
    has_active_debts: bool,
) -> dict:
    """Calcula e atualiza o score de crédito do cliente autenticado.

    Use somente após coletar todos os dados da entrevista financeira.

    Argumentos:
        cpf: CPF do cliente autenticado.
        monthly_income: Renda mensal do cliente.
        employment_type: formal, autonomo ou desempregado.
        fixed_expenses: Despesas fixas mensais do cliente.
        dependents: Número de dependentes financeiros.
        has_active_debts: Indica se o cliente possui dívidas ativas.

    Retorno:
        Score anterior, novo score e status da atualização.
    """

    normalized_cpf = "".join(
        character for character in cpf if character.isdigit()
    )

    if len(normalized_cpf) != 11:
        return {
            "success": False,
            "error": "invalid_cpf",
            "message": "O CPF deve conter 11 dígitos.",
        }

    if monthly_income < 0:
        return {
            "success": False,
            "error": "invalid_monthly_income",
            "message": "A renda mensal não pode ser negativa.",
        }

    if fixed_expenses < 0:
        return {
            "success": False,
            "error": "invalid_fixed_expenses",
            "message": "As despesas fixas não podem ser negativas.",
        }

    if dependents < 0:
        return {
            "success": False,
            "error": "invalid_dependents",
            "message": "O número de dependentes não pode ser negativo.",
        }

    normalized_employment_type = (
        employment_type.strip().lower()
        .replace("ô", "o")
        .replace("á", "a")
        .replace("ã", "a")
    )

    allowed_employment_types = {
        "formal",
        "autonomo",
        "desempregado",
    }

    if normalized_employment_type not in allowed_employment_types:
        return {
            "success": False,
            "error": "invalid_employment_type",
            "message": (
                "O tipo de emprego deve ser formal, "
                "autônomo ou desempregado."
            ),
        }

    try:
        authorized_cpf = authorize_customer(normalized_cpf)
        result = score_service.calculate_and_update(
            cpf=authorized_cpf,
            monthly_income=monthly_income,
            employment_type=normalized_employment_type,
            fixed_expenses=fixed_expenses,
            dependents=dependents,
            has_active_debts=has_active_debts,
        )

        return {
            "success": True,
            "cpf": normalized_cpf,
            "previous_score": result.previous_score,
            "new_score": result.new_score,
            "message": "Score recalculado e atualizado com sucesso.",
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
            "error": "invalid_interview_data",
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
            "message": "Não foi possível atualizar o score neste momento.",
        }
