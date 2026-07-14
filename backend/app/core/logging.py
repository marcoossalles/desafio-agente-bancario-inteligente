import logging
import sys


NOISY_LOGGERS = (
    "asyncio",
    "groq",
    "httpcore",
    "httpx",
    "langchain",
    "langgraph",
    "watchfiles",
)


def configure_logging(
    log_level: str = "INFO",
) -> None:
    application_level = getattr(
        logging,
        log_level.upper(),
        logging.INFO,
    )

    logging.basicConfig(
        level=logging.WARNING,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )

    logging.addLevelName(logging.DEBUG, "DEPURAÇÃO")
    logging.addLevelName(logging.INFO, "INFO")
    logging.addLevelName(logging.WARNING, "AVISO")
    logging.addLevelName(logging.ERROR, "ERRO")
    logging.addLevelName(logging.CRITICAL, "CRÍTICO")

    logging.getLogger("app").setLevel(application_level)

    for logger_name in NOISY_LOGGERS:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
