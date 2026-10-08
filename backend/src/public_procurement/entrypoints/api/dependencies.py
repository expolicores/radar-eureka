"""Dependencias inyectadas con `Depends`; los tests las sustituyen con `dependency_overrides`."""

import uuid

from fastapi import Request
from sqlalchemy import Engine

# Usuario de demostración del MVP Beta (sin autenticación). Lo reemplaza la sesión de `identity`.
DEMO_USER_ID = uuid.UUID("0d3a8c55-6a1e-4f5b-9c2d-7e4b1a2f9c10")


def get_engine(request: Request) -> Engine:
    engine: Engine = request.app.state.engine
    return engine


def demo_user_provider(request: Request) -> uuid.UUID:
    """Usuario actual mientras no hay sesión: siempre el Analista demo."""
    return DEMO_USER_ID
