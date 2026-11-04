"""Read-only projection of a real Socrata research proof, isolated from demo purchases.

Raw extractions remain in the existing document/extraction stores. Only bounded
product evidence and acquisition diagnostics are exposed by this local prototype.
"""

import hashlib
import json
import re
from collections import Counter
from dataclasses import asdict, replace
from itertools import combinations
from pathlib import Path
from typing import Any

from public_procurement.comparison.services import DEFAULT_CONFIG
from public_procurement.shared.text import normalize_text

from .domain.television import (
    Television,
    compare_pair,
    positive_decimal,
    purchase_price_usable,
    television_specs,
)
from .research_comparison import compare_observations


def document_stage(name: str) -> str:
    text = normalize_text(name)
    if "estudio de mercado" in text or "analisis del sector" in text:
        return "budget"
    for stage, terms in (
        ("award", ("aceptacion", "adjudic", "evaluacion", "oferta seleccionada")),
        ("contract", ("contrato", "pccntr", "clausulado")),
        ("execution", ("acta de inicio",)),
        ("specifications", ("estudio", "especifica", "anexo tecnico", "ficha tecnica")),
        ("budget", ("cdp", "presupuesto", "disponibilidad", "compromiso presupuestal")),
        ("opening", ("invitacion",)),
        ("offer", ("oferta", "propuesta economica", "cotizac")),
    ):
        if any(term in text for term in terms):
            return stage
    return "other"


def relevant_document(name: str) -> bool:
    return document_stage(name) != "other"


def _safe_url(raw: Any) -> str | None:
    from urllib.parse import urlsplit

    value = raw.get("url") if isinstance(raw, dict) else raw
    if not isinstance(value, str):
        return None
    try:
        url = urlsplit(value)
        if (
            url.scheme == "https"
            and url.hostname == "community.secop.gov.co"
            and not url.username
            and not url.password
            and url.port in (None, 443)
        ):
            return value
    except ValueError:
        pass
    return None


def products_from_canonicals(process: dict[str, Any]) -> list[Television]:
    row = process["process"]
    facts = {str(f["id"]): f for f in process.get("facts", [])}
    products = []
    for canonical in process.get("canonicals", {}).get("facts", []):
        if canonical["canonical_type"] != "PURCHASE_ITEM":
            continue
        value = canonical["canonical_value"].get("value", {})
        description = str(value.get("description") or "")
        if not re.match(r"\s*(?:televisor(?:es)?|smart\s*tv|tv)\b", normalize_text(description)):
            continue
        sources = [facts[str(i)] for i in canonical.get("evidence_ids", []) if str(i) in facts]
        evidence = [
            {
                "fact_id": f["id"],
                "document_version_id": f["document_version_id"],
                "canonical_id": canonical["id"],
                "source_locator": f["source_locator"],
                "text": f["evidence_text"][:1200],
            }
            for f in sources
        ]
        quantity = positive_decimal(value.get("quantity"))
        price = positive_decimal(value.get("unit_price_cop"))
        total = positive_decimal(value.get("total_cop"))
        warnings = []
        if any(f.get("rule_name") == "tv_row_price_requires_review" for f in sources):
            warnings.append("derived_row_price_ambiguous_header_requires_review")
        if canonical["status"] == "conflict":
            warnings.append("conflicting_canonical")
            price = None
        if quantity and price and total and abs(quantity * price - total) > 1:
            warnings.append("quantity_price_total_mismatch")
            price = None
        stages = {
            document_stage(s["original_name"])
            for f in sources
            for s in f["source_locator"].get("sources", [])
        }
        # Mixed evidence is kept uncertain, never silently promoted to purchase price.
        stage = next(iter(stages)) if len(stages) == 1 else "mixed"
        if stage not in ("contract", "award"):
            warnings.append("not_a_confirmed_purchase_price")
        if stage == "offer":
            warnings.append("offer_acceptance_not_verified")
        products.append(
            Television(
                process_id=row["id_del_proceso"],
                entity=row.get("entidad") or "",
                description=description,
                **television_specs(description),
                quantity=quantity,
                unit=value.get("unit"),
                unit_price_cop=price,
                total_cop=total,
                price_stage=stage,
                confidence=canonical["confidence"],
                evidence=evidence,
                warnings=warnings,
            )
        )
    return products


