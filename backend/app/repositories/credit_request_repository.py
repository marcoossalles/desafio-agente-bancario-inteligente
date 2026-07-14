import csv
from pathlib import Path

from app.models.credit_request import CreditRequest


DEFAULT_CREDIT_REQUEST_FILE = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "solicitacoes_aumento_limite.csv"
)


class CreditRequestRepository:
    FIELDNAMES = [
        "cpf_cliente",
        "data_hora_solicitacao",
        "limite_atual",
        "novo_limite_solicitado",
        "status_pedido",
    ]

    def __init__(
        self,
        file_path: str | Path = DEFAULT_CREDIT_REQUEST_FILE,
    ) -> None:
        self.file_path = Path(file_path)

    def save(self, credit_request: CreditRequest) -> None:
        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        file_exists = self.file_path.exists()
        file_is_empty = (
            not file_exists or self.file_path.stat().st_size == 0
        )

        needs_leading_newline = (
            not file_is_empty
            and not self._file_ends_with_newline()
        )

        with self.file_path.open(
            mode="a",
            encoding="utf-8",
            newline="",
        ) as csv_file:
            if needs_leading_newline:
                csv_file.write("\n")

            writer = csv.DictWriter(
                csv_file,
                fieldnames=self.FIELDNAMES,
            )

            if file_is_empty:
                writer.writeheader()

            writer.writerow(
                {
                    "cpf_cliente": credit_request.cpf,
                    "data_hora_solicitacao": (
                        credit_request.requested_at.isoformat()
                    ),
                    "limite_atual": (
                        f"{credit_request.current_limit:.2f}"
                    ),
                    "novo_limite_solicitado": (
                        f"{credit_request.requested_limit:.2f}"
                    ),
                    "status_pedido": credit_request.status.value,
                }
            )

    def _file_ends_with_newline(self) -> bool:
        with self.file_path.open(mode="rb") as csv_file:
            csv_file.seek(-1, 2)
            return csv_file.read(1) in (b"\n", b"\r")
