"""Evaluación comercial sobre procesos existentes; única puerta de entrada de Eureka."""

import re
import uuid
from collections.abc import Callable, Iterator
from contextlib import suppress
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from public_procurement.extraction.services import build_consolidation_service
from public_procurement.ingestion.services import build_process_query_service
from public_procurement.shared.config import Settings
from public_procurement.shared.text import normalize_text

from .adapters.extraction import ExtractionCanonicalSource
from .adapters.ingestion import IngestionProcessSource
from .config import DEFAULT_CONFIG, DiscoveryConfig
from .domain.details import CanonicalEntry, CanonicalInput, EurekaOpportunityDetails
from .domain.discovery import OpportunityEvaluation, evaluate_process
from .ports import CanonicalFactsSource, OpportunityQueries, ProcessMetadataSource
from .radar_config import RadarConfig, load_radar_config
from .radar_repositories import SqlRadarRepository
from .radar_services import RadarService
from .repositories import SqlOpportunityQueries, SqlOpportunityRepository
from .review_services import HumanReviewService as HumanReviewService

__all__ = [
    "DEFAULT_CONFIG",
    "DiscoveryConfig",
    "EurekaDetailsService",
    "EurekaHttpQueries",
    "EurekaOpportunityDetails",
    "EurekaService",
    "OpportunityEvaluation",
    "RadarConfig",
    "RadarService",
    "build_eureka_details_service",
    "build_eureka_http_queries",
    "build_eureka_service",
    "build_radar_queries",
    "build_radar_service",
    "load_radar_config",
]


class EurekaService:
    def __init__(
        self,
        sessions: sessionmaker[Session],
        source: ProcessMetadataSource,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        canonical: CanonicalFactsSource | None = None,
    ) -> None:
        self.sessions, self.source, self.clock = sessions, source, clock
        self.canonical = canonical

    def canonical_context(self, reference: str) -> CanonicalInput | None:
        return self.canonical.read(reference) if self.canonical is not None else None

    def evaluate(
        self,
        reference: str | None = None,
        department: str | None = None,
        dry_run: bool = False,
        config: DiscoveryConfig = DEFAULT_CONFIG,
    ) -> Iterator[OpportunityEvaluation]:
        if bool(reference) == bool(department):
            raise ValueError("Indica exactamente un proceso o un departamento.")
        found = False
        for facts in self.source.iter_processes(reference, department):
            found = True
            result = evaluate_process(facts, config)
            if not dry_run:
                with self.sessions.begin() as session:
                    SqlOpportunityRepository(session).save(result, self.clock(), asdict(config))
            yield result
        if reference and not found:
            raise ValueError("Proceso persistido no encontrado.")


def build_eureka_service(
    sessions: sessionmaker[Session],
    *,
    canonical: CanonicalFactsSource | None = None,
) -> EurekaService:
    return EurekaService(
        sessions, IngestionProcessSource(build_process_query_service(sessions)), canonical=canonical
    )


