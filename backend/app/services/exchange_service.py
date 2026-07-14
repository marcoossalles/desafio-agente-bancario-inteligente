from datetime import datetime, timezone

import httpx

from app.config.settings import get_settings
from app.models.exchange_rate import ExchangeRate


class ExchangeService:
    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
    ) -> None:
        settings = get_settings()

        self.base_url = (
            base_url or settings.exchange_api_url
        ).rstrip("/")

        self.timeout = (
            timeout
            if timeout is not None
            else settings.exchange_api_timeout
        )

    def get_rate(
        self,
        source_currency: str,
        target_currency: str,
    ) -> ExchangeRate:
        source = self._normalize_currency(source_currency)
        target = self._normalize_currency(target_currency)

        if source == target:
            return ExchangeRate(
                source_currency=source,
                target_currency=target,
                rate=1.0,
                consulted_at=datetime.now(timezone.utc),
            )

        url = f"{self.base_url}/latest"

        params = {
            "base": source,
            "symbols": target,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    url,
                    params=params,
                )

                response.raise_for_status()

        except httpx.TimeoutException as error:
            raise TimeoutError(
                "A consulta ao serviço de câmbio excedeu o tempo limite."
            ) from error

        except httpx.HTTPStatusError as error:
            if error.response.status_code in {400, 404}:
                raise ValueError(
                    "Uma das moedas informadas não é suportada."
                ) from error

            raise RuntimeError(
                "O serviço de câmbio retornou uma resposta inválida."
            ) from error

        except httpx.RequestError as error:
            raise RuntimeError(
                "O serviço de câmbio está indisponível."
            ) from error

        data = response.json()
        rates = data.get("rates", {})

        rate = rates.get(target)

        if rate is None:
            raise ValueError(
                "Não foi encontrada cotação para as moedas informadas."
            )

        return ExchangeRate(
            source_currency=source,
            target_currency=target,
            rate=float(rate),
            consulted_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _normalize_currency(currency: str) -> str:
        normalized_currency = currency.strip().upper()

        if len(normalized_currency) != 3:
            raise ValueError(
                "O código da moeda deve possuir três letras."
            )

        if not normalized_currency.isalpha():
            raise ValueError(
                "O código da moeda deve conter apenas letras."
            )

        return normalized_currency
