import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.containers import Container
from app.core.exceptions import register_exception_handlers


def configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
            if not settings.DEBUG
            else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.LOG_LEVEL)
        ),
    )


def create_app() -> FastAPI:
    configure_logging()
    logger = structlog.get_logger()

    container = Container()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        logger.info("app.startup", stand=settings.STAND_NAME, debug=settings.DEBUG)
        yield

    app = FastAPI(
        title="AI Market",
        version="0.1.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    app.container = container  # type: ignore[attr-defined]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(v1_router, prefix="/api/v1")

    return app


app = create_app()