class EurekaDetailsService:
    def __init__(
        self,
        source: ProcessMetadataSource,
        opportunities: OpportunityQueries,
        canonical: CanonicalFactsSource,
        config: DiscoveryConfig = DEFAULT_CONFIG,
    ) -> None:
        self.source, self.opportunities, self.canonical, self.config = (
            source,
            opportunities,
            canonical,
            config,
        )

    def get(self, reference: str) -> EurekaOpportunityDetails:
        process = next(iter(self.source.iter_processes(reference, None)), None)
        if process is None:
            raise ValueError("Proceso persistido no encontrado.")
        stored = self.opportunities.get_by_process(process.process_id)
        canonical = self.canonical.read(str(process.process_id))
        # La identidad ya consolidada es la única clave: nunca se vuelve a deduplicar por similitud.
        entries = list({fact.id: fact for fact in canonical.facts}.values())
        by_type: dict[str, list[CanonicalEntry]] = {}
        for fact in entries:
            by_type.setdefault(fact.canonical_type, []).append(fact)
        evidence: dict[str, Any] = {}
        conflicts: list[dict[str, Any]] = []

        def views(kind: str, field: str) -> list[dict[str, Any]]:
            values = []
            for fact in by_type.get(kind, []):
                evidence.setdefault(field, []).append(
                    {
                        "canonical_fact_id": str(fact.id),
                        "structured_fact_ids": [
                            str(identifier) for identifier in fact.evidence_ids
                        ],
                        "confidence": str(fact.confidence),
                        "corroborated": fact.corroborated,
                        "field_sources": fact.field_sources,
                        "field_confidence": fact.field_confidence,
                    }
                )
                values.append(
                    {
                        "canonical_fact_id": str(fact.id),
                        "value": fact.value,
                        "status": fact.status,
                        "confidence": str(fact.confidence),
                    }
                )
            return values

        def single(kind: str, field: str) -> dict[str, Any] | None:
            values = views(kind, field)
            if not values:
                return None
            if len(values) == 1:
                return values[0]
            conflicts.append(
                {
                    "type": kind,
                    "candidates": values,
                    "canonical_fact_ids": [value["canonical_fact_id"] for value in values],
                    "reason": "multiple_canonical_values",
                }
            )
            return {"value": None, "status": "conflict", "candidates": values}

        commercial: dict[str, Any] = {
            "products": views("PRODUCT", "commercial.products"),
            "presentations": views("PRESENTATION", "commercial.presentations"),
            "brands": views("BRAND", "commercial.brands"),
            "purchase_items": views("PURCHASE_ITEM", "commercial.purchase_items"),
            "quantities": views("QUANTITY", "commercial.quantities"),
            "unit_prices_cop": views("UNIT_PRICE_COP", "commercial.unit_prices_cop"),
            "totals_cop": views("TOTAL_COP", "commercial.totals_cop"),
            "budget_cop": single("BUDGET_COP", "commercial.budget_cop"),
            "unspsc": views("UNSPSC", "commercial.unspsc"),
        }
        execution: dict[str, Any] = {
            "execution_term": single("EXECUTION_TERM", "execution.execution_term"),
            "delivery_location": single("DELIVERY_LOCATION", "execution.delivery_location"),
            "delivery_count": single("DELIVERY_COUNT", "execution.delivery_count"),
        }
        payment: dict[str, Any] = {
            "payment_method": single("PAYMENT_METHOD", "payment.payment_method"),
            "payment_percentage": single("PAYMENT_PERCENTAGE", "payment.payment_percentage"),
            "payment_term": single("PAYMENT_TERM", "payment.payment_term"),
        }
        requirements: dict[str, Any] = {
            "guarantee_required": views("GUARANTEE_REQUIRED", "requirements.guarantee_required"),
            "rup_required": single("RUP_REQUIRED", "requirements.rup_required"),
            "experience_required": single(
                "EXPERIENCE_REQUIRED", "requirements.experience_required"
            ),
            "operational_observations": views(
                "OPERATIONAL_OBSERVATION", "requirements.operational_observations"
            ),
        }
        conflicts.extend(
            [
                {
                    "canonical_fact_id": str(fact.id),
                    "type": fact.canonical_type,
                    "candidates": fact.candidates,
                    "structured_fact_ids": [str(identifier) for identifier in fact.evidence_ids],
                }
                for fact in entries
                if fact.status == "conflict"
            ]
        )

        def numeric(field: dict[str, Any] | None) -> int | str | None:
            if not field or field["status"] != "confirmed" or not isinstance(field["value"], dict):
                return None
            return field["value"].get("value")

        def requirement(values: list[dict[str, Any]]) -> str:
            states = {
                str(value["value"].get("state", "unknown"))
                for value in values
                if value["status"] == "confirmed" and isinstance(value["value"], dict)
            }
            if len(states) != 1 or any(value["status"] != "confirmed" for value in values):
                return "unknown"
            return next(iter(states))

        products = [fact for fact in by_type.get("PRODUCT", []) if fact.status == "confirmed"]
        matches = False
        for product in products:
            name = (
                normalize_text(str(product.value.get("name", "")))
                if isinstance(product.value, dict)
                else ""
            )
            for category in self.config.catalog:
                for term in category.product_terms:
                    term = normalize_text(term)
                    if term == "jugos":
                        term = "jugo"
                    if re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", name):
                        matches = True
        product_match = matches if products else None
        if not matches and any(fact.status == "conflict" for fact in by_type.get("PRODUCT", [])):
            product_match = None
        policies = [
            value
            for value in requirements["guarantee_required"]
            if isinstance(value["value"], dict) and value["value"].get("subject") == "policy"
        ]
        profile = {
            "product_match_basis": "literal_current_catalog",
            "catalog_version": self.config.version,
            "product_match": product_match,
            "budget_cop": numeric(commercial["budget_cop"]),
            "execution_days": numeric(execution["execution_term"]),
            "payment_days": numeric(payment["payment_term"]),
            "guarantee_required": requirement(policies),
            "rup_required": requirement(
                [requirements["rup_required"]] if requirements["rup_required"] else []
            ),
            "experience_required": requirement(
                [requirements["experience_required"]] if requirements["experience_required"] else []
            ),
        }
        return EurekaOpportunityDetails(
            process.process_id,
            process.secop_id,
            stored.id if stored else None,
            stored.categories if stored else (),
            stored.score if stored else None,
            stored.priority if stored else None,
            stored.rule_version if stored else None,
            bool(conflicts) or bool(stored and stored.review_required),
            canonical.status,
            commercial,
            execution,
            payment,
            requirements,
            {
                "extraction_coverage": canonical.extraction_coverage,
                "conflicts": conflicts,
                "missing_fields": list(canonical.missing_fields),
                "canonical_fact_count": len(entries),
                "structured_fact_count": canonical.structured_fact_count,
                "opportunity_persisted": stored is not None,
                "discovery_review_notes": list(stored.review_notes) if stored else [],
            },
            profile,
            evidence,
        )

    def evidence(self, reference: str, canonical_id: uuid.UUID) -> list[dict[str, Any]]:
        return self.canonical.evidence(reference, canonical_id)


def build_eureka_details_service(
    sessions: sessionmaker[Session], settings: Settings
) -> EurekaDetailsService:
    return EurekaDetailsService(
        IngestionProcessSource(build_process_query_service(sessions)),
        SqlOpportunityQueries(sessions),
        ExtractionCanonicalSource(build_consolidation_service(sessions, settings)),
    )


class EurekaHttpQueries:
    def __init__(
        self,
        details: EurekaDetailsService,
        metadata: IngestionProcessSource,
        radar: SqlRadarRepository | None = None,
    ) -> None:
        self.details, self.metadata = details, metadata
        self.radar = radar

    def detail(self, identifier: uuid.UUID) -> dict[str, Any]:
        from dataclasses import asdict

        opportunity = self.details.opportunities.get_by_id(identifier)
        if opportunity is None:
            raise LookupError("Oportunidad no encontrada.")
        reference = str(opportunity.process_id)
        enriched = self.details.get(reference)
        return {
            "opportunity": self.summary(opportunity, self.metadata.header(reference), enriched),
            "details": asdict(enriched),
        }

    def summary(
        self,
        opportunity: Any,
        header: dict[str, Any],
        enriched: EurekaOpportunityDetails | None = None,
    ) -> dict[str, Any]:
        enriched = enriched or self.details.get(str(opportunity.process_id))
        alert = self.radar.alert_for_opportunity(opportunity.id) if self.radar else None
        evidence = {}
        if alert:
            evidence = {key: alert[key] for key in ("evidence_level", "document_status")}
        return {
            **header,
            **evidence,
            "opportunity_id": opportunity.id,
            "category": opportunity.categories,
            "score": opportunity.score,
            "priority": opportunity.priority,
            "review_required": enriched.review_required
            or evidence.get("evidence_level") == "metadata_only",
            "enrichment_status": enriched.enrichment_status,
            "product_match": enriched.commercial_profile["product_match"],
            "budget": enriched.commercial_profile["budget_cop"]
            if enriched.commercial["budget_cop"]
            else header["budget"],
        }

    def listing(
        self,
        page: int,
        page_size: int,
        priority: str | None = None,
        department: str | None = None,
        category: str | None = None,
        review_required: bool | None = None,
    ) -> dict[str, Any]:
        candidates = self.details.opportunities.all()
        rows = []
        for opportunity in candidates:
            if priority and opportunity.priority != priority:
                continue
            if category and category not in opportunity.categories:
                continue
            header = self.metadata.header(str(opportunity.process_id))
            if department and normalize_text(str(header["department"] or "")) != normalize_text(
                department
            ):
                continue
            row = self.summary(opportunity, header)
            if review_required is not None and row["review_required"] != review_required:
                continue
            rows.append(row)
        start = (page - 1) * page_size
        return {
            "items": rows[start : start + page_size],
            "total": len(rows),
            "page": page,
            "page_size": page_size,
        }

    def evidence(self, identifier: uuid.UUID, canonical_id: uuid.UUID) -> list[dict[str, Any]]:
        opportunity = self.details.opportunities.get_by_id(identifier)
        if opportunity is None:
            raise LookupError("Oportunidad no encontrada.")
        reference = str(opportunity.process_id)
        details = self.details.get(reference)
        refs = [
            ref
            for values in details.evidence.values()
            for ref in values
            if ref["canonical_fact_id"] == str(canonical_id)
        ]
        if not refs:
            raise LookupError("Evidencia no disponible en esta oportunidad.")
        return [
            {
                **fact,
                "canonical_fact_id": str(canonical_id),
                "confidence": refs[0]["confidence"],
                "corroborated": refs[0]["corroborated"],
            }
            for fact in self.details.evidence(reference, canonical_id)
        ]


