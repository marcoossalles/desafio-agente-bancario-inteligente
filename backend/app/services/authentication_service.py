from datetime import date

from app.models.customer import Customer
from app.repositories.customer_repository import CustomerRepository


class AuthenticationService:
    def __init__(self, customer_repository: CustomerRepository) -> None:
        self.customer_repository = customer_repository

    def authenticate(
        self,
        cpf: str,
        birth_date: date,
    ) -> Customer | None:
        customer = self.customer_repository.find_by_cpf(cpf)

        if customer is None:
            return None

        if customer.birth_date != birth_date:
            return None

        return customer