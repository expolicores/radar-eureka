"""CLI de administración.

Uso: `uv run python -m public_procurement.entrypoints.cli load-seed`
"""

import json
import logging
import sys
import uuid
from collections.abc import Iterable
from datetime import UTC, date, datetime, timedelta, timezone
from typing import Annotated

import typer

from public_procurement.comparison.services import RunSummary, build_comparison_service
from public_procurement.documents.services import build_document_service
from public_procurement.eureka.services import DEFAULT_CONFIG as EUREKA_CONFIG
from public_procurement.eureka.services import (
    build_eureka_details_service,
    build_eureka_service,
    build_radar_service,
)
from public_procurement.extraction.services import (
    CanonicalSummary,
    ExtractionResult,
    StructuredFact,
    build_consolidation_service,
    build_extraction_service,
    build_structured_service,
    extraction_metrics,
)
from public_procurement.ingestion.adapters.seed import SeedPublicDataSource
from public_procurement.ingestion.adapters.socrata_processes import SocrataProcessSource
from public_procurement.ingestion.domain.purchase import Source
from public_procurement.ingestion.services import (
    ProcessQuery,
    SecopProcess,
    build_ingestion_service,
    build_process_ingestion_service,
    build_process_query_service,
)
from public_procurement.market.adapters.seed import SeedRetailObservationSource
from public_procurement.market.services import build_market_ingestion_service
from public_procurement.notifications.services import (
    DispatcherBusyError,
    NotificationSchemaPendingError,
    build_notification_dispatcher,
    digest_window,
    ensure_schema,
)
from public_procurement.shared.config import load_settings
from public_procurement.shared.database import create_db_engine
from public_procurement.shared.logging import configure_logging
from public_procurement.shared.persistence import create_session_factory
from public_procurement.shared.text import normalize_text

app = typer.Typer(help="Administración de Seguimiento Compras Públicas.", no_args_is_help=True)


