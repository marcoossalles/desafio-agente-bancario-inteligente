import csv
from pathlib import Path

from app.models.credit_interview import ScoreLimitRange


DEFAULT_SCORE_LIMIT_FILE = (
    Path(__file__).resolve().parents[2] / "data" / "score_limite.csv"
)


class ScoreLimitRepository:
    def __init__(
        self,
        file_path: str | Path = DEFAULT_SCORE_LIMIT_FILE,
    ) -> None:
        self.file_path = Path(file_path)

    def find_by_score(self, score: int) -> ScoreLimitRange | None:
        if not 0 <= score <= 1000:
            raise ValueError(
                "O score de crédito deve estar entre 0 e 1000."
            )

        if not self.file_path.exists():
            raise FileNotFoundError(
                "Arquivo de faixas de score não encontrado: "
                f"{self.file_path}"
            )

        with self.file_path.open(
            mode="r",
            encoding="utf-8",
            newline="",
        ) as csv_file:
            reader = csv.DictReader(csv_file)

            for row in reader:
                score_range = ScoreLimitRange(
                    minimum_score=int(row["minimum_score"]),
                    maximum_score=int(row["maximum_score"]),
                    maximum_credit_limit=float(
                        row["maximum_credit_limit"]
                    ),
                )

                if (
                    score_range.minimum_score
                    <= score
                    <= score_range.maximum_score
                ):
                    return score_range

        return None
