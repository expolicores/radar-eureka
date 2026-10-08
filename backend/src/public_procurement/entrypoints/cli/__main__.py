"""CLI de administración.

Uso: `uv run python -m public_procurement.entrypoints.cli load-seed`
"""

import typer

from public_procurement.comparison.services import RunSummary, build_comparison_service
from public_procurement.ingestion.adapters.seed import SeedPublicDataSource
from public_procurement.ingestion.domain.purchase import Source
from public_procurement.ingestion.services import build_ingestion_service
from public_procurement.market.adapters.seed import SeedRetailObservationSource
from public_procurement.market.services import build_market_ingestion_service
from public_procurement.shared.config import load_settings
from public_procurement.shared.database import create_db_engine
from public_procurement.shared.logging import configure_logging
from public_procurement.shared.persistence import create_session_factory

app = typer.Typer(help="Administración de Seguimiento Compras Públicas.", no_args_is_help=True)


@app.callback()
def main() -> None:
    """Comandos de administración."""


def _print_run(summary: RunSummary) -> None:
    typer.echo(
        f"Recálculo {summary.config_version_id}: {summary.evaluated_count} ítems evaluados · "
        f"{summary.signal_count} señales que merecen revisión"
    )


@app.command("load-seed")
def load_seed() -> None:
    """Carga los datos FICTICIOS de la demo (compras y mercado) y recalcula las señales."""
    settings = load_settings()
    configure_logging(settings.log_level)
    engine = create_db_engine(settings)
    try:
        session_factory = create_session_factory(engine)
        ingestion = build_ingestion_service(session_factory)
        for source in (Source.SECOP_II, Source.TVEC):
            result = ingestion.run(SeedPublicDataSource(source))
            typer.echo(
                f"{source.value}: {result.read_count} leídas · {result.new_count} nuevas · "
                f"{result.updated_count} actualizadas"
            )
        new_observations = build_market_ingestion_service(session_factory).load(
            SeedRetailObservationSource()
        )
        typer.echo(f"Mercado (simulado): {new_observations} observaciones nuevas")
        _print_run(build_comparison_service(session_factory).recalculate())
    finally:
        engine.dispose()


@app.command("recalculate-signals")
def recalculate_signals() -> None:
    """Recalcula benchmarks y señales con la configuración analítica vigente (nueva versión)."""
    settings = load_settings()
    configure_logging(settings.log_level)
    engine = create_db_engine(settings)
    try:
        _print_run(build_comparison_service(create_session_factory(engine)).recalculate())
    finally:
        engine.dispose()


if __name__ == "__main__":
    app()
