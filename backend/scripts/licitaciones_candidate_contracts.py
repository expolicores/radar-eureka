"""Versioned candidate-adapter contracts. No persistence or product dependencies."""

import copy
import json
from contextlib import suppress
from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from licitaciones_validity import parse_deadline

CONTRACT_VERSION = "licitaciones-candidate-v1"


@dataclass(frozen=True)
class CandidateProcess:
    external_source: str
    profile_id: str
    codigo_proceso: str
    entity_name: str | None
    object: str
    department: str
    municipality: str | None
    published_at: str | None
    amount: str | None
    id_contrato: str
    id_fuente_contract: str
    id_ultima_fase: str | None
    key_config: str
    raw_source_reference: dict[str, Any]
    deadline_at: str | None = None
    deadline_timezone: str = "America/Bogota"
    provider_status: str | None = None
    validity_status: str = "unknown"
    validity_warning: str | None = None

    @property
    def reference(self):
        identity = self.id_contrato or f"codigo:{self.codigo_proceso}"
        return f"{self.external_source}:{self.profile_id}:{identity}"

    @classmethod
    def from_source(cls, row, profile_id):
        department, _, municipality = str(row.get("TextoDepartamento") or "").partition(":")
        amount = None
        try:
            parsed = Decimal(str(row.get("Valor")))
            if parsed.is_finite():
                amount = str(parsed)
        except InvalidOperation:
            pass
        published_at = row.get("FechaPublicacion")
        # Keep malformed/missing source evidence; freshness marks it ineligible.
        with suppress(ValueError, TypeError):
            published_at = datetime.fromisoformat(
                str(published_at).replace("Z", "+00:00")
            ).isoformat()
        deadline, validity_warning = parse_deadline(row.get("FechaVencimiento"))
        return cls(
            external_source="licitaciones_info",
            profile_id=str(profile_id),
            codigo_proceso=str(row.get("CodigoProceso") or ""),
            entity_name=row.get("EntidadContratante"),
            object=str(row.get("Objeto") or ""),
            department=department.strip(),
            municipality=municipality.strip() or None,
            published_at=published_at,
            amount=amount,
            id_contrato=str(row.get("idContrato") or ""),
            id_fuente_contract=str(row.get("id_fuente_contract") or ""),
            id_ultima_fase=str(row["idUltimaFase"])
            if row.get("idUltimaFase") is not None
            else None,
            key_config=str(row.get("key_config") or ""),
            deadline_at=deadline.isoformat() if deadline else None,
            provider_status=row.get("EstadoProceso"),
            validity_warning=validity_warning,
            # Public source identifiers/metadata only, never a browser/session snapshot.
            raw_source_reference={
                key: row.get(key)
                for key in (
                    "idContrato",
                    "CodigoProceso",
                    "Link",
                    "TextoDepartamento",
                    "FechaPublicacion",
                    "FechaVencimiento",
                    "EstadoProceso",
                    "Valor",
                )
            },
        )

    def to_dict(self):
        return {"process_reference": self.reference, **asdict(self)}


@dataclass(frozen=True)
class CandidateDocument:
    process_reference: str
    document_reference: str
    document_name: str
    document_type: str
    extension: str
    secop_document_id: str
    source_url: str
    extraction_mode: str | None = None
    extraction_status: str = "not_selected"
    total_pages: int | None = None
    processed_pages: list[int] = field(default_factory=list)
    coverage_ratio: float | None = None
    text_length: int = 0
    warnings: list[str] = field(default_factory=list)