def build_eureka_http_queries(
    sessions: sessionmaker[Session], settings: Settings
) -> EurekaHttpQueries:
    return EurekaHttpQueries(
        build_eureka_details_service(sessions, settings),
        IngestionProcessSource(build_process_query_service(sessions)),
        SqlRadarRepository(sessions),
    )


def build_radar_queries(sessions: sessionmaker[Session]) -> SqlRadarRepository:
    return SqlRadarRepository(sessions)


def build_assistant_read_queries(sessions: sessionmaker[Session], settings: Settings) -> Any:
    from public_procurement.documents.services import build_document_service

    from .assistant_queries import AssistantReadQueries

    def canonical(reference: str) -> list[dict[str, Any]]:
        state = build_consolidation_service(sessions, settings).read_state(reference)
        return [asdict(f) for f in state.summary.facts]

    def documents(reference: str) -> list[dict[str, Any]]:
        return [
            {"id": str(d.id), "name": d.source.original_name, "status": str(d.status)}
            for d in build_document_service(sessions, settings).list_documents(reference)
        ]

    return AssistantReadQueries(
        build_human_review_service(sessions, settings),
        build_radar_queries(sessions),
        canonical,
        documents,
    )


def get_eureka_commercial_profile(settings: Settings) -> dict[str, Any]:
    """Live configuration projection; no scoring, discovery or database access."""
    from .review_fit import load_review_fit_config

    catalog = load_radar_config(settings.eureka_radar_config_path)
    return {
        "regions": list(
            dict.fromkeys(r.strip() for r in settings.eureka_radar_regions.split(",") if r.strip())
        ),
        "commercial_categories": [
            {"category": f.category, "label": f.label, "priority_weight": f.priority}
            for f in catalog.families
            if not f.discovery_only
        ],
        "discovery_only_categories": [
            {"category": f.category, "label": f.label} for f in catalog.families if f.discovery_only
        ],
        "preferred_amount_max": settings.eureka_preferred_budget_max,
        "currency": "COP",
        "above_preferred_amount_automatically_excluded": False,
        "above_preferred_amount_requires_review": True,
        "review_inbox_amount_cap": load_review_fit_config().max_amount_cop,
        "review_inbox_cap_scope": "Merecen Revisión; distinto del monto preferido y de alertas",
        "complexity_review_terms": list(catalog.review_terms),
        "manageable_execution_days": catalog.manageable_execution_days,
        "manageable_payment_days": catalog.manageable_payment_days,
        "provenance": {
            "catalog_version": catalog.version,
            "catalog_fingerprint": catalog.fingerprint,
            "catalog_file": settings.eureka_radar_config_path.name,
            "regions_setting": "EUREKA_RADAR_REGIONS",
            "preferred_amount_setting": "EUREKA_PREFERRED_BUDGET_MAX",
        },
    }


def build_source_pipeline(
    sessions: sessionmaker[Session],
    settings: Settings,
    inventory: Any,
    observer: Callable[[str, dict[str, Any]], None] | None = None,
) -> Any:
    """Same commercial pipeline, with an explicit provider inventory port."""
    from public_procurement.documents.services import build_document_service
    from public_procurement.extraction.services import (
        ConsolidationService,
        StructuredExtractionService,
        build_extraction_service,
    )
    from public_procurement.ingestion.services import build_process_ingestion_service

    from .adapters.radar_pipeline import ExistingRadarPipeline

    documents = build_document_service(
        sessions, settings, inventory=inventory, retry_once=True, limit_to_synced=True
    )
    extraction = build_extraction_service(
        sessions, settings, document_service=documents, ocr_page_limit=20
    )
    structured = StructuredExtractionService(sessions, extraction)
    return ExistingRadarPipeline(
        build_process_ingestion_service(sessions),
        build_process_query_service(sessions),
        documents,
        extraction,
        structured,
        ConsolidationService(sessions, structured),
        build_eureka_service(sessions),
        build_eureka_details_service(sessions, settings),
        observer=observer,
    )


def source_review_eligible(item: dict[str, Any]) -> bool:
    from .review_services import review_evidence_sufficient

    return review_evidence_sufficient(item)


