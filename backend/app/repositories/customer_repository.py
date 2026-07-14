import csv
from datetime import date
from pathlib import Path

from app.models.customer import Customer


DEFAULT_CUSTOMER_FILE = (
    Path(__file__).resolve().parents[2] / "data" / "clientes.csv"
)


class CustomerRepository:
    def __init__(
        self,
        file_path: str | Path = DEFAULT_CUSTOMER_FILE,
    ) -> None:
        self.file_path = Path(file_path)

    def find_by_cpf(self, cpf: str) -> Customer | None:
        if not self.file_path.exists():
            raise FileNotFoundError(
                f"Arquivo de clientes não encontrado: {self.file_path}"
            )

        normalized_cpf = self._normalize_cpf(cpf)

        with self.file_path.open(
            mode="r",
            encoding="utf-8",
            newline="",
        ) as csv_file:
            reader = csv.DictReader(csv_file)

            for row in reader:
                row_cpf = self._normalize_cpf(row["cpf"])

                if row_cpf == normalized_cpf:
                    return Customer(
                        cpf=row_cpf,
                        name=row["name"],
                        birth_date=date.fromisoformat(
                            row["birth_date"]
                        ),
                        credit_score=int(row["credit_score"]),
                        credit_limit=float(row["credit_limit"]),
                    )

        return None

    def update_credit_limit(
        self,
        cpf: str,
        new_credit_limit: float,
    ) -> None:
        if new_credit_limit < 0:
            raise ValueError(
                "O limite de crédito não pode ser negativo."
            )

        self._update_customer_field(
            cpf=cpf,
            field_name="credit_limit",
            new_value=f"{new_credit_limit:.2f}",
        )

    def update_credit_score(
        self,
        cpf: str,
        new_credit_score: int,
    ) -> None:
        if not 0 <= new_credit_score <= 1000:
            raise ValueError(
                "O score de crédito deve estar entre 0 e 1000."
            )

        self._update_customer_field(
            cpf=cpf,
            field_name="credit_score",
            new_value=str(new_credit_score),
        )

    def _update_customer_field(
        self,
        cpf: str,
        field_name: str,
        new_value: str,
    ) -> None:
        if not self.file_path.exists():
            raise FileNotFoundError(
                f"Arquivo de clientes não encontrado: {self.file_path}"
            )

        normalized_cpf = self._normalize_cpf(cpf)

        with self.file_path.open(
            mode="r",
            encoding="utf-8",
            newline="",
        ) as csv_file:
            reader = csv.DictReader(csv_file)
            fieldnames = reader.fieldnames
            rows = list(reader)

        if not fieldnames:
            raise ValueError(
                "O arquivo de clientes não possui cabeçalho."
            )

        if field_name not in fieldnames:
            raise ValueError(
                f"O campo '{field_name}' não existe "
                "no arquivo de clientes."
            )

        customer_found = False

        for row in rows:
            row_cpf = self._normalize_cpf(row["cpf"])

            if row_cpf == normalized_cpf:
                row[field_name] = new_value
                customer_found = True
                break

        if not customer_found:
            raise ValueError(
                f"Cliente com CPF '{normalized_cpf}' não encontrado."
            )

        temporary_file = self.file_path.with_suffix(".tmp")

        try:
            with temporary_file.open(
                mode="w",
                encoding="utf-8",
                newline="",
            ) as csv_file:
                writer = csv.DictWriter(
                    csv_file,
                    fieldnames=fieldnames,
                )
                writer.writeheader()
                writer.writerows(rows)

            temporary_file.replace(self.file_path)

        except Exception:
            if temporary_file.exists():
                temporary_file.unlink()

            raise

    @staticmethod
    def _normalize_cpf(cpf: str) -> str:
        normalized_cpf = "".join(
            character
            for character in cpf
            if character.isdigit()
        )

        if len(normalized_cpf) != 11:
            raise ValueError(
                "O CPF deve conter exatamente 11 dígitos."
            )

        return normalized_cpf