def specification_evidence(fragments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Explicit TV specification excerpts; no whole-page/person metadata published."""
    result = []
    seen: set[tuple[str, str]] = set()
    for fragment in fragments:
        for match in re.finditer(r"\btelevisor(?:es)?\b", fragment["text"], re.IGNORECASE):
            excerpt = fragment["text"][match.start() : match.start() + 700]
            excerpt = re.split(
                r"\n\s*\d+\s+(?:congelador|computador|impresora|proyector|consola|"
                r"parlante|kit|aire acondicionado)\b",
                excerpt,
                flags=re.IGNORECASE,
            )[0]
            # Cut at a new legal/person section; don't expose full contract pages.
            excerpt = re.split(
                r"\b(?:CONTRATISTA|CEDULA|CÉDULA|NIT|FIRMA|REPRESENTANTE|SUPERVISOR)\b",
                excerpt,
                flags=re.IGNORECASE,
            )[0]
            specs = television_specs(excerpt)
            if not specs["screen_size_inches"]:
                continue
            identity = (fragment["source_locator"].get("input_sha256", ""), excerpt)
            if identity in seen:
                continue
            seen.add(identity)
            prefix = normalize_text(fragment["text"][max(0, match.start() - 55) : match.start()])
            word_counts = {
                "un": 1,
                "uno": 1,
                "dos": 2,
                "tres": 3,
                "cuatro": 4,
                "cinco": 5,
                "seis": 6,
                "siete": 7,
                "ocho": 8,
                "nueve": 9,
                "diez": 10,
                "catorce": 14,
            }
            quantity = None
            literal_quantity = re.search(
                r"\b(un|uno|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|catorce)\s*(?:\((\d+)\))?\s*$",
                prefix,
            )
            if literal_quantity and (
                not literal_quantity[2]
                or int(literal_quantity[2]) == word_counts[literal_quantity[1]]
            ):
                quantity = word_counts[literal_quantity[1]]
            if quantity is None:
                unit_quantities = re.findall(
                    r"\b(\d{1,3})\s+(?:unidades?|und|un)\b|\b(?:unidades?|und)\s+(\d{1,3})\b",
                    normalize_text(excerpt[:350]),
                )
                values = {int(a or b) for a, b in unit_quantities}
                if len(values) == 1:
                    quantity = next(iter(values))
            result.append(
                {
                    "description": excerpt,
                    "specifications": specs,
                    "document_name": fragment["original_name"],
                    "document_version_id": fragment["document_version_id"],
                    "fragment_id": fragment["id"],
                    "source_locator": fragment["source_locator"],
                    "unit_price_cop": None,
                    "quantity": quantity,
                    "quantity_evidence_prefix": prefix[-55:] if literal_quantity else None,
                    "warning": "specification_evidence_not_a_confirmed_purchase_item",
                    "context_type": "supplier_reference_unverified"
                    if re.search(
                        r"\b(?:factura|experiencia contractual|certificado de experiencia)\b",
                        normalize_text(fragment["text"]),
                    )
                    else "document_excerpt",
                }
            )
    return result


def research_observations(
    item: dict[str, Any], contracts: list[dict[str, Any]], fragments: list[dict[str, Any]]
) -> list[Television]:
    """Stage-specific observations: never merge a budget and an awarded price silently."""
    row = item["process"]
    common = {
        "process_id": row["id_del_proceso"],
        "entity": row.get("entidad") or "",
        "published_at": row.get("fecha_de_publicacion_del"),
        "department": row.get("departamento_entidad"),
        "municipality": row.get("ciudad_entidad"),
        "supplier": contracts[0].get("proveedor_adjudicado") if len(contracts) == 1 else None,
    }
    by_hash: dict[str, list[str]] = {}
    fragment_texts = {str(f["id"]): normalize_text(f["text"]) for f in fragments}
    for f in fragments:
        by_hash.setdefault(f["source_locator"].get("input_sha256", ""), []).append(f["text"])
    seen = set()
    products = []
    tv_head = re.compile(
        r"^(?:(?:suministro|adquisicion|compra)(?: e instalacion)? (?:de )?)?"
        r"(?:televisor(?:es)?|tv|smart\s*tv)\b"
    )
    source_text = normalize_text(
        (row.get("nombre_del_procedimiento") or "")
        + " "
        + (row.get("descripci_n_del_procedimiento") or "")
    )
    service_only = "mantenimiento" in source_text and not any(
        t in source_text for t in ("adquisic", "compra", "suministr")
    )
    for fact in item.get("facts", []):
        value = fact.get("normalized_value")
        if fact["fact_type"] != "purchase_item" or not isinstance(value, dict):
            continue
        description = str(value.get("description") or "")
        if not tv_head.search(normalize_text(description)):
            continue
        sources = fact["source_locator"].get("sources", [])
        if not sources:
            continue
        locator = sources[0]["locator"]
        content_hash = locator.get("input_sha256", "")
        stage = document_stage(sources[0]["original_name"])
        page_text = fragment_texts.get(str(fact.get("content_fragment_id")), "")
        if stage == "offer" and re.search(
            r"\b(?:factura|experiencia contractual|certificado de experiencia)\b", page_text
        ):
            continue
        if stage == "award" and "evaluac" in normalize_text(sources[0]["original_name"]):
            continue
        quantity, price, total = (
            positive_decimal(value.get(k)) for k in ("quantity", "unit_price_cop", "total_cop")
        )
        identity = (
            content_hash,
            normalize_text(description),
            str(quantity),
            str(price),
            str(total),
            stage,
        )
        if identity in seen:
            continue
        seen.add(identity)
        warnings = []
        explicit = fact["rule_name"] in ("item_row", "tv_row_price_explicit")
        if not explicit:
            warnings.append("derived_row_price_ambiguous_header_requires_review")
        if quantity and price and total and abs(quantity * price - total) > 1:
            warnings.append("quantity_price_total_mismatch")
            price = None
        if stage not in ("contract", "award"):
            warnings.append("not_a_confirmed_purchase_price")
        if stage == "offer":
            warnings.append("offer_acceptance_not_verified")
        if stage == "contract" and (len(contracts) != 1 or not contracts[0].get("fecha_de_firma")):
            warnings.append("unsigned_or_unverified_contract")
        if stage == "award" and not any(
            term in normalize_text(sources[0]["original_name"])
            for term in ("aceptacion", "adjudic", "oferta seleccionada")
        ):
            warnings.append("award_price_unverified")
        if service_only:
            warnings.append("service_not_purchase")
        if any(
            t in normalize_text(description)
            for t in ("computador", "impresora", "aire acondicionado", "ventilador")
        ):
            warnings.append("mixed_product_bundle")
        whole_document = normalize_text(" ".join(by_hash.get(content_hash, [])))
        if stage == "contract":
            identifiers = [
                row.get("referencia_del_proceso"),
                *(c.get("id_contrato") for c in contracts),
                *(c.get("referencia_del_contrato") for c in contracts),
            ]
            compact_text = re.sub(r"[^a-z0-9]", "", whole_document)
            refs = [re.sub(r"[^a-z0-9]", "", normalize_text(str(i))) for i in identifiers if i]
            refs = [
                i for i in refs if len(i) >= 6 and re.search(r"[a-z]", i) and re.search(r"\d", i)
            ]
            if not any(i in compact_text for i in refs):
                warnings.append("source_reference_unverified")
        if any(
            t in whole_document
            for t in ("servicios de actividad pedagogica", "talleres practicos dirigidos")
        ):
            warnings.append("document_scope_conflict")
        price_text = normalize_text(fact["evidence_text"])
        vat = (
            "included"
            if re.search(r"\b(?:iva incluido|incluido iva|incluye iva)\b", price_text)
            else (
                "excluded"
                if re.search(r"\b(?:sin iva|antes de iva|no incluye iva)\b", price_text)
                else "undetermined"
            )
        )
        linked = [
            c
            for c in item.get("canonicals", {}).get("facts", [])
            if fact.get("id") in c.get("evidence_ids", [])
        ]
        if any(c["status"] == "conflict" for c in linked):
            warnings.append("cross_document_canonical_conflict_preserved")
        specs = television_specs(description)
        if specs["screen_size_inches"] is None and specs["model"] is None:
            warnings.append("aggregate_item_scope_unresolved")
        products.append(
            Television(
                **common,
                description=description,
                **specs,
                quantity=quantity,
                unit=value.get("unit"),
                unit_price_cop=price,
                total_cop=total,
                price_stage=stage,
                vat_basis=vat,
                confidence=fact["confidence"],
                warnings=warnings,
                price_reliable=bool(
                    explicit
                    and price
                    and quantity
                    and not service_only
                    and not any(
                        w in warnings
                        for w in (
                            "mixed_product_bundle",
                            "document_scope_conflict",
                            "aggregate_item_scope_unresolved",
                        )
                    )
                ),
                price_basis="explicit_row" if explicit else "ambiguous_header",
                observation_id=str(fact.get("id") or fact["fingerprint"]),
                evidence=[
                    {
                        "fact_id": fact.get("id"),
                        "document_version_id": fact["document_version_id"],
                        "source_locator": fact["source_locator"],
                        "text": fact["evidence_text"],
                        "canonical_ids": [c["id"] for c in linked],
                    }
                ],
                other_specifications={
                    "interactive_touchscreen": True
                    if re.search(r"\b(?:tactil|interactiva)\b", normalize_text(description))
                    else None
                },
            )
        )
    for excerpt in specification_evidence(fragments):
        if excerpt.get("context_type") == "supplier_reference_unverified":
            continue
        if document_stage(excerpt["document_name"]) == "award":
            continue
        specs = excerpt["specifications"]
        if any(all(getattr(p, key) == value for key, value in specs.items()) for p in products):
            continue
        doc_hash = excerpt["source_locator"].get("input_sha256", "")
        whole_document = normalize_text(" ".join(by_hash.get(doc_hash, [])))
        warnings = ["specification_only", "not_a_confirmed_purchase_price"]
        if service_only:
            warnings.append("service_not_purchase")
        if any(
            t in whole_document
            for t in ("servicios de actividad pedagogica", "talleres practicos dirigidos")
        ):
            warnings.append("document_scope_conflict")
        products.append(
            Television(
                **common,
                description=excerpt["description"],
                **specs,
                price_stage=document_stage(excerpt["document_name"]),
                quantity=positive_decimal(excerpt.get("quantity")),
                confidence="0.6",
                observation_id=hashlib.sha256(
                    (str(common["process_id"]) + json.dumps(specs, sort_keys=True)).encode()
                ).hexdigest(),
                warnings=warnings,
                evidence=[excerpt],
                other_specifications={
                    "interactive_touchscreen": True
                    if re.search(
                        r"\b(?:tactil|interactiva)\b", normalize_text(excerpt["description"])
                    )
                    else None
                },
            )
        )
    # Same-stage disagreements are preserved and excluded from automatic comparisons.
    for index, product in enumerate(products):
        rivals = [
            p
            for p in products
            if normalize_text(p.description) == normalize_text(product.description)
            and p.price_stage == product.price_stage
            and p.unit_price_cop
            and product.unit_price_cop
            and p.unit_price_cop != product.unit_price_cop
        ]
        if rivals:
            products[index] = replace(
                product,
                price_reliable=False,
                warnings=[*product.warnings, "price_conflict_same_stage"],
            )
    return products


def tv_in_official_scope(row: dict[str, Any], fragments: list[dict[str, Any]]) -> bool:
    metadata = normalize_text(
        (row.get("nombre_del_procedimiento") or "")
        + " "
        + (row.get("descripci_n_del_procedimiento") or "")
    )
    if "mantenimiento" in metadata and not any(
        t in metadata for t in ("compra", "adquisic", "suministr")
    ):
        return False
    docs: dict[str, list[str]] = {}
    for fragment in fragments:
        name = fragment["original_name"]
        if document_stage(name) not in (
            "contract",
            "specifications",
            "opening",
        ) or "experiencia" in normalize_text(name):
            continue
        docs.setdefault(name, []).append(fragment["text"])
    for texts in docs.values():
        content = normalize_text(" ".join(texts))
        if any(
            t in content
            for t in ("servicios de actividad pedagogica", "talleres practicos dirigidos")
        ):
            continue
        if re.search(r"\btelevisor(?:es)?\b", content):
            return True
    return False


def build_report(
    sample: dict[str, Any],
    contracts: list[dict[str, Any]],
    fragments_by_process: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    if sample.get("source") != "socrata_secop" or not sample.get("finished_at"):
        raise ValueError("Se requiere una muestra Socrata finalizada, no datos demo o parciales.")
    processes = []
    all_products = []
    research_v2 = sample.get("research_policy") == "research-pair-v2"
    for item in sample["processes"]:
        row = item["process"]
        reference = row["id_del_proceso"]
        matching = [
            c
            for c in contracts
            if row.get("id_del_portafolio")
            and c.get("proceso_de_compra") == row["id_del_portafolio"]
        ]
        extractions = {e["document"]["document_id"]: e for e in item.get("extractions", [])}
        selected = {d["id_documento"] for d in item.get("selected_documents", [])}
        stored = {d["document"]["source"]["id_documento"]: d for d in item.get("documents", [])}
        docs = []
        for doc in item.get("inventory", []):
            saved = stored.get(doc["id_documento"], {})
            version = saved.get("version") or {}
            extraction = extractions.get(saved.get("document", {}).get("id"), {})
            docs.append(
                {
                    "id": doc["id_documento"],
                    "name": doc["original_name"],
                    "stage": document_stage(doc["original_name"]),
                    "source_url": _safe_url(doc["source_url"]),
                    "selected": doc["id_documento"] in selected,
                    "downloaded": bool(version),
                    "sha256": version.get("sha256"),
                    "extraction_status": extraction.get("status", "not_processed"),
                    "error": item.get("download_errors", {}).get(doc["id_documento"])
                    or extraction.get("error_code"),
                    "text_length": extraction.get("text_length", 0),
                    "pages": extraction.get("page_count", 0),
                    "coverage_complete": extraction.get("diagnostics", {}).get("coverage_complete"),
                }
            )
        covered = {d["stage"] for d in docs if d["downloaded"] and d["text_length"] > 0}
        required = {"opening", "specifications", "budget", "award", "contract"}
        products = (
            research_observations(item, matching, fragments_by_process.get(reference, []))
            if research_v2
            else products_from_canonicals(item)
        )
        partial_versions = {
            e["document"]["document_version_id"]
            for e in item.get("extractions", [])
            if e.get("diagnostics", {}).get("coverage_complete") is False
        }
        products = [
            replace(p, price_reliable=False, warnings=[*p.warnings, "partial_document_coverage"])
            if any(e.get("document_version_id") in partial_versions for e in p.evidence)
            else p
            for p in products
        ]
        all_products.extend(products)
        canonical_summaries = []
        for canonical in item.get("canonicals", {}).get("facts", []):
            payload = canonical["canonical_value"]
            canonical_summaries.append(
                {
                    "id": canonical["id"],
                    "type": canonical["canonical_type"],
                    "status": canonical["status"],
                    "confidence": canonical["confidence"],
                    "value": None if canonical["status"] == "conflict" else payload.get("value"),
                    "alternatives": payload.get("candidates", payload.get("field_candidates", {}))
                    if canonical["status"] == "conflict"
                    else None,
                    "fact_ids": canonical.get("evidence_ids", []),
                }
            )
        warnings = ["base_price_is_not_unit_price", "inventory_names_are_not_content_validation"]
        if any(d["selected"] and (not d["downloaded"] or d["error"]) for d in docs):
            warnings.append("incomplete_document_acquisition_or_extraction")
        if any(d["coverage_complete"] is False for d in docs):
            warnings.append("partial_document_coverage")
        if not matching:
            warnings.append("no_contract_in_socrata_at_query_time")
        tv_confirmed = any(
            not any(
                w in p.warnings
                for w in (
                    "service_not_purchase",
                    "document_scope_conflict",
                    "aggregate_item_scope_unresolved",
                )
            )
            for p in products
        )
        if research_v2:
            tv_confirmed = tv_in_official_scope(
                row, fragments_by_process.get(reference, [])
            ) or any(purchase_price_usable(p) for p in products)
        if any(purchase_price_usable(p) for p in products):
            disposition = "requires_comparable_peer"
        elif any("service_not_purchase" in p.warnings for p in products):
            disposition = "service_not_tv_purchase"
        elif any("document_scope_conflict" in p.warnings for p in products):
            disposition = "conflicting_document_scope"
        elif tv_confirmed:
            disposition = "no_reliable_awarded_unit_price"
        elif any(
            d["selected"] and (not d["downloaded"] or d["error"] or d["coverage_complete"] is False)
            for d in docs
        ):
            disposition = "insufficient_document_coverage"
        else:
            disposition = "tv_not_confirmed_in_processed_documents"
        processes.append(
            {
                "id": reference,
                "reference": row.get("referencia_del_proceso"),
                "source": "socrata_secop",
                "dataset": "p6dx-8zbt",
                "portfolio_id": row.get("id_del_portafolio"),
                "entity": row.get("entidad"),
                "department": row.get("departamento_entidad"),
                "municipality": row.get("ciudad_entidad"),
                "published_at": row.get("fecha_de_publicacion_del"),
                "status": row.get("estado_del_procedimiento"),
                "object": row.get("descripci_n_del_procedimiento"),
                "base_price_cop": row.get("precio_base"),
                "source_url": _safe_url(row.get("urlproceso")),
                "contracts": [
                    {
                        k: c.get(k)
                        for k in (
                            "id_contrato",
                            "referencia_del_contrato",
                            "estado_contrato",
                            "proveedor_adjudicado",
                            "fecha_de_firma",
                            "fecha_de_inicio_del_contrato",
                            "fecha_de_fin_del_contrato",
                            "valor_del_contrato",
                            "proceso_de_compra",
                        )
                    }
                    for c in matching
                ],
                "documents": docs,
                "facts_count": len(item.get("facts", [])),
                "canonicals_count": len(item.get("canonicals", {}).get("facts", [])),
                "canonical_summaries": canonical_summaries,
                "conflicts": sum(
                    c["status"] == "conflict" for c in item.get("canonicals", {}).get("facts", [])
                ),
                "products": [asdict(p) for p in products],
                "comparison_disposition": disposition,
                "tv_confirmed": tv_confirmed,
                "tv_confirmation_status": "documented_product"
                if tv_confirmed
                else "not_confirmed_in_processed_evidence",
                "specification_evidence": [
                    e
                    for e in specification_evidence(fragments_by_process.get(reference, []))
                    if not research_v2
                    or (
                        document_stage(e["document_name"]) != "award"
                        and e.get("context_type") != "supplier_reference_unverified"
                    )
                ],
                "lifecycle_covered": sorted(covered),
                "lifecycle_missing": sorted(required - covered),
                "warnings": warnings,
                "errors": item.get("errors", []),
            }
        )
    comparisons = (
        [compare_pair(a, b) for a, b in combinations(all_products, 2)] if not research_v2 else []
    )
    report: dict[str, Any] = {
        "schema_version": "research-proof-v1",
        "source": "socrata_secop",
        "started_at": sample["started_at"],
        "finished_at": sample["finished_at"],
        "window_start": sample["window_start"],
        "window_before": sample["window_before"],
        "comparison_policy": sample.get("comparison_policy", "research-pair-v2"),
        "processes": processes,
        "comparisons": comparisons,
        "signals": [],
        "signal_status": "insufficient_evidence",
        "analysis_config": {
            "id": DEFAULT_CONFIG.id,
            "min_comparables": DEFAULT_CONFIG.min_comparables,
        },
        "signal_reason": (
            "No se publica señal sin precios unitarios documentados, compras comparables, "
            "impuestos y evidencia suficientes. La muestra no reduce el mínimo analítico "
            f"vigente de {DEFAULT_CONFIG.min_comparables} comparables."
        ),
        "limitations": [
            "purposeful_small_sample_not_representative",
            "no_private_market",
            "no_tvec",
            "no_historical_benchmark",
            "no_radar_scoring_or_alerts",
            "socrata_may_lag",
            "local_prototype_report_not_new_analytical_schema",
        ],
    }
    if research_v2:
        pending_cycle = sample.get("comparison_policy") == "research-60d-v1"
        assessment: dict[str, Any] = (
            {
                "comparisons": [],
                "comparable_groups": [],
                "signals": [],
                "comparability_counts": {},
                "comparison_exclusion_reasons": {},
                "comparisons_possible": 0,
            }
            if pending_cycle
            else compare_observations(all_products)
        )
        report.update(assessment)
        selection = sample.get("selection", {})
        report["research_policy"] = "research-pair-v2"
        report["analysis_config"] = {
            "min_purchases_for_pair": 2,
            "same_model_signal_threshold_pct": str(DEFAULT_CONFIG.same_model_threshold_pct),
            "equivalent_signal_threshold_pct": str(DEFAULT_CONFIG.equivalent_threshold_pct),
            "scope": "research_only_not_radar",
        }
        report["signal_status"] = (
            "signals_supported" if assessment["signals"] else "insufficient_evidence"
        )
        report["signal_reason"] = (
            "Las comparaciones por pares requieren dos compras documentadas "
            "de entidades distintas, "
            "cantidades y precios confiables. Una señal requiere además comparabilidad, impuestos "
            "y alcance coherentes; no usa un mínimo de cinco comparables."
        )
        if pending_cycle:
            report["signal_status"] = "awaiting_economic_cycle"
            report["signal_reason"] = (
                "La comparación de 60 días se calcula después de reconstruir el ciclo económico."
            )
            report["analysis_config"] = {"policy": "research-60d-v1", "percentage_threshold": None}
        report["summary"] = {
            "processes_found": selection.get("discovered_unique", len(processes)),
            "mature_metadata_candidates": selection.get("mature_metadata"),
            "document_candidates": len(processes),
            "processes_with_documented_tv": sum(p["tv_confirmed"] for p in processes),
            "tv_observations": len(all_products),
            "reliable_unit_prices": sum(p.price_reliable for p in all_products),
            "reliable_purchase_unit_prices": sum(purchase_price_usable(p) for p in all_products),
            "documents_selected": sum(d["selected"] for p in processes for d in p["documents"]),
            "documents_downloaded": sum(d["downloaded"] for p in processes for d in p["documents"]),
            "documents_failed": sum(
                d["selected"] and not d["downloaded"] for p in processes for d in p["documents"]
            ),
            "extraction_failed": sum(
                bool(d["error"]) and d["downloaded"] for p in processes for d in p["documents"]
            ),
            "partial_coverage_documents": sum(
                d["coverage_complete"] is False for p in processes for d in p["documents"]
            ),
            "disposition_counts": dict(Counter(p["comparison_disposition"] for p in processes)),
            "comparisons_possible": assessment["comparisons_possible"],
            "signals_generated": len(assessment["signals"]),
            "processes_without_tv_confirmation": [
                p["id"] for p in processes if not p["tv_confirmed"]
            ],
        }
    return report


class ResearchReportStore:
    def __init__(self, directory: Path) -> None:
        self.path = directory / "latest.json"

    def read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {
                "schema_version": "research-proof-v1",
                "source": "socrata_secop",
                "processes": [],
                "comparisons": [],
                "signals": [],
                "signal_status": "not_run",
                "signal_reason": "Aún no hay una muestra real finalizada.",
            }
        data: dict[str, Any] = json.loads(self.path.read_text(encoding="utf-8"))
        if (
            not isinstance(data, dict)
            or data.get("schema_version") != "research-proof-v1"
            or data.get("source") != "socrata_secop"
        ):
            raise ValueError("Informe investigativo inválido; no se sustituye con datos demo.")
        return data

    def write(self, report: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(report, default=str, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(self.path)