@app.command("run-eureka-cycle")
def run_eureka_cycle(
    dry_run: Annotated[
        bool, typer.Option(help="PREFLIGHT/configuration dry-run; NO consulta SECOP")
    ] = False,
    trigger: Annotated[str, typer.Option(help="manual o scheduled")] = "manual",
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Una sola coordinación Radar → notifications → métricas/logs."""
    from public_procurement.operations.services import build_cycle_service

    if trigger not in ("manual", "scheduled"):
        raise typer.BadParameter("trigger debe ser manual o scheduled")
    settings = load_settings()
    engine = create_db_engine(settings)
    try:
        result = build_cycle_service(create_session_factory(engine), settings).run(
            dry_run=dry_run, trigger=trigger
        )
        # ASCII JSON is stable across Windows PowerShell/native pipe encodings.
        typer.echo(json.dumps(result, ensure_ascii=True, default=str, indent=2))
        if result.get("status") == "failed":
            raise typer.Exit(1)
    except Exception as error:
        # Operational exceptions must not dump connection strings or provider bodies.
        if not dry_run:
            from public_procurement.operations.services import record_startup_failure

            record_startup_failure(settings, type(error).__name__, trigger)
        typer.echo(
            json.dumps(
                {
                    "status": "failed",
                    "error": type(error).__name__,
                    "message": "Revisar configuración, migración 0016 y conectividad local.",
                }
            ),
            err=True,
        )
        raise typer.Exit(1) from None
    finally:
        engine.dispose()


@app.callback()
def main() -> None:
    """Comandos de administración."""


@app.command("send-eureka-notifications")
def send_eureka_notifications(
    alert_id: Annotated[str | None, typer.Option(help="UUID de una alerta persistida")] = None,
    pending: Annotated[
        bool, typer.Option(help="Preparar pendientes; opción predeterminada")
    ] = False,
    digest: Annotated[str | None, typer.Option(help="daily, since-last o window")] = None,
    digest_date: Annotated[
        str | None, typer.Option("--date", help="Día local YYYY-MM-DD para daily")
    ] = None,
    from_date: Annotated[
        str | None, typer.Option(help="Inicio inclusivo local del digest window")
    ] = None,
    before_date: Annotated[
        str | None, typer.Option(help="Fin exclusivo local del digest window")
    ] = None,
    recipient: Annotated[list[str] | None, typer.Option(help="Destinatario; repetible")] = None,
    mode: Annotated[
        str | None, typer.Option(help="Override por ejecución: disabled/file/resend")
    ] = None,
    retry: Annotated[bool, typer.Option(help="Reintentar retryable cuando corresponde")] = False,
    dry_run: Annotated[
        bool, typer.Option(help="Vista exacta sin envíos, archivos ni escrituras")
    ] = False,
    allow_real_send: Annotated[
        bool, typer.Option(help="Autorización explícita de envío real para esta ejecución")
    ] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Resultado y preview JSON")] = False,
) -> None:
    """Notifica alertas existentes; no ejecuta Radar ni activa scheduler."""
    settings = load_settings()
    try:
        if sum((bool(alert_id), bool(pending), bool(digest))) > 1:
            raise ValueError("Usa solo uno de --alert-id, --pending o --digest.")
        if mode is not None:
            if mode not in ("disabled", "file", "resend"):
                raise ValueError("Modo inválido: disabled, file o resend.")
            settings = load_settings(
                eureka_notification_mode=mode, eureka_notification_enabled=mode != "disabled"
            )
        identifier = uuid.UUID(alert_id) if alert_id else None
        window = digest_window(
            digest,
            date.fromisoformat(digest_date) if digest_date else None,
            datetime.now(UTC),
            date.fromisoformat(from_date) if from_date else None,
            date.fromisoformat(before_date) if before_date else None,
        )
        sessions = create_session_factory(create_db_engine(settings))
        service = build_notification_dispatcher(sessions, settings)
        if service.policy.enabled or dry_run:
            with sessions() as session:
                ensure_schema(session)
        configure_logging(settings.log_level)
        if json_output or dry_run:
            for handler in logging.getLogger().handlers:
                if isinstance(handler, logging.StreamHandler):
                    handler.setStream(sys.stderr)
        result = service.run(
            recipient
            or [r.strip() for r in settings.eureka_notification_recipients.split(",") if r.strip()],
            alert_id=identifier,
            window=window,
            digest=digest is not None,
            retry=retry,
            dry_run=dry_run,
            allow_real_send=allow_real_send,
        )
    except DispatcherBusyError as error:
        typer.echo(
            json.dumps({"status": "busy", "message": str(error)}) if json_output else str(error)
        )
        raise typer.Exit(2) from error
    except (ValueError, LookupError, NotificationSchemaPendingError) as error:
        raise typer.BadParameter(str(error)) from error
    if json_output or dry_run:
        typer.echo(json.dumps(result, ensure_ascii=False, default=str, indent=2))
    else:
        typer.echo(
            "Notificaciones "
            + (
                "deshabilitadas"
                if result["disabled"]
                else f"preparadas={result['prepared']} capturadas={result['captured']} "
                f"aceptadas={result['sent']} retryable={result['retryable']} "
                f"fallidas={result['failed']} omitidas={result['skipped']}"
            )
        )
    if result["failed"] or result["retryable"]:
        raise typer.Exit(1)


@app.command("run-eureka-radar")
def run_eureka_radar(
    from_date: Annotated[
        str | None, typer.Option(help="Inicio inclusivo; usa EUREKA_RADAR_START_DATE si se omite")
    ] = None,
    before_date: Annotated[
        str | None, typer.Option(help="Fin exclusivo; por defecto mañana en Colombia")
    ] = None,
    department: Annotated[
        list[str] | None, typer.Option(help="Repetible; reemplaza regiones configuradas")
    ] = None,
    process: Annotated[
        str | None, typer.Option(help="Evalúa un proceso ya persistido; útil para golden case")
    ] = None,
    dry_run: Annotated[
        bool, typer.Option(help="Consulta y evalúa sin escrituras ni descargas")
    ] = False,
    max_processes: Annotated[
        int, typer.Option(min=1, help="Máximo de procesos nuevos/fallidos atendidos")
    ] = 20,
    json_output: Annotated[
        bool, typer.Option("--json", help="Informe completo auditable JSON")
    ] = False,
) -> None:
    """Ejecuta una corrida única de Radar; no activa scheduler ni envía mensajes."""
    settings = load_settings()
    try:
        start = date.fromisoformat(from_date) if from_date else settings.eureka_radar_start_date
        before = (
            date.fromisoformat(before_date)
            if before_date
            else datetime.now(timezone(timedelta(hours=-5))).date() + timedelta(days=1)
        )
        regions = tuple(
            value.strip()
            for value in (department or settings.eureka_radar_regions.split(","))
            if value.strip()
        )
        configured_regions = {
            normalize_text(value.strip()): value.strip()
            for value in settings.eureka_radar_regions.split(",")
        }
        regions = tuple(configured_regions.get(normalize_text(value), value) for value in regions)
        if start is None or start >= before or not regions:
            raise ValueError("Configura fecha inicial, fin posterior y al menos una región.")
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    configure_logging(settings.log_level)
    if json_output:
        for handler in logging.getLogger().handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setStream(sys.stderr)
    engine = create_db_engine(settings)
    try:
        sessions = create_session_factory(engine)
        service = build_radar_service(sessions, settings)
        source: Iterable[SecopProcess]
        if process:
            records = list(build_process_query_service(sessions).iter_processes(reference=process))
            if not records:
                raise ValueError("Proceso persistido no encontrado.")
            source = (record.process for record in records)
        else:
            query = ProcessQuery(
                published_from=start,
                published_before=before,
                departments=regions,
                page_size=service.config.page_size,
                max_pages=service.config.max_pages,
            )
            source = SocrataProcessSource().fetch_processes(query)
        result = service.run(
            source,
            start=start,
            before=before,
            regions=regions,
            dry_run=dry_run,
            max_processes=max_processes,
        )
        if json_output:
            typer.echo(json.dumps(result, default=str, ensure_ascii=False))
        else:
            typer.echo(
                f"Radar {result['id']} · {result['status']} · "
                f"{result['processes_seen']} leídos · {result['candidates']} candidatos · "
                f"{result['enriched']} enriquecidos · {result['alerts_created']} alertas creadas · "
                f"{result['failures']} fallos"
            )
            for item in result["items"]:
                typer.echo(
                    f"{item['secop_id']} · {item['outcome']} · {item.get('reason', item['stage'])}"
                )
        if result["failures"]:
            raise typer.Exit(1)
    except (ValueError, RuntimeError) as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error
    finally:
        engine.dispose()


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


@app.command("sync-processes")
def sync_processes(
    portfolio: Annotated[str | None, typer.Option(help="ID de portafolio CO1.BDOS.…")] = None,
    published_from: Annotated[str | None, typer.Option(help="Inicio inclusivo YYYY-MM-DD")] = None,
    published_before: Annotated[str | None, typer.Option(help="Fin exclusivo YYYY-MM-DD")] = None,
    page_size: Annotated[int, typer.Option(min=1, max=1000)] = 1000,
    max_pages: Annotated[int, typer.Option(min=1, max=1000)] = 100,
    dry_run: Annotated[
        bool, typer.Option(help="Consulta sin conectar ni escribir en la base")
    ] = False,
) -> None:
    """Consulta procesos SECOP II y persiste sus datos; no carga compras ni recalcula señales."""
    try:
        query = ProcessQuery(
            published_from=date.fromisoformat(published_from) if published_from else None,
            published_before=date.fromisoformat(published_before) if published_before else None,
            portfolio_id=portfolio,
            page_size=page_size,
            max_pages=max_pages,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    source = SocrataProcessSource()
    if dry_run:
        try:
            processes = list(source.fetch_processes(query))
        except (ValueError, RuntimeError) as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(1) from exc
        for process in processes:
            typer.echo(
                f"{process.id_del_proceso} · {process.id_del_portafolio or 'Sin portafolio'}"
            )
        typer.echo(f"{len(processes)} registros consultados; sin persistencia.")
        return
    settings = load_settings()
    configure_logging(settings.log_level)
    engine = create_db_engine(settings)
    try:
        result = build_process_ingestion_service(create_session_factory(engine)).run(source, query)
        typer.echo(
            f"{result.read_count} leídos · {result.unique_count} procesos únicos · "
            f"{result.changed_count} insertados o actualizados"
        )
    except (ValueError, RuntimeError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    finally:
        engine.dispose()


@app.command("sync-documents")
def sync_documents(
    process: Annotated[str, typer.Option(help="UUID interno o identificador CO1.REQ.…")],
    dry_run: Annotated[bool, typer.Option(help="Consulta sin registrar ni descargar")] = False,
) -> None:
    """Consulta el inventario dmgg-8hin del portafolio de un proceso persistido."""
    settings = load_settings()
    engine = create_db_engine(settings)
    try:
        service = build_document_service(create_session_factory(engine), settings)
        documents = service.sync(process, dry_run=dry_run)
        for document in documents:
            typer.echo(f"{document.id_documento} · {document.original_name}")
        typer.echo(
            f"{len(documents)} documentos; "
            + ("sin persistencia." if dry_run else "inventario registrado.")
        )
    except (ValueError, RuntimeError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    finally:
        engine.dispose()


@app.command("download-documents")
def download_documents(
    process: Annotated[str, typer.Option(help="UUID interno o identificador CO1.REQ.…")],
) -> None:
    """Descarga o reintenta el inventario registrado; conserva versiones anteriores."""
    settings = load_settings()
    engine = create_db_engine(settings)
    try:
        service = build_document_service(create_session_factory(engine), settings)
        result = service.download(process)
        typer.echo(
            f"{result.available} disponibles · {result.failed} fallidos; intentos registrados."
        )
        if result.failed:
            raise typer.Exit(1)
    except (ValueError, RuntimeError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    finally:
        engine.dispose()


@app.command("evaluate-eureka")
def evaluate_eureka(
    process: Annotated[
        str | None, typer.Option(help="UUID interno o identificador CO1.REQ.…")
    ] = None,
    department: Annotated[
        str | None, typer.Option(help="Departamento de procesos persistidos")
    ] = None,
    dry_run: Annotated[bool, typer.Option(help="Evaluar sin persistir oportunidades")] = False,
) -> None:
    """Descubre y prioriza oportunidades comerciales sobre metadata ya persistida."""
    if bool(process) == bool(department):
        raise typer.BadParameter("Indica exactamente --process o --department.")
    settings = load_settings()
    engine = create_db_engine(settings)
    labels = {category.code: category.label for category in EUREKA_CONFIG.catalog}
    try:
        count = 0
        service = build_eureka_service(create_session_factory(engine))
        for result in service.evaluate(process, department, dry_run=dry_run):
            count += 1
            categories = (
                ", ".join(labels.get(code, code) for code in result.matched_categories)
                or "Sin categoría específica"
            )
            band = {"high": "alta", "medium": "media", "low": "baja"}[result.priority_band.value]
            state = {
                "candidate": "candidata",
                "review": "por revisar",
                "excluded": "excluida",
                "closed": "cerrada o vencida",
                "no_match": "sin coincidencias",
            }[result.state.value]
            typer.echo(f"{result.secop_id} · score {result.score} · prioridad {band} · {state}")
            typer.echo(f"Categorías: {categories}")
            typer.echo("Señales UNSPSC: " + (", ".join(result.matched_unspsc) or "Ninguna"))
            typer.echo(
                "Términos/contexto: "
                + (", ".join(result.matched_terms + result.matched_context) or "Ninguno")
            )
            for reason in result.reasons:
                typer.echo(
                    f"+{reason.points}: {reason.label}"
                    + (" · " + ", ".join(reason.signals) if reason.signals else "")
                )
            for penalty in result.penalties:
                typer.echo(f"-{penalty.points}: {penalty.label}")
            for note in result.review_notes:
                typer.echo(f"Revisión: {note}")
        typer.echo(
            f"{count} procesos evaluados · "
            + ("sin persistencia" if dry_run else "resultados guardados")
        )
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    finally:
        engine.dispose()


def _print_extraction(result: ExtractionResult) -> None:
    statuses = {
        "running": "en ejecución",
        "completed": "completado",
        "partial_text": "texto parcial",
        "requires_ocr": "posible OCR requerido",
        "empty_text": "sin texto",
        "failed": "fallido",
    }
    typer.echo(
        f"{result.document.original_name} · {statuses[result.status.value]} · "
        f"{result.extractor.name}/{result.extractor.version} · {result.fragment_count} fragmentos"
    )
    if result.page_count:
        typer.echo(f"Páginas: {result.page_count}; sin texto: {list(result.pages_without_text)}")
    for key, label in (("paragraphs", "Párrafos"), ("tables", "Tablas"), ("sheets", "Hojas")):
        if key in result.format_counts:
            typer.echo(f"{label}: {result.format_counts[key]}")
    if result.diagnostics:
        import json

        typer.echo("Diagnóstico OCR: " + json.dumps(result.diagnostics, ensure_ascii=False))
        typer.echo(
            "Cobertura documental: "
            + ("completa" if result.diagnostics.get("coverage_complete") else "INCOMPLETA")
        )
    if result.reused:
        typer.echo("Resultado existente reutilizado; sin duplicar extracción.")
    if result.error_code:
        typer.echo(f"Error {result.error_code}: {result.error_message}")


@app.command("extract-documents")
def extract_documents(
    process: Annotated[str, typer.Option(help="UUID interno o identificador SECOP")],
    dry_run: Annotated[bool, typer.Option(help="Extraer sin persistir texto ni runs")] = False,
    no_ocr: Annotated[bool, typer.Option("--no-ocr", help="Solo extracción nativa")] = False,
    retry_ocr: Annotated[
        bool, typer.Option("--retry-ocr", help="Nuevo intento OCR incompleto")
    ] = False,
) -> None:
    """Extrae las versiones descargadas de un proceso; no descarga archivos."""
    settings = load_settings()
    engine = create_db_engine(settings)
    try:
        service = build_extraction_service(create_session_factory(engine), settings)
        failed = 0
        results = []
        options = {
            key: True for key, enabled in (("no_ocr", no_ocr), ("retry_ocr", retry_ocr)) if enabled
        }
        for result in service.extract_process(process, dry_run=dry_run, **options):
            results.append(result)
            _print_extraction(result)
            failed += int(
                result.status.value == "failed"
                or result.diagnostics.get("coverage_complete") is False
            )
        import json

        typer.echo("Métricas de extracción: " + json.dumps(extraction_metrics(results)))
        if failed:
            raise typer.Exit(1)
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error
    finally:
        engine.dispose()


@app.command("extract-document")
def extract_document(
    document: Annotated[str, typer.Option(help="UUID o id_documento registrado")],
    dry_run: Annotated[bool, typer.Option(help="Extraer sin persistir")] = False,
    no_ocr: Annotated[bool, typer.Option("--no-ocr", help="Solo extracción nativa")] = False,
    force_ocr: Annotated[
        bool, typer.Option("--force-ocr", help="Forzar OCR diagnóstico; requiere --dry-run")
    ] = False,
    retry_ocr: Annotated[
        bool, typer.Option("--retry-ocr", help="Nuevo intento OCR incompleto")
    ] = False,
) -> None:
    """Extrae un documento registrado por identificador, nunca por una ruta arbitraria."""
    settings = load_settings()
    engine = create_db_engine(settings)
    try:
        options = {
            key: True
            for key, enabled in (
                ("no_ocr", no_ocr),
                ("force_ocr", force_ocr),
                ("retry_ocr", retry_ocr),
            )
            if enabled
        }
        result = build_extraction_service(
            create_session_factory(engine), settings
        ).extract_document(document, dry_run, **options)
        _print_extraction(result)
        if result.status.value == "failed" or result.diagnostics.get("coverage_complete") is False:
            raise typer.Exit(1)
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error
    finally:
        engine.dispose()


@app.command("search-extracted-text")
def search_extracted_text(
    process: Annotated[str, typer.Option(help="UUID o identificador SECOP")],
    term: Annotated[str, typer.Option(help="Texto literal de búsqueda")],
    limit: Annotated[int, typer.Option(min=1, max=100)] = 50,
) -> None:
    """Busca evidencia textual persistida, sin IA ni interpretación."""
    import json

    settings = load_settings()
    engine = create_db_engine(settings)
    try:
        hits = build_extraction_service(create_session_factory(engine), settings).search(
            process, term, limit
        )
        for hit in hits:
            typer.echo(
                f"{hit.original_name} · versión {hit.document_version_id} · "
                f"SHA-256 {hit.input_sha256}"
            )
            typer.echo(json.dumps(hit.source_locator, ensure_ascii=False))
            typer.echo(hit.text)
            for neighbor in hit.context:
                if neighbor["text"] != hit.text:
                    typer.echo(
                        "Contexto "
                        + json.dumps(neighbor["source_locator"], ensure_ascii=False)
                        + ": "
                        + neighbor["text"]
                    )
        typer.echo(f"{len(hits)} coincidencias (máximo {limit}).")
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error
    finally:
        engine.dispose()


def _print_structured(fact: StructuredFact) -> None:
    import json

    value = (
        fact.normalized_value
        if fact.normalized_value is not None
        else (fact.string_value if fact.string_value is not None else str(fact.numeric_value))
    )
    typer.echo(f"{fact.fact_type.upper()}: {value} {fact.unit or ''} · confianza {fact.confidence}")
    typer.echo(f"Regla: {fact.rule_name}/{fact.rule_version}")
    typer.echo(json.dumps(fact.source_locator, ensure_ascii=False))
    typer.echo(f"Evidencia: {fact.evidence_text}")


@app.command("extract-structured")
def extract_structured(
    process: Annotated[str, typer.Option(help="UUID interno o identificador SECOP")],
    dry_run: Annotated[bool, typer.Option(help="Evaluar reglas sin persistir hechos")] = False,
) -> None:
    """Estructura fragmentos ya persistidos; no descarga ni vuelve a leer archivos."""
    settings = load_settings()
    engine = create_db_engine(settings)
    try:
        facts, inserted = build_structured_service(
            create_session_factory(engine), settings
        ).extract(
            process,
            dry_run=dry_run,
        )
        for fact in facts:
            _print_structured(fact)
        typer.echo(f"{len(facts)} hechos; {inserted} nuevos persistidos; dry-run={dry_run}.")
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error
    finally:
        engine.dispose()


@app.command("show-structured")
def show_structured(
    process: Annotated[str, typer.Option(help="UUID interno o identificador SECOP")],
    history: Annotated[bool, typer.Option(help="Incluir versiones y reglas históricas")] = False,
) -> None:
    """Consulta hechos persistidos con toda su evidencia, sin ejecutar reglas."""
    settings = load_settings()
    engine = create_db_engine(settings)
    try:
        facts = build_structured_service(create_session_factory(engine), settings).list_facts(
            process,
            include_history=history,
        )
        for fact in facts:
            _print_structured(fact)
        typer.echo(f"{len(facts)} hechos persistidos.")
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error
    finally:
        engine.dispose()


def _print_canonical(summary: CanonicalSummary) -> None:
    import json

    for fact in summary.facts:
        value = fact.canonical_value
        typer.echo(f"{fact.canonical_type} · {fact.status} · confianza {fact.confidence}")
        typer.echo(json.dumps(value["value"], ensure_ascii=False))
        typer.echo(f"Corroborado: {value['corroborated']}; evidencias: {len(fact.evidence_ids)}")
        if value["review_required"]:
            typer.echo(
                "Requiere revisión; candidatos: "
                + json.dumps(
                    value.get("candidates", value.get("field_candidates")),
                    ensure_ascii=False,
                )
            )
    typer.echo(
        f"{summary.input_count} hechos de entrada → {len(summary.facts)} canónicos; "
        f"{len(summary.conflicts)} conflictos; {summary.inserted} nuevos."
    )
    typer.echo("Campos ausentes: " + ", ".join(summary.missing_fields))


@app.command("consolidate-facts")
def consolidate_facts(
    process: Annotated[str, typer.Option(help="UUID interno o identificador SECOP")],
    dry_run: Annotated[bool, typer.Option(help="Consolidar sin persistir")] = False,
) -> None:
    """Consolida hechos persistidos y conserva todos sus vínculos de evidencia."""
    settings = load_settings()
    engine = create_db_engine(settings)
    try:
        summary = build_consolidation_service(create_session_factory(engine), settings).run(
            process,
            dry_run=dry_run,
        )
        _print_canonical(summary)
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error
    finally:
        engine.dispose()


@app.command("show-canonical")
def show_canonical(
    process: Annotated[str, typer.Option(help="UUID interno o identificador SECOP")],
    with_evidence: Annotated[
        bool, typer.Option(help="Mostrar hechos originales y localizadores")
    ] = False,
) -> None:
    """Consulta únicamente la consolidación correspondiente a los hechos vigentes."""
    import json

    settings = load_settings()
    engine = create_db_engine(settings)
    try:
        service = build_consolidation_service(create_session_factory(engine), settings)
        summary = service.show(process)
        if not summary.persisted:
            typer.echo("No hay consolidación vigente persistida; ejecute consolidate-facts.")
            return
        _print_canonical(summary)
        if with_evidence:
            for canonical in summary.facts:
                typer.echo(f"Evidencias de {canonical.canonical_type} {canonical.id}")
                for fact in service.evidence(process, canonical.id):
                    typer.echo(f"Hecho {fact.id}: {fact.evidence_text}")
                    typer.echo(json.dumps(fact.source_locator, ensure_ascii=False))
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error
    finally:
        engine.dispose()


@app.command("show-eureka-details")
def show_eureka_details(
    process: Annotated[str, typer.Option(help="UUID interno o identificador SECOP")],
    json_output: Annotated[
        bool, typer.Option("--json", help="Serializar el read model completo")
    ] = False,
    with_evidence: Annotated[
        bool, typer.Option(help="Incluir texto original y localizadores")
    ] = False,
) -> None:
    """Consulta Eureka enriquecido sin evaluar score ni ejecutar extracción."""
    import json
    import uuid
    from dataclasses import asdict

    settings = load_settings()
    engine = create_db_engine(settings)
    try:
        service = build_eureka_details_service(create_session_factory(engine), settings)
        details = service.get(process)
        payload = asdict(details)
        if with_evidence:
            identifiers = {
                ref["canonical_fact_id"] for refs in details.evidence.values() for ref in refs
            }
            payload["evidence_details"] = {
                identifier: service.evidence(process, uuid.UUID(identifier))
                for identifier in sorted(identifiers)
            }
        if json_output:
            typer.echo(json.dumps(payload, ensure_ascii=False, default=str))
            return
        typer.echo(f"EUREKA · {details.secop_id}")
        priority = {"high": "alta", "medium": "media", "low": "baja"}.get(
            details.priority or "", "unknown"
        )
        typer.echo(
            f"Prioridad: {priority}; Score: {details.score}; "
            f"Enrichment: {details.enrichment_status}"
        )
        for section in ("commercial", "execution", "payment", "requirements", "commercial_profile"):
            typer.echo(section.upper())
            for field, value in payload[section].items():
                if isinstance(value, list):
                    value = [
                        entry.get("value", entry) if isinstance(entry, dict) else entry
                        for entry in value
                    ]
                elif isinstance(value, dict) and "status" in value:
                    value = value["value"] if value["status"] == "confirmed" else value
                display = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
                typer.echo(f"{field}: " + (display if value is not None else "unknown"))
        typer.echo("QUALITY")
        typer.echo(
            f"Conflictos: {len(details.quality['conflicts'])}; "
            f"Canónicos: {details.quality['canonical_fact_count']}; "
            f"review_required={details.review_required}"
        )
        typer.echo("Missing: " + ", ".join(details.quality["missing_fields"]))
        for note in details.quality["discovery_review_notes"]:
            typer.echo("Revisión discovery: " + note)
        if details.quality["conflicts"]:
            typer.echo(json.dumps(details.quality["conflicts"], ensure_ascii=False))
        typer.echo("Evidence: " + ("available" if details.evidence else "unknown"))
        if with_evidence:
            typer.echo(json.dumps(payload["evidence_details"], ensure_ascii=False, default=str))
    except ValueError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(1) from error
    finally:
        engine.dispose()


if __name__ == "__main__":
    app()
