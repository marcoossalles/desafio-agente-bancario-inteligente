from datetime import date
from types import SimpleNamespace

from app.services.authentication_service import AuthenticationService
from app.tools.authentication_tools import authenticate_customer


class CustomerRepositoryStub:
    def __init__(self, customer):
        self.customer = customer

    def find_by_cpf(self, cpf):
        return self.customer


def test_authenticate_returns_customer_when_birth_date_matches():
    customer = SimpleNamespace(birth_date=date(1990, 1, 2))
    service = AuthenticationService(CustomerRepositoryStub(customer))

    assert service.authenticate("12345678901", date(1990, 1, 2)) is customer


def test_authenticate_rejects_wrong_birth_date():
    customer = SimpleNamespace(birth_date=date(1990, 1, 2))
    service = AuthenticationService(CustomerRepositoryStub(customer))

    assert service.authenticate("12345678901", date(1991, 1, 2)) is None


def test_example_customer_can_authenticate_against_default_database():
    result = authenticate_customer.invoke(
        {
            "cpf": "11111111111",
            "birth_date": "1990-05-15",
        }
    )

    assert result["authenticated"] is True
    assert result["customer"]["name"] == "Cliente Exemplo 1"
