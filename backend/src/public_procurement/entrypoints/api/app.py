"""*App factory* del Servicio Web / API.

Arranque local:
    uv run uvicorn public_procurement.entrypoints.api.app:create_app --factory --reload
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from public_procurement.comparison import api as signals_api
from public_procurement.comparison.services import build_signal_query_service
from public_procurement.exploration import api as exploration_api
from public_procurement.exploration.services import build_exploration_service
from public_procurement.investigation import api as cases_api
from public_procurement.investigation.services import build_investigation_service
from public_procurement.shared.config import Settings, load_settings
from public_procurement.shared.database import create_db_engine
from public_procurement.shared.logging import configure_logging, log_event
from public_procurement.shared.persistence import create_session_factory

from . import health
from .dependencies import demo_user_provider
from .errors import register_error_handlers
from .middleware import CorrelationMiddleware

logger = logging.getLogger("public_procurement.entrypoints.api.app")


def create_app(settings: Settings | None = None) -> FastAPI:
    # Falla rápido: si falta una variable obligatoria, el servicio no llega a escuchar solicitudes.
    settings = settings or load_settings()
    configure_logging(settings.log_level)
    engine = create_db_engine(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        log_event(logger, "app_started", app_env=settings.app_env.value)
        yield
        engine.dispose()

    app = FastAPI(title="Seguimiento Compras Públicas", version="0.1.0", lifespan=lifespan)
    app.state.engine = engine
    session_factory = create_session_factory(engine)
    app.state.exploration_service = build_exploration_service(session_factory)
    app.state.signal_service = build_signal_query_service(session_factory)
    app.state.investigation_service = build_investigation_service(session_factory)
    app.state.current_user_provider = demo_user_provider
    # También responde las excepciones no controladas (500), para no perder las cabeceras.
    app.add_middleware(CorrelationMiddleware)
    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(exploration_api.router)
    app.include_router(signals_api.router)
    app.include_router(cases_api.router)
    return app
