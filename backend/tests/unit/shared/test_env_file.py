"""El .env de Regional se resuelve por ruta absoluta; la precedencia no cambia.

Nunca se leen ni se comparan valores reales del .env local: solo rutas y valores señuelo.
"""

from pathlib import Path

import pytest

from public_procurement.agents.eureka_assistant.schemas import FoundrySettings
from public_procurement.investigation.market_benchmark.foundry_scout import (
    ScoutSettings,
)
from public_procurement.investigation.market_benchmark.mercadolibre_adapter import (
    MercadoLibreSettings,
)
from public_procurement.investigation.market_benchmark.serpapi_http import SerpApiSettings
from public_procurement.licitaciones_cdp.configuration import resolve_profile_id
from public_procurement.shared.config import ENV_FILE, Settings

BACKEND = Path(__file__).resolve().parents[3]
DECOY_PROFILE = "999999999"
DECOY_REGIONS = "REGION_SENUELO_XYZ"


def test_env_file_is_the_absolute_regional_backend_env():
    assert ENV_FILE.is_absolute()
    assert ENV_FILE == BACKEND / ".env"


@pytest.mark.parametrize(
    "settings_class",
    [Settings, FoundrySettings, ScoutSettings, MercadoLibreSettings, SerpApiSettings],
)
def test_every_settings_class_uses_the_same_absolute_env_file(settings_class):
    assert settings_class.model_config["env_file"] == ENV_FILE


def test_no_settings_class_reads_a_working_directory_relative_env():
    offenders = [
        str(path.relative_to(BACKEND))
        for path in (BACKEND / "src").rglob("*.py")
        if 'env_file=".env"' in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_a_decoy_env_in_another_working_directory_is_never_read(tmp_path, monkeypatch):
    # Arrange: un .env ajeno (p. ej. de otro proyecto) en el directorio de trabajo.
    (tmp_path / ".env").write_text(
        f"LICITACIONES_PROFILE_ID={DECOY_PROFILE}\nEUREKA_RADAR_REGIONS={DECOY_REGIONS}\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LICITACIONES_PROFILE_ID", raising=False)
    monkeypatch.delenv("EUREKA_RADAR_REGIONS", raising=False)
    # Act
    settings = Settings(database_url="postgresql://unused")
    # Assert
    assert settings.licitaciones_profile_id != DECOY_PROFILE
    assert settings.eureka_radar_regions != DECOY_REGIONS


def test_precedence_is_unchanged_argument_then_environment_then_env_file(monkeypatch):
    monkeypatch.setenv("EUREKA_RADAR_REGIONS", "Desde entorno")
    assert Settings(database_url="postgresql://unused").eureka_radar_regions == "Desde entorno"
    assert (
        Settings(
            database_url="postgresql://unused", eureka_radar_regions="Argumento"
        ).eureka_radar_regions
        == "Argumento"
    )


def test_profile_cli_override_still_wins_over_configuration(monkeypatch):
    monkeypatch.setenv("LICITACIONES_PROFILE_ID", "730001")
    assert resolve_profile_id("730002") == "730002"
    assert resolve_profile_id() == "730001"
