from app.models.credit_interview import ScoreUpdateResult
from app.repositories.customer_repository import CustomerRepository


class ScoreService:
    INCOME_WEIGHT = 30

    EMPLOYMENT_WEIGHTS = {
        "formal": 300,
        "autonomo": 200,
        "desempregado": 0,
    }

    DEPENDENT_WEIGHTS = {
        0: 100,
        1: 80,
        2: 60,
        3: 30,
    }

    DEBT_WEIGHTS = {
        True: -100,
        False: 100,
    }

    def __init__(
        self,
        customer_repository: CustomerRepository,
    ) -> None:
        self.customer_repository = customer_repository

    def calculate_and_update(
        self,
        cpf: str,
        monthly_income: float,
        employment_type: str,
        fixed_expenses: float,
        dependents: int,
        has_active_debts: bool,
    ) -> ScoreUpdateResult:
        customer = self.customer_repository.find_by_cpf(cpf)

        if customer is None:
            raise ValueError("Cliente não encontrado.")

        new_score = self.calculate_score(
            monthly_income=monthly_income,
            employment_type=employment_type,
            fixed_expenses=fixed_expenses,
            dependents=dependents,
            has_active_debts=has_active_debts,
        )

        previous_score = customer.credit_score

        self.customer_repository.update_credit_score(
            cpf=customer.cpf,
            new_credit_score=new_score,
        )

        return ScoreUpdateResult(
            previous_score=previous_score,
            new_score=new_score,
        )

    def calculate_score(
        self,
        monthly_income: float,
        employment_type: str,
        fixed_expenses: float,
        dependents: int,
        has_active_debts: bool,
    ) -> int:
        normalized_employment_type = (
            self._normalize_employment_type(employment_type)
        )

        self._validate_interview_data(
            monthly_income=monthly_income,
            employment_type=normalized_employment_type,
            fixed_expenses=fixed_expenses,
            dependents=dependents,
        )

        income_ratio = monthly_income / (fixed_expenses + 1)
        income_score = income_ratio * self.INCOME_WEIGHT

        dependent_group = min(dependents, 3)

        score = (
            income_score
            + self.EMPLOYMENT_WEIGHTS[normalized_employment_type]
            + self.DEPENDENT_WEIGHTS[dependent_group]
            + self.DEBT_WEIGHTS[has_active_debts]
        )

        return int(max(0, min(round(score), 1000)))

    def _validate_interview_data(
        self,
        monthly_income: float,
        employment_type: str,
        fixed_expenses: float,
        dependents: int,
    ) -> None:
        if monthly_income < 0:
            raise ValueError(
                "A renda mensal não pode ser negativa."
            )

        if fixed_expenses < 0:
            raise ValueError(
                "As despesas fixas não podem ser negativas."
            )

        if dependents < 0:
            raise ValueError(
                "O número de dependentes não pode ser negativo."
            )

        if employment_type not in self.EMPLOYMENT_WEIGHTS:
            raise ValueError(
                "O tipo de emprego deve ser formal, "
                "autônomo ou desempregado."
            )

    @staticmethod
    def _normalize_employment_type(
        employment_type: str,
    ) -> str:
        return (
            employment_type
            .strip()
            .lower()
            .replace("ô", "o")
            .replace("á", "a")
            .replace("ã", "a")
        )