def source_review_decision(item: dict[str, Any]) -> dict[str, Any]:
    from .review_policy import admission

    return admission(item)


def evaluate_source_alert(
    record: Any, details: EurekaOpportunityDetails, settings: Settings
) -> Any:
    """Use the exact existing Eureka candidate and alert decisions."""
    from datetime import timedelta

    from .domain.radar import candidate_decision, evaluate_alert
    from .radar_services import radar_process

    config = load_radar_config(settings.eureka_radar_config_path)
    process = radar_process(record)
    start = record.published_on
    if start is None:
        raise ValueError("Publicacion requerida para evaluar comercialmente.")
    candidate = candidate_decision(
        process, start, start + timedelta(days=1), (record.department or "",), config
    )
    return evaluate_alert(process, candidate, details, config, settings.eureka_preferred_budget_max)


def source_pipeline_review(
    pipeline: Any, reference: str, annotate: Callable[..., Any], policy: dict[str, Any]
) -> dict[str, Any]:
    """Review annotations preserve shared persisted facts; never gate commercial scoring."""
    from dataclasses import asdict

    facts = [asdict(f) for f in pipeline.structured.list_facts(reference)]
    details = pipeline.details.get(reference)
    coverage = details.quality.get("extraction_coverage", {})
    incomplete = {
        str(run.document.document_version_id)
        for run in pipeline.extraction.list_extractions(reference)
        if run.diagnostics.get("coverage_complete") is False
    }
    annotated = annotate(facts, incomplete, policy)
    return {
        "facts": annotated,
        "suspicious_fact": any(f["suspicious"] for f in annotated),
        "partial_document_coverage": coverage.get("coverage_complete") is False,
        "missing_documents": details.quality.get("document_status") == "unavailable",
    }


class RadarHttpQueries:
    """Metadata persistida para presentación; conserva intacta la evidencia histórica."""

    def __init__(self, radar: SqlRadarRepository, metadata: IngestionProcessSource) -> None:
        self.radar, self.metadata = radar, metadata

    def _present(self, alert: dict[str, Any]) -> dict[str, Any]:
        reference = alert["snapshot"].get("secop_id")
        header: dict[str, Any] | None = None
        if reference:
            # Una alerta histórica sigue disponible si falta la metadata relacionada.
            with suppress(ValueError):
                header = self.metadata.header(reference)
        return {**alert, "process": header}

    def alerts(self, page: int, page_size: int) -> dict[str, Any]:
        result = self.radar.alerts(page, page_size)
        return {**result, "items": [self._present(alert) for alert in result["items"]]}

    def get_alert(self, identifier: uuid.UUID) -> dict[str, Any]:
        return self._present(self.radar.get_alert(identifier))

    def runs(self, page: int, page_size: int) -> dict[str, Any]:
        return self.radar.runs(page, page_size)

    def get_run(self, identifier: uuid.UUID) -> dict[str, Any]:
        return self.radar.get_run(identifier)


def build_radar_http_queries(sessions: sessionmaker[Session]) -> RadarHttpQueries:
    return RadarHttpQueries(
        build_radar_queries(sessions), IngestionProcessSource(build_process_query_service(sessions))
    )


