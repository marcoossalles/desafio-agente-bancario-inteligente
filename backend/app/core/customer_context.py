from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator


_authenticated_customer_cpf: ContextVar[str | None] = ContextVar(
    "authenticated_customer_cpf",
    default=None,
)


def normalize_cpf(cpf: str) -> str:
    return "".join(character for character in cpf if character.isdigit())


@contextmanager
def customer_context(cpf: str | None) -> Iterator[None]:
    normalized_cpf = normalize_cpf(cpf) if cpf else None
    token = _authenticated_customer_cpf.set(normalized_cpf)

    try:
        yield
    finally:
        _authenticated_customer_cpf.reset(token)


def authorize_customer(cpf: str) -> str:
    normalized_cpf = normalize_cpf(cpf)
    authenticated_cpf = _authenticated_customer_cpf.get()

    if not authenticated_cpf or normalized_cpf != authenticated_cpf:
        raise PermissionError(
            "A operação não está autorizada para o CPF informado."
        )

    return normalized_cpf
