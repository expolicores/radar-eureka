"""Observation and human assessment of existing funnel results, with no acquisition."""

import unicodedata
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from public_procurement.ingestion.services import canonical_process_identity

from .review_fit import load_review_fit_config, review_fit
from .review_identity import review_aliases
from .review_policy import POLICY_VERSION, admission, documentary_reasons, historical_config
from .review_repositories import ReviewRepository

BOGOTA = ZoneInfo("America/Bogota")
REVIEW_MESSAGES = {
    "suspicious_fact": "Requiere revisión por hechos documentales sospechosos.",
    "suspicious_facts": "Requiere revisión por hechos documentales sospechosos.",
    "ocr_truncated": "Extracción parcial; existen indicios para revisión humana.",
    "partial_document_coverage": "Extracción parcial; existen indicios para revisión humana.",
    "partial_coverage": "Información documental incompleta.",
    "missing_documents": "Sin documentos disponibles; evaluación basada en metadata.",
    "metadata_only": "Sin documentos disponibles; evaluación basada en metadata.",
    "unknown_source": "Origen por verificar; metadata suficiente para revisión.",
    "provider_status_deadline_conflict": (
        "El estado del proveedor contradice la fecha límite; prevalece el deadline."
    ),
}


def review_evidence_sufficient(item: dict[str, Any]) -> bool:
    """Useful public metadata plus at least one operational/commercial evidence signal."""
    m = item.get("metadata", {})
    baseline = (
        len(str(m.get("object") or "").strip()) >= 5
        and bool(str(m.get("entity_name") or "").strip())
        and normalized(m.get("department")) in {"boyaca", "casanare"}
        and moment(m.get("published_at")) is not None
    )
    signals = admission(item)["review_candidate"]
    return bool(baseline and signals)


EXCLUDED = {
    "outside_region",
    "outside_local_scope",
    "outside_window",
    "stale",
    "invalid_response",
    "publication_unknown",
    "incomplete_row",
    "missing_canonical_identity",
    "unenriched_row_skipped",
}
STAGES = {
    s: i
    for i, s in enumerate(
        (
            "metadata",
            "preview",
            "ingestion",
            "discovery",
            "pipeline",
            "documents_sync",
            "documents_download",
            "extraction",
            "extraction_partial",
            "structured",
            "consolidation",
            "canonical_reused",
            "alert_evaluation",
            "completed",
        )
    )
}
REASONS = {
    "limit_deferred": "Diferido por límite de procesamiento",
    "validity_closed": "Deadline vencido",
    "stale": "Fuera de la ventana reciente",
    "outside_window": "Fuera de la ventana reciente",
    "outside_region": "Fuera del alcance geográfico",
    "duplicate_canonical": "Alerta duplicada ya existente",
    "no_confirmed_affinity": "No se confirmaron productos del catálogo comercial",
    "pipeline_required": "Pendiente de enriquecimiento documental",
    "attempts_exhausted": "Reintentos operativos agotados",
    "already_seen": "Proceso ya observado; se conserva su resultado previo",
    "strong_exclusion": "Descartado por una exclusión comercial definida",
    "no_metadata_match": "Sin coincidencia comercial en los metadatos",
    "missing_or_invalid_offer_deadline": "Deadline ausente o inválido; requiere verificación",
    "publication_unknown": "Fecha de publicación desconocida",
    "process_error": "Error del proceso; requiere revisión",
    "metadata_exclusion_policy_invalid": (
        "Alerta provisional bloqueada: política de exclusión inválida"
    ),
    "extraction_failed": "Falló la extracción documental",
}


def moment(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=BOGOTA) if parsed.tzinfo is None else parsed
    except (TypeError, ValueError):
        return None


def normalized(value: Any) -> str:
    return "".join(
        c
        for c in unicodedata.normalize("NFD", str(value or "").lower())
        if not unicodedata.combining(c)
    )


def project(
    data: dict[str, Any], processes: dict[str, dict[str, Any]], now: datetime
) -> list[dict[str, Any]]:
    """Exact identities only. Preserve all observations while selecting latest metadata."""
    index: dict[str, dict[str, Any]] = {}
    aliases = review_aliases(data["observations"])
    configs = {}
    for obs in data["observations"]:
        item = obs["result"]
        if not isinstance(item, dict):
            continue
        m = item.get("metadata") or {}
        if not isinstance(m, dict):
            continue
        reference = (
            m.get("source_identity")
            or m.get("id_ultima_fase")
            or m.get("process_reference")
            or item.get("secop_id", "")
        )
        stored = processes.get(str(reference), {})
        if not reference or not (m.get("object") or stored.get("object") or item.get("title")):
            continue
        identity = canonical_process_identity(
            str(reference),
            m.get("raw_source_reference", {}).get("Link") or stored.get("source_url"),
        )
        observed_identity = identity
        identity = aliases.get(identity, identity)
        if obs["source"] == "licitaciones_info_cdp" and not identity.startswith(
            ("secop:", "licitaciones_info:", "secop1:")
        ):
            continue
        row = index.setdefault(
            identity,
            {
                "canonical_identity": identity,
                "sources": [],
                "history": [],
                "stage_max": "metadata",
                "manual_review_reasons": [],
                "requires_manual_document_review": False,
                "decision": None,
                "score": None,
                "opportunity_id": None,
                "equivalent_identities": [identity],
                "review_evidence_sufficient": False,
            },
        )
        for equivalent in [observed_identity] + [
            a for a, target in aliases.items() if target == identity
        ]:
            if equivalent not in row["equivalent_identities"]:
                row["equivalent_identities"].append(equivalent)
        for key, value in {
            "codigo_proceso": m.get("codigo_proceso") or stored.get("codigo_proceso") or reference,
            "entity_name": m.get("entity_name") or stored.get("entity_name"),
            "object": m.get("object") or stored.get("object") or item.get("title"),
            "department": m.get("department") or stored.get("department") or item.get("department"),
            "municipality": m.get("municipality") or stored.get("municipality"),
            "amount": m.get("amount") if m.get("amount") is not None else stored.get("amount"),
            "published_at": m.get("published_at")
            or stored.get("published_at")
            or item.get("published_on"),
            "deadline_at": m.get("deadline_at") or stored.get("deadline_at"),
            "source_url": m.get("raw_source_reference", {}).get("Link") or stored.get("source_url"),
        }.items():
            if value is not None:
                row[key] = value
        row.update(
            last_run_at=obs["run_at"],
            last_run_id=obs["run_id"],
            funnel_state=item.get("reason") or item.get("outcome", "no_alert"),
        )
        row["provider_source"] = m.get("provider_source") or {
            "secop2": "secop2",
            "secop1": "secop1",
            "secopi": "secop1",
            "fao": "fao",
            "cruz_roja": "cruz_roja",
            "universidad": "universidad",
        }.get(str(m.get("key_config") or "").casefold(), "unknown")
        review_item = {**item, "metadata": {**stored, **m}}
        config_key = obs["run_id"]
        if config_key not in configs:
            configs[config_key] = historical_config(obs.get("config_snapshot"))
        review_policy = admission(review_item, configs[config_key])
        row["review_evidence_sufficient"] |= review_policy["review_candidate"]
        row.setdefault("review_admission_reasons", [])
        row["review_admission_reasons"] = list(
            dict.fromkeys(
                row["review_admission_reasons"] + review_policy["review_admission_reasons"]
            )
        )
        stage = item.get("stage", "metadata")
        if STAGES.get(stage, 0) > STAGES.get(row["stage_max"], 0):
            row["stage_max"] = stage
        if obs["source"] not in row["sources"]:
            row["sources"].append(obs["source"])
        decision = item.get("decision")
        if decision:
            row["decision"] = decision
            row["score"] = decision.get("snapshot", {}).get("score")
        process_id = item.get("process_id") or stored.get("process_id")
        if process_id:
            row["process_id"] = str(process_id)
        opportunity = data["opportunities"].get(str(process_id), {})
        if opportunity:
            row["opportunity_id"] = opportunity["id"]
            if row["score"] is None:
                row["score"] = opportunity["score"]
        review = item.get("document_review", {})
        reasons = item.get("manual_review_reasons") or review.get("manual_review_reasons", [])
        reasons = [reason for reason in reasons if reason != "source_metadata_review"]
        reasons.extend(documentary_reasons(item))
        for flag in (
            "suspicious_fact",
            "ocr_truncated",
            "partial_document_coverage",
            "extraction_failed",
            "unsupported_format",
            "missing_documents",
            "document_download_failed",
        ):
            reason = "suspicious_facts" if flag == "suspicious_fact" else flag
            if review.get(flag) and reason not in reasons:
                reasons.append(reason)
        if item.get("coverage_incomplete"):
            reasons.append("partial_document_coverage")
        for warning in item.get("warnings", []):
            code = warning.get("code") if isinstance(warning, dict) else warning
            if code in REVIEW_MESSAGES:
                reasons.append("suspicious_facts" if code == "suspicious_fact" else str(code))
        row["requires_manual_document_review"] |= bool(
            item.get("requires_manual_document_review") or reasons
        )
        row["manual_review_reasons"] = list(dict.fromkeys(row["manual_review_reasons"] + reasons))
        row["review_explanations"] = [
            REVIEW_MESSAGES.get(reason, "Información documental incompleta.")
            for reason in row["manual_review_reasons"]
        ]
        row["history"].append(
            {
                "run_id": obs["run_id"],
                "run_at": obs["run_at"],
                "source": obs["source"],
                "observed_identity": observed_identity,
                "provider_reference": m.get("process_reference"),
                "result": item,
            }
        )
    for row in index.values():
        fit_rejection = review_fit(
            {"metadata": row, "decision": row.get("decision")}, historical_config(None)
        )
        row["review_fit_rejected_reason"] = fit_rejection
        if fit_rejection:
            row["review_evidence_sufficient"] = False
        deadline = moment(row.get("deadline_at"))
        published = moment(row.get("published_at"))
        row["validity_status"] = (
            "unknown" if not deadline else "open" if deadline > now else "closed"
        )
        row["stale"] = bool(published and published < now - timedelta(days=7))
        row["alert_ids"] = [
            a["id"]
            for a in data["alerts"]
            if (a["canonical_identity"] or a["snapshot"].get("canonical_identity"))
            in row["equivalent_identities"]
        ]
        row["has_alert"] = bool(row["alert_ids"])
        decision = row["decision"]
        row["commercial_decision"] = (
            "Sin evaluar"
            if not decision
            else "Elegible"
            if decision.get("create")
            else "No elegible"
        )
        state = row["funnel_state"]
        if state == "missing_or_invalid_offer_deadline" and row["review_evidence_sufficient"]:
            row["review_explanations"].append("Deadline por verificar")
        row["no_alert_reason"] = REASONS.get(state)
        term = (decision or {}).get("snapshot", {}).get("metadata_exclusion_term")
        if term and not (decision or {}).get("create"):
            row["no_alert_reason"] = f"Alerta provisional excluida por objeto: {term}"
            row["metadata_exclusion_term"] = term
        if row["validity_status"] == "closed":
            row["no_alert_reason"] = REASONS["validity_closed"]
        elif not row["no_alert_reason"]:
            row["no_alert_reason"] = (
                REASONS["no_confirmed_affinity"]
                if decision
                and not decision.get("create")
                and not decision.get("snapshot", {}).get("confirmed_matches")
                else "Alerta existente"
                if row["has_alert"]
                else "Requiere revisión documental manual"
                if row["requires_manual_document_review"]
                else "Score calculado, pero sin decisión elegible"
                if row["score"] is not None
                else "Pendiente de revisión humana"
            )
        # Presentation reasons do not change the documentary manual-review flag.
        if not row["review_explanations"]:
            if state == "limit_deferred":
                row["review_explanations"] = [REASONS["limit_deferred"]]
            elif decision is None and row["score"] is None:
                row["review_explanations"] = ["Sin evaluación comercial registrada todavía."]
        ratings = [
            {"canonical_identity": identity, **data["ratings"][identity]}
            for identity in row["equivalent_identities"]
            if identity in data["ratings"]
        ]
        row["manual_assessments"] = [
            rating
            for rating in ratings
            if rating.get("reviewed_at") or rating.get("manual_rating") or rating.get("manual_note")
        ]
        row["review_protected_by_human"] = bool(row["manual_assessments"])
        selected: dict[str, Any] = max(
            row["manual_assessments"] or ratings,
            key=lambda r: moment(r.get("reviewed_at")) or datetime.min.replace(tzinfo=UTC),
            default={},
        )
        row.update(
            {
                "review_first_seen_at": None,
                "review_first_seen_origin": "legacy_unknown",
                "manual_rating": None,
                "manual_note": "",
                "reviewed_at": None,
                "reviewed_by": None,
            }
            | selected
        )
        valid_entries = [r for r in ratings if moment(r.get("review_first_seen_at")) is not None]
        if valid_entries:
            first = min(
                valid_entries,
                key=lambda r: moment(r["review_first_seen_at"]) or datetime.max.replace(tzinfo=UTC),
            )
            row["review_first_seen_at"] = first["review_first_seen_at"]
            row["review_first_seen_origin"] = first.get("review_first_seen_origin", "observed")
        else:
            row["review_first_seen_at"] = None
            row["review_first_seen_origin"] = "legacy_unknown"
        row["canonical_identity"] = row["equivalent_identities"][0]
    return list(index.values())


