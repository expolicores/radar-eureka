"""Configuración explícita para pruebas que pueden destruir tablas; nunca usa la URL habitual."""

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from .config import AppEnvironment, Settings


def settings_for_test_database(settings: Settings) -> Settings:
    if settings.app_env is AppEnvironment.PRODUCTION:
        raise ValueError("Las pruebas destructivas no están permitidas en production.")
    if not settings.test_database_url:
        raise ValueError("Se requiere TEST_DATABASE_URL; DATABASE_URL no es una alternativa.")
    try:
        test_url = make_url(settings.test_database_url)
        development_url = make_url(settings.database_url)
    except ArgumentError as exc:
        raise ValueError("La configuración de bases de datos no es válida.") from exc
    if test_url.get_backend_name() != "postgresql":
        raise ValueError("La base de pruebas debe ser PostgreSQL.")
    if not test_url.database or not test_url.database.endswith("_test"):
        raise ValueError("El nombre de la base de pruebas debe terminar en _test.")
    # Comparar nombres incluso con hosts/usuarios distintos evita alias locales del mismo servidor.
    if test_url.database == development_url.database:
        raise ValueError("Las bases de pruebas y desarrollo deben tener nombres distintos.")
    return settings.model_copy(update={"database_url": settings.test_database_url})
