import csv

import pytest

from app.repositories.customer_repository import CustomerRepository


@pytest.fixture
def customer_file(tmp_path):
    path = tmp_path / "clientes.csv"
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "cpf",
                "name",
                "birth_date",
                "credit_score",
                "credit_limit",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "cpf": "123.456.789-01",
                "name": "Cliente Teste",
                "birth_date": "1990-01-02",
                "credit_score": "700",
                "credit_limit": "2500.00",
            }
        )
    return path


def test_find_by_cpf_normalizes_value(customer_file):
    repository = CustomerRepository(customer_file)

    customer = repository.find_by_cpf("12345678901")

    assert customer is not None
    assert customer.name == "Cliente Teste"
    assert customer.credit_limit == 2500.0


def test_update_customer_fields_atomically(customer_file):
    repository = CustomerRepository(customer_file)

    repository.update_credit_limit("12345678901", 3100)
    repository.update_credit_score("12345678901", 755)

    customer = repository.find_by_cpf("12345678901")
    assert customer is not None
    assert customer.credit_limit == 3100.0
    assert customer.credit_score == 755


def test_default_data_path_is_independent_from_working_directory():
    repository = CustomerRepository()

    assert repository.file_path.is_absolute()
    assert repository.file_path.name == "clientes.csv"