class HumanReviewService:
    def __init__(
        self,
        repository: ReviewRepository,
        metadata: Any,
        evidence: Any,
        clock: Any = None,
        scoped_metadata: Any = None,
    ) -> None:
        self.repository, self.metadata, self.evidence = repository, metadata, evidence
        self.clock = clock or (lambda: datetime.now(UTC))
        self.scoped_metadata = scoped_metadata

    def rows(self, since: datetime | None = None) -> list[dict[str, Any]]:
        at = self.clock()
        data = self.repository.read(since=since) if since is not None else self.repository.read()
        metadata = (
            self.scoped_metadata(data["observations"])
            if since is not None and self.scoped_metadata is not None
            else self.metadata()
        )
        rows = project(data, metadata, at)
        # Reading an old result is not an observed entry into the review tray.
        # Only record_review_entry records new first-entry events at persistence time.
        return [r for r in rows if any(i in data["ratings"] for i in r["equivalent_identities"])]

    def list(self, filters: dict[str, Any]) -> dict[str, Any]:
        # Alerts own their operational queue. Keep historical review assessments/evidence,
        # but never show the same exact/equivalent identity in both inboxes. Apply before
        # options, optional filters and pagination; include_excluded cannot undo it.
        since = self.clock() - timedelta(days=7)
        rows = [row for row in self.rows(since=since) if not row["has_alert"]]
        options = {
            key: sorted({str(r[key]) for r in rows if r.get(key)})
            for key in ("department", "municipality", "funnel_state")
        }
        accepted = []
        for row in rows:
            if filters.get("identity") and filters["identity"] not in row["equivalent_identities"]:
                continue
            if filters.get("run_id") and not any(
                h["run_id"] == filters["run_id"] for h in row["history"]
            ):
                continue
            validity = filters.get("validity", "active")
            if validity == "active" and row["validity_status"] == "closed":
                continue
            if validity not in {"all", "active"} and row["validity_status"] != validity:
                continue
            if not filters.get("include_excluded") and (
                row["stale"]
                or row.get("review_fit_rejected_reason")
                or row["funnel_state"] in EXCLUDED
                or (
                    not row.get("review_evidence_sufficient", False)
                    and not row.get("review_protected_by_human", False)
                )
            ):
                continue
            if filters.get("source") and filters["source"] not in row["sources"]:
                continue
            if any(
                filters.get(k) and normalized(filters[k]) not in normalized(row.get(k))
                for k in ("department", "municipality", "funnel_state")
            ):
                continue
            if filters.get("q") and normalized(filters["q"]) not in normalized(
                " ".join(str(row.get(k, "")) for k in ("codigo_proceso", "entity_name", "object"))
            ):
                continue
            if any(
                filters.get(k) is not None and row[k] != filters[k]
                for k in ("has_alert", "requires_manual_document_review")
            ):
                continue
            skip = False
            for field, low, high in (
                ("score", "score_min", "score_max"),
                ("amount", "amount_min", "amount_max"),
            ):
                value = row.get(field)
                for bound, lower in ((low, True), (high, False)):
                    if filters.get(bound) is not None and (
                        value is None
                        or (
                            float(value) < float(filters[bound])
                            if lower
                            else float(value) > float(filters[bound])
                        )
                    ):
                        skip = True
            deadline = moment(row.get("deadline_at"))
            for bound, lower in (("deadline_from", True), ("deadline_to", False)):
                if filters.get(bound) and (
                    deadline is None
                    or (
                        deadline.date() < filters[bound]
                        if lower
                        else deadline.date() > filters[bound]
                    )
                ):
                    skip = True
            if not skip:
                accepted.append(row)
        accepted.sort(
            key=lambda r: (
                not any(
                    h["run_id"] == filters.get("run_id")
                    and h["result"].get("review_entry", {}).get("status") == "new"
                    for h in r["history"]
                )
                if filters.get("run_id")
                else False,
                (first_seen := moment(r.get("review_first_seen_at"))) is None,
                -first_seen.timestamp() if first_seen else 0,
            )
        )
        page, size = filters.get("page", 1), filters.get("page_size", 25)
        return {
            "items": [self.present(r) for r in accepted[(page - 1) * size : page * size]],
            "admission_policy": {
                "version": POLICY_VERSION,
                "max_amount_cop": load_review_fit_config().max_amount_cop,
            },
            "total": len(accepted),
            "observed_since": since.isoformat(),
            "page": page,
            "page_size": size,
            "filter_options": options,
        }

    @staticmethod
    def present(row: dict[str, Any]) -> dict[str, Any]:
        return {
            **row,
            "history": [{k: v for k, v in h.items() if k != "result"} for h in row["history"]],
        }

    def get(self, identity: str) -> dict[str, Any]:
        row = next((r for r in self.rows() if identity in r["equivalent_identities"]), None)
        if row is None:
            raise LookupError("Proceso no encontrado en las corridas persistidas")
        return {**row, "evidence": self.evidence(row)}

    def save(self, identity: str, rating: str | None, note: str, user: uuid.UUID) -> dict[str, Any]:
        row = next((r for r in self.rows() if identity in r["equivalent_identities"]), None)
        if row is None:
            raise LookupError("Proceso no encontrado")
        return self.repository.save(row["canonical_identity"], rating, note, user, self.clock())


