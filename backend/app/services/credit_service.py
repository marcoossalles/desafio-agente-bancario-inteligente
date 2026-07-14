from datetime import datetime, timezone
from uuid import uuid4

from app.models.credit_request import (
    CreditRequest,
    CreditRequestResult,
    CreditRequestStatus,
)
from app.repositories.credit_request_repository import (
    CreditRequestRepository,
)
from app.repositories.customer_repository import CustomerRepository
from app.repositories.score_limit_repository import (
    ScoreLimitRepository,
)


class CreditService:
    def __init__(
        self,
        customer_repository: CustomerRepository,
        score_limit_repository: ScoreLimitRepository,
        credit_request_repository: CreditRequestRepository,
    ) -> None:
        self.customer_repository = customer_repository
        self.score_limit_repository = score_limit_repository
        self.credit_request_repository = (
            credit_request_repository
        )

    def request_limit_increase(
        self,
        cpf: str,
        requested_limit: float,
    ) -> CreditRequestResult:
        customer = self.customer_repository.find_by_cpf(cpf)

        if customer is None:
            raise ValueError("Cliente não encontrado.")

        if requested_limit <= customer.credit_limit:
            raise ValueError(
                "O novo limite deve ser maior que o limite atual."
            )

        score_limit_range = (
            self.score_limit_repository.find_by_score(
                customer.credit_score
            )
        )

        if score_limit_range is None:
            raise ValueError(
                "Não foi encontrada uma faixa para o score atual."
            )

        request_status = CreditRequestStatus.PENDING

        credit_request = CreditRequest(
            request_id=str(uuid4()),
            cpf=customer.cpf,
            requested_at=datetime.now(timezone.utc),
            current_limit=customer.credit_limit,
            requested_limit=requested_limit,
            status=request_status,
        )

        if (
            requested_limit
            <= score_limit_range.maximum_credit_limit
        ):
            credit_request.status = CreditRequestStatus.APPROVED

            self.customer_repository.update_credit_limit(
                cpf=customer.cpf,
                new_credit_limit=requested_limit,
            )

            message = (
                "A solicitação de aumento de limite foi aprovada."
            )
        else:
            credit_request.status = CreditRequestStatus.REJECTED

            message = (
                "A solicitação de aumento de limite foi rejeitada "
                "de acordo com o score atual."
            )

        self.credit_request_repository.save(credit_request)

        return CreditRequestResult(
            request_id=credit_request.request_id,
            cpf=credit_request.cpf,
            current_limit=credit_request.current_limit,
            requested_limit=credit_request.requested_limit,
            status=credit_request.status,
            message=message,
        )