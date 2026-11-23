"""Commercial profile configuration; independent of browser authentication."""

import re
from pathlib import Path

from public_procurement.shared.config import Settings

BACKEND = Path(__file__).resolve().parents[3]


class ProfileConfigurationError(ValueError):
    """Safe actionable error without echoing configuration values."""


def resolve_profile_id(override: str | None = None, *, settings: Settings | None = None) -> str:
    """Explicit CLI override, then existing env/.env settings; no historical fallback."""
    value: str | None
    if override is not None:
        value = override
    else:
        config = settings or Settings(_env_file=BACKEND / ".env", database_url="disabled://no-db")
        value = config.licitaciones_profile_id
    if value is None or not value.strip():
        raise ProfileConfigurationError(
            "Falta LICITACIONES_PROFILE_ID. Configura el ID del perfil comercial en backend/.env "
            "o usa --profile-id. Inicia sesion manualmente en Edge CDP."
        )
    value = value.strip()
    if not re.fullmatch(r"[1-9][0-9]*", value):
        raise ProfileConfigurationError(
            "LICITACIONES_PROFILE_ID / --profile-id debe ser un ID numerico positivo."
        )
    return value