def default_review_entry(row: dict[str, Any]) -> bool:
    """Same default tray membership; optional UI filters do not create entry events."""
    return (
        row["validity_status"] != "closed"
        and not row["stale"]
        and row["funnel_state"] not in EXCLUDED
        and row.get("review_evidence_sufficient", True)
    )


def record_review_entry(
    session: Any, item: dict[str, Any], source: str, at: datetime
) -> dict[str, Any] | None:
    """Observe persisted outcomes without affecting funnel, scoring, or source requests."""
    from sqlalchemy.dialects.postgresql import insert

    from .review_repositories import ManualProcessReviewRecord

    if (
        source not in {"socrata", "licitaciones_info_cdp"}
        or item.get("review_candidate") is not True
    ):
        return None
    stored = {}
    if source == "socrata" and item.get("process_id"):
        from sqlalchemy.orm import sessionmaker

        from public_procurement.ingestion.services import build_process_query_service

        reference = next(
            build_process_query_service(sessionmaker(bind=session.get_bind())).iter_processes(
                reference=item["process_id"], page_size=1
            ),
            None,
        )
        if reference:
            process = reference.process
            stored[str(item["secop_id"])] = {
                "codigo_proceso": process.reference,
                "object": process.title or process.description,
                "published_at": process.published_on,
                "deadline_at": process.offer_deadline_raw,
                "source_url": process.source_url,
            }
    rows = project(
        {
            "observations": [{"source": source, "run_id": "", "run_at": at, "result": item}],
            "ratings": {},
            "alerts": [],
            "opportunities": {},
        },
        stored,
        at,
    )
    for row in rows:
        if item.get("review_candidate") is True:
            inserted = session.execute(
                insert(ManualProcessReviewRecord)
                .values(
                    canonical_identity=row["canonical_identity"],
                    manual_note="",
                    review_first_seen_at=at,
                    review_first_seen_origin="observed",
                )
                .on_conflict_do_nothing(index_elements=["canonical_identity"])
                .returning(ManualProcessReviewRecord.canonical_identity)
            ).scalar_one_or_none()
            return {
                "canonical_identity": row["canonical_identity"],
                "status": "new" if inserted else "existing",
            }
    return None
