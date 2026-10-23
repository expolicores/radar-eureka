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
from public_procurement.eureka import api as eureka_api
from public_procurement.eureka import review_api
from public_procurement.eureka.services import (
    build_eureka_http_queries,
    build_human_review_service,
    build_radar_http_queries,
)
from public_procurement.exploration import api as exploration_api
from public_procurement.exploration.services import build_exploration_service
from public_procurement.investigation import api as cases_api
from public_procurement.investigation.services import build_investigation_service
from public_procurement.licitaciones_cdp import api as cdp_api
from public_procurement.licitaciones_cdp.background import ManualCdpRunner
from public_procurement.licitaciones_cdp.services import LicitacionesQueries
from public_procurement.notifications import api as notifications_api
from public_procurement.notifications.services import NotificationQueries
from public_procurement.operations import api as operations_api
from public_procurement.operations.background import ManualCycleRunner
from public_procurement.operations.services import OperationsQueries
from public_procurement.search import api as search_api
from public_procurement.search.services import SearchQueries
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
        app.state.manual_cycle_runner.close()
        app.state.manual_cdp_runner.close()
        engine.dispose()

    app = FastAPI(title="Seguimiento Compras Públicas", version="0.1.0", lifespan=lifespan)
    app.state.engine = engine
    session_factory = create_session_factory(engine)
    app.state.exploration_service = build_exploration_service(session_factory)
    app.state.signal_service = build_signal_query_service(session_factory)
    app.state.investigation_service = build_investigation_service(session_factory)
    app.state.current_user_provider = demo_user_provider
    app.state.eureka_queries = build_eureka_http_queries(session_factory, settings)
    app.state.radar_queries = build_radar_http_queries(session_factory)
    app.state.human_review_queries = build_human_review_service(session_factory, settings)
    app.state.search_queries = SearchQueries(session_factory, settings)
    app.state.notification_queries = NotificationQueries(session_factory)
    app.state.operations_queries = OperationsQueries(session_factory, settings)
    app.state.manual_cycle_runner = ManualCycleRunner(session_factory, settings)
    app.state.manual_cdp_runner = ManualCdpRunner(session_factory, settings)
    app.state.cdp_queries = LicitacionesQueries(session_factory)
    # También responde las excepciones no controladas (500), para no perder las cabeceras.
    app.add_middleware(CorrelationMiddleware)
    register_error_handlers(app)
    app.include_router(search_api.router)
    app.include_router(notifications_api.router)
    app.include_router(operations_api.router)
    app.include_router(health.router)
    app.include_router(exploration_api.router)
    app.include_router(signals_api.router)
    app.include_router(cases_api.router)
    app.include_router(eureka_api.router)
    app.include_router(eureka_api.radar_router)
    app.include_router(review_api.router)
    app.include_router(cdp_api.router)
    return app