def document_contract(process, document, normalize, detail=None):
    name = normalize(document.original_name)
    kind = next(
        (
            kind
            for term, kind in (
                ("invitacion", "invitation"),
                ("estudios previos", "prior_studies"),
                ("especificaciones", "specifications"),
                ("anexo tecnico", "technical_annex"),
                ("ficha tecnica", "technical_sheet"),
            )
            if term in name
        ),
        "other",
    )
    detail = detail or {}
    warnings = []
    if detail.get("ocr_truncated"):
        warnings.append("ocr_truncated")
    if detail and not detail.get("coverage_complete"):
        warnings.append("incomplete_coverage")
    if detail.get("error_code"):
        warnings.append(detail["error_code"])
    return asdict(
        CandidateDocument(
            process_reference=process.reference,
            document_reference=f"{process.reference}:document:{document.document_id}",
            document_name=document.original_name,
            document_type=kind,
            extension=document.extension,
            secop_document_id=document.document_id,
            source_url=document.source_url,
            extraction_mode=detail.get("extraction_mode"),
            extraction_status=detail.get("extraction_status", "not_selected"),
            total_pages=detail.get("total_pages"),
            processed_pages=detail.get("processed_pages", []),
            coverage_ratio=detail.get("coverage_ratio"),
            text_length=detail.get("text_length", 0),
            warnings=warnings,
        )
    )


@dataclass(frozen=True)
class CandidateFact:
    process_reference: str
    document_reference: str
    fact_type: str
    value: Any
    unit: str | None
    normalized_value: Any
    confidence: str
    suspicious: bool
    evidence_text: str
    page_reference: Any
    extraction_mode: str | None
    coverage_ratio: float | None
    document_coverage_complete: bool
    usable_as_complete_evidence: bool
    suspicious_reasons: list[str]
    original_confidence: Any
    provenance: dict[str, Any]
    occurrences: int = 1
    provenance_records: list[dict[str, Any]] = field(default_factory=list)


def fact_contract(process, fact, document):
    value = next(
        (
            fact.get(key)
            for key in ("string_value", "numeric_value", "boolean_value")
            if fact.get(key) is not None
        ),
        fact.get("normalized_value"),
    )
    sources = fact.get("source_locator", {}).get("sources", [])
    locator = sources[0].get("locator", {}) if sources else {}
    raw = copy.deepcopy(fact)
    return asdict(
        CandidateFact(
            process_reference=process.reference,
            document_reference=document["document_reference"],
            fact_type=fact["fact_type"],
            value=value,
            unit=fact.get("unit"),
            normalized_value=fact.get("normalized_value"),
            confidence=str(fact.get("confidence") or 0),
            suspicious=bool(fact.get("suspicious")),
            evidence_text=fact.get("evidence_text", ""),
            page_reference=locator.get("page_number", locator or None),
            extraction_mode=document.get("extraction_mode"),
            coverage_ratio=document.get("coverage_ratio"),
            document_coverage_complete=bool(document.get("coverage_complete")),
            usable_as_complete_evidence=bool(fact.get("usable_as_complete_evidence")),
            suspicious_reasons=list(fact.get("suspicious_reasons", [])),
            original_confidence=fact.get("original_confidence"),
            provenance=raw,
            provenance_records=[raw],
        )
    )


def deduplicate_facts(facts):
    """Exact values only, scoped by process/document/type/unit/normalized value.

    Different evidence pages do not make otherwise identical values distinct.
    Keep every original fact (including its full source locator) in provenance_records.
    """
    unique = {}
    for fact in facts:
        key = json.dumps(
            [
                fact.get(k)
                for k in (
                    "process_reference",
                    "document_reference",
                    "fact_type",
                    "value",
                    "unit",
                    "normalized_value",
                )
            ],
            sort_keys=True,
            ensure_ascii=False,
            default=str,
        )
        if key not in unique:
            unique[key] = copy.deepcopy(fact)
            continue
        target = unique[key]
        target["occurrences"] += fact["occurrences"]
        target["provenance_records"].extend(copy.deepcopy(fact["provenance_records"]))
        target["confidence"] = str(min(Decimal(target["confidence"]), Decimal(fact["confidence"])))
        target["suspicious"] = target["suspicious"] or fact["suspicious"]
        target["suspicious_reasons"] = sorted(
            set(target["suspicious_reasons"] + fact["suspicious_reasons"])
        )
        target["usable_as_complete_evidence"] &= fact["usable_as_complete_evidence"]
        target["document_coverage_complete"] &= fact["document_coverage_complete"]
    return list(unique.values())
