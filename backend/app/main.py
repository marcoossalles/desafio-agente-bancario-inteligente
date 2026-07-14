from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.chat import router as chat_router
from app.core.logging import configure_logging
from app.config.settings import get_settings
from app.graph.builder import close_banking_graph, get_banking_graph


settings = get_settings()

configure_logging(
    log_level="DEBUG" if settings.debug else "INFO",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        get_banking_graph()
        yield
    finally:
        close_banking_graph()


app = FastAPI(
    title=settings.app_name,
    description=(
        "API de atendimento bancário inteligente operada "
        "por agentes de IA especializados."
    ),
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    chat_router,
    prefix="/api/v1",
)