def build_human_review_service(
    sessions: sessionmaker[Session], settings: Settings
) -> HumanReviewService:
    from public_procurement.extraction.services import (
        StructuredExtractionService,
        build_extraction_service,
    )

    from .review_repositories import ReviewRepository

    def metadata(references: set[str] | None = None) -> dict[str, dict[str, Any]]:
        result = {}
        query = build_process_query_service(sessions)
        records = (
            query.iter_processes()
            if references is None
            else (stored for ref in references for stored in query.iter_processes(reference=ref))
        )
        for stored in records:
            p = stored.process
            result[p.id_del_proceso] = {
                "process_id": str(stored.id),
                "codigo_proceso": p.reference,
                "entity_name": p.entity_name,
                "object": p.title or p.description,
                "department": p.department,
                "municipality": p.municipality,
                "amount": p.base_price_cop,
                "published_at": p.published_on,
                "deadline_at": p.offer_deadline_raw,
                "source_url": p.source_url,
            }
        return result

    def scoped_metadata(observations: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        references = set()
        for obs in observations:
            item = obs["result"]
            m = item.get("metadata") or {}
            # Modern outcomes already contain the display metadata. Only resolve
            # incomplete legacy observations, never scan every ingested process.
            if not all(
                m.get(k) for k in ("object", "entity_name", "department", "published_at")
            ) or not (m.get("raw_source_reference") or {}).get("Link"):
                ref = m.get("source_identity") or m.get("id_ultima_fase") or item.get("secop_id")
                if ref:
                    references.add(str(ref))
        return metadata(references)

    def evidence(row: dict[str, Any]) -> dict[str, Any]:
        reference = row.get("process_id") or row["canonical_identity"].split(":", 1)[1]
        if build_process_query_service(sessions).get_process(reference) is None:
            return {"facts": [], "documents": [], "canonicals": None}
        extraction = build_extraction_service(sessions, settings)
        facts = StructuredExtractionService(sessions, extraction).list_facts(
            reference, include_history=True
        )
        latest = {}
        for run in extraction.list_extractions(reference):
            latest[str(run.document.document_version_id)] = run
        documents = []
        for run in latest.values():
            diag = run.diagnostics
            processed = (
                len(diag.get("processed_pages", []))
                if "processed_pages" in diag
                else run.page_count
            )
            documents.append(
                {
                    "name": run.document.original_name,
                    "document_version_id": str(run.document.document_version_id),
                    "status": run.status,
                    "extraction_mode": "ocr" if diag.get("processed_pages") else "native",
                    "total_pages": run.page_count,
                    "processed_pages": processed,
                    "coverage_ratio": processed / run.page_count if run.page_count else None,
                    "text_length": run.text_length,
                    "warning": run.error_code or diag.get("status"),
                    "coverage_complete": diag.get("coverage_complete"),
                    "omitted_pages": diag.get("omitted_pages"),
                }
            )
        details = asdict(build_eureka_details_service(sessions, settings).get(reference))
        return {"facts": [asdict(f) for f in facts], "documents": documents, "canonicals": details}

    return HumanReviewService(
        ReviewRepository(sessions), metadata, evidence, scoped_metadata=scoped_metadata
    )


def build_radar_service(
    sessions: sessionmaker[Session],
    settings: Settings,
    observer: Callable[[str, dict[str, Any]], None] | None = None,
) -> RadarService:
    from public_procurement.documents.services import build_document_service
    from public_procurement.extraction.services import (
        build_extraction_service,
        build_structured_service,
    )
    from public_procurement.ingestion.services import (
        build_process_ingestion_service,
        diagnose_secop_availability,
    )

    from .adapters.radar_pipeline import ExistingRadarPipeline

    pipeline = ExistingRadarPipeline(
        build_process_ingestion_service(sessions),
        build_process_query_service(sessions),
        build_document_service(sessions, settings),
        build_extraction_service(sessions, settings),
        build_structured_service(sessions, settings),
        build_consolidation_service(sessions, settings),
        build_eureka_service(sessions),
        build_eureka_details_service(sessions, settings),
        observer=observer,
    )
    return RadarService(
        SqlRadarRepository(sessions),
        pipeline,
        load_radar_config(settings.eureka_radar_config_path),
        settings.eureka_preferred_budget_max,
        observer=observer,
        metadata_exclusion_path=settings.eureka_metadata_alert_exclusions_path,
        availability_diagnostic=diagnose_secop_availability,
    )


def search_vocabulary(settings: Settings) -> dict[str, Any]:
    config = load_radar_config(settings.eureka_radar_config_path)
    return {
        "aliases": {
            key: list(values)
            for family in config.families
            for key, values in family.aliases.items()
        },
        "categories": {family.category: family.label for family in config.families},
    }


def notification_alerts(
    sessions: sessionmaker[Session],
    alert_id: uuid.UUID | None,
    window: tuple[datetime, datetime] | None,
) -> Iterator[dict[str, Any]]:
    from .notification_queries import alerts

    return alerts(sessions, alert_id, window)


def search_opportunities(
    session: Session, process_ids: list[uuid.UUID]
) -> dict[uuid.UUID, dict[str, Any]]:
    from sqlalchemy import select

    from .radar_repositories import AlertRecord
    from .repositories import OpportunityRecord

    records = session.scalars(
        select(OpportunityRecord).where(OpportunityRecord.process_id.in_(process_ids))
    ).all()
    alerts = set(
        session.scalars(
            select(AlertRecord.opportunity_id).where(
                AlertRecord.opportunity_id.in_([r.id for r in records])
            )
        )
    )
    return {
        r.process_id: {
            "id": str(r.id),
            "score": r.score,
            "priority": r.priority_band,
            "categories": r.matched_categories,
            "has_alert": r.id in alerts,
        }
        for r in records
    }
