import csv
from datetime import datetime, timezone
from types import SimpleNamespace

from app.core.customer_context import customer_context
from app.models.credit_request import CreditRequest, CreditRequestStatus
from app.repositories.credit_request_repository import CreditRequestRepository
from app.services.credit_service import CreditService
from app.tools import credit_tools


class CustomerRepositoryStub:
    def __init__(self):
        self.customer = SimpleNamespace(
            cpf="12345678901",
            credit_score=700,
            credit_limit=2000.0,
        )
        self.updated_limit = None

    def find_by_cpf(self, cpf):
        return self.customer

    def update_credit_limit(self, cpf, new_credit_limit):
        self.updated_limit = new_credit_limit


class ScoreLimitRepositoryStub:
    def find_by_score(self, score):
        return SimpleNamespace(maximum_credit_limit=5000.0)


class CreditRequestRepositoryStub:
    def __init__(self):
        self.saved = None

    def save(self, request):
        self.saved = request


def test_approved_request_updates_limit_and_is_persisted():
    customers = CustomerRepositoryStub()
    requests = CreditRequestRepositoryStub()
    service = CreditService(
        customers,
        ScoreLimitRepositoryStub(),
        requests,
    )

    result = service.request_limit_increase("12345678901", 4000.0)

    assert result.status is CreditRequestStatus.APPROVED
    assert customers.updated_limit == 4000.0
    assert requests.saved.status is CreditRequestStatus.APPROVED


def test_credit_tool_rejects_cpf_different_from_authenticated_customer():
    with customer_context("12345678901"):
        result = credit_tools.get_customer_credit_limit.invoke(
            {"cpf": "99999999999"}
        )

    assert result["success"] is False
    assert result["error"] == "unauthorized_customer"


def test_credit_request_csv_uses_required_portuguese_status(tmp_path):
    output_file = tmp_path / "solicitacoes.csv"
    repository = CreditRequestRepository(output_file)
    repository.save(
        CreditRequest(
            request_id="request-id",
            cpf="12345678901",
            requested_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            current_limit=2000,
            requested_limit=4000,
            status=CreditRequestStatus.APPROVED,
        )
    )

    with output_file.open(encoding="utf-8", newline="") as csv_file:
        row = next(csv.DictReader(csv_file))

    assert row["status_pedido"] == "aprovado"


def test_all_credit_status_values_match_the_challenge():
    assert {status.value for status in CreditRequestStatus} == {
        "pendente",
        "aprovado",
        "rejeitado",
    }
