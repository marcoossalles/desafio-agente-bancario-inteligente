from langchain.tools import tool

from app.services.exchange_service import ExchangeService


exchange_service = ExchangeService()


@tool
def get_exchange_rate(
    source_currency: str,
    target_currency: str = "BRL",
) -> dict:
    """Consulta a cotação de câmbio mais recente disponível.

    Argumentos:
        source_currency: Código ISO 4217 da moeda de origem, como USD ou EUR.
        target_currency: Código ISO 4217 da moeda de destino. Padrão: BRL.

    Retorno:
        Taxa de câmbio e horário da consulta.
    """

    normalized_source = source_currency.strip().upper()
    normalized_target = target_currency.strip().upper()

    try:
        result = exchange_service.get_rate(
            source_currency=normalized_source,
            target_currency=normalized_target,
        )

        return {
            "success": True,
            "source_currency": result.source_currency,
            "target_currency": result.target_currency,
            "rate": result.rate,
            "consulted_at": result.consulted_at.isoformat(),
            "message": "Cotação consultada com sucesso.",
        }

    except ValueError as error:
        return {
            "success": False,
            "error": "invalid_or_unsupported_currency",
            "message": str(error),
        }

    except TimeoutError:
        return {
            "success": False,
            "error": "exchange_service_timeout",
            "message": (
                "O serviço de câmbio demorou para responder."
            ),
        }

    except RuntimeError:
        return {
            "success": False,
            "error": "exchange_service_unavailable",
            "message": (
                "Não foi possível consultar a cotação neste momento."
            ),
        }

    except Exception:
        return {
            "success": False,
            "error": "unexpected_error",
            "message": (
                "Ocorreu um erro inesperado ao consultar a cotação."
            ),
        }
