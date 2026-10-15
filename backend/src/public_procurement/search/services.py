"""Consultas persistidas exclusivamente. Sin ingestion, OCR ni escritores."""

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from public_procurement.eureka.services import search_vocabulary
from public_procurement.shared.config import Settings
from public_procurement.shared.logging import log_event

from .adapters import PersistedSearchSource
from .domain.query import (
    SearchQuery,
    modality,
    normalize,
    rank,
    searchable_value,
    tsquery,
    variants,
)
from .ports import SearchSource

logger = logging.getLogger(__name__)
SOURCE_RANK = {
    "canonical_match": 4,
    "structured_match": 3,
    "metadata_match": 2,
    "extracted_text_match": 1,
}
TYPE_MAP = {
    "product": "PRODUCT",
    "item_description": "PURCHASE_ITEM",
    "purchase_item": "PURCHASE_ITEM",
    "brand": "BRAND",
    "presentation": "PRESENTATION",
    "quantity": "QUANTITY",
    "unit_price_cop": "UNIT_PRICE_COP",
    "total_cop": "TOTAL_COP",
    "official_budget_cop": "BUDGET_COP",
    "unspsc": "UNSPSC",
    "delivery_location": "DELIVERY_LOCATION",
    "execution_term": "EXECUTION_TERM",
    "payment_term": "PAYMENT_TERM",
    "guarantee": "GUARANTEE_REQUIRED",
    "rup": "RUP_REQUIRED",
    "experience": "EXPERIENCE_REQUIRED",
}


def fact_match(
    key: str, term: str, kind: str, value: Any, aliases: dict[str, list[str]], queries: list[str]
) -> str | None:
    if key == "product" and kind not in ("PRODUCT", "PURCHASE_ITEM"):
        return None
    if key == "brand" and kind not in ("BRAND", "PRODUCT", "PURCHASE_ITEM"):
        return None
    label = value.get("name", value.get("description", "")) if isinstance(value, dict) else value
    mode = modality(str(label), term, aliases)
    if mode:
        return mode
    if key == "brand":
        return None  # A number/unit never becomes a brand.
    return modality(searchable_value(value), term, aliases) or (
        "full_text" if key in queries else None
    )


class SearchService:
    def __init__(
        self, source: SearchSource, vocabulary: dict[str, Any], policy: dict[str, Any]
    ) -> None:
        self.source, self.vocabulary, self.policy = source, vocabulary, policy

    def evaluate(self, data: dict[str, Any], query: SearchQuery) -> dict[str, Any] | None:
        metadata, opportunity = data["metadata"], data["opportunity"]
        canonical = data["canonical"]
        current_kinds = {f["type"] for f in canonical}
        structured = [
            f for f in data["structured"] if TYPE_MAP.get(f["fact_type"]) not in current_kinds
        ]
        aliases: dict[str, list[str]] = self.vocabulary["aliases"]
        categories = self.vocabulary["categories"]
        category = (
            next(
                (
                    key
                    for key, label in categories.items()
                    if normalize(query.category) in (normalize(key), normalize(label))
                ),
                query.category,
            )
            if query.category
            else ""
        )
        if category and (not opportunity or category not in opportunity["categories"]):
            return None
        if query.priority and (not opportunity or query.priority != opportunity["priority"]):
            return None
        if query.entity and not modality(str(metadata.get("entity_name") or ""), query.entity, {}):
            return None
        budgets = [
            f
            for f in canonical
            if f["type"] == "BUDGET_COP"
            and f["status"] == "confirmed"
            and isinstance(f["value"], dict)
            and f["value"].get("value") is not None
        ]
        budget_values = {int(f["value"]["value"]) for f in budgets}
        budget = (
            next(iter(budget_values)) if len(budget_values) == 1 else metadata["base_price_cop"]
        )
        budget_origin = "canonical_match" if len(budget_values) == 1 else "metadata_match"
        if not budgets and "BUDGET_COP" not in current_kinds:
            fallback = {
                int(f["numeric_value"])
                for f in structured
                if f["fact_type"] == "official_budget_cop" and f["numeric_value"] is not None
            }
            if len(fallback) == 1:
                budget = next(iter(fallback))
                budget_origin = "structured_match"
        if query.budget_min is not None and (budget is None or budget < query.budget_min):
            return None
        if query.budget_max is not None and (budget is None or budget > query.budget_max):
            return None
        if query.unspsc:
            codes = [
                str(f["value"].get("code", ""))
                for f in canonical
                if f["type"] == "UNSPSC"
                and f["status"] == "confirmed"
                and isinstance(f["value"], dict)
            ]
            codes.extend(
                str(f["string_value"] or "") for f in structured if f["fact_type"] == "unspsc"
            )
            codes.extend((metadata.get("category_code") or "").removeprefix("V1.").split(","))
            if query.unspsc not in codes:
                return None
        matches: list[dict[str, Any]] = []
        for key in ("q", "product", "brand"):
            term = getattr(query, key)
            if not normalize(term):
                continue
            reasons: list[dict[str, Any]] = []
            for fact in canonical:
                if fact["status"] != "confirmed":
                    continue
                mode = fact_match(
                    key, term, fact["type"], fact["value"], aliases, fact.get("_queries", [])
                )
                if mode:
                    reasons.append(
                        {
                            "type": "canonical_match",
                            "mode": mode,
                            "field": fact["type"],
                            "value": fact["value"],
                            "canonical_fact_id": fact["id"],
                            "rank": rank("canonical_match", mode, fact["type"]),
                        }
                    )
            for fact in structured:
                kind = TYPE_MAP.get(fact["fact_type"], fact["fact_type"])
                value = (
                    fact["normalized_value"]
                    if fact["normalized_value"] is not None
                    else (
                        fact["string_value"]
                        if fact["string_value"] is not None
                        else fact["numeric_value"]
                    )
                )
                mode = fact_match(key, term, kind, value, aliases, fact.get("_queries", []))
                if mode:
                    sources = fact["source_locator"].get("sources", [])
                    reasons.append(
                        {
                            "type": "structured_match",
                            "mode": mode,
                            "field": kind,
                            "value": value,
                            "rank": rank("structured_match", mode, kind),
                            "fragment_id": sources[0].get("content_fragment_id")
                            if sources
                            else None,
                        }
                    )
            fields = (
                ("title", "description")
                if key in ("product", "brand")
                else (
                    "title",
                    "description",
                    "entity_name",
                    "department",
                    "municipality",
                    "reference",
                    "id_del_proceso",
                    "category_code",
                )
            )
            for field in fields:
                value = str(metadata.get(field) or "")
                mode = modality(value, term, aliases) or (
                    "full_text" if key + "." + field in metadata.get("_queries", []) else None
                )
                if mode:
                    reasons.append(
                        {
                            "type": "metadata_match",
                            "mode": mode,
                            "field": field,
                            "value": value,
                            "rank": rank("metadata_match", mode, field),
                        }
                    )
            for fragment in data["text"]:
                mode = modality(fragment["text"], term, aliases) or (
                    "full_text" if key in fragment.get("_queries", []) else None
                )
                if mode:
                    normalized_terms = variants(term, aliases)
                    position = next(
                        (
                            fragment["text"].lower().find(t)
                            for t in normalized_terms
                            if t in fragment["text"].lower()
                        ),
                        0,
                    )
                    start = max(0, position - 80)
                    reasons.append(
                        {
                            "type": "extracted_text_match",
                            "mode": mode,
                            "field": "document",
                            "value": fragment["text"][start : start + self.policy["snippet_chars"]],
                            "fragment_id": fragment["id"],
                            "locator": fragment["locator"],
                            "rank": rank("extracted_text_match", mode, "document"),
                        }
                    )
            if not reasons:
                return None
            matches.extend(reasons)
        modes: dict[str, int] = {
            "exact_normalized": 5,
            "explicit_alias": 4,
            "phrase": 3,
            "full_text": 2,
            "token_prefix": 1,
        }
        matches.sort(
            key=lambda m: (-m["rank"], -SOURCE_RANK[m["type"]], -modes[m["mode"]], str(m["value"]))
        )
        best: dict[str, Any] = (
            matches[0]
            if matches
            else {"type": "metadata_match", "mode": "exact_normalized", "rank": 0}
        )
        products = [
            {"value": f["value"], "origin": "canonical_match"}
            for f in canonical
            if f["type"] in ("PRODUCT", "PURCHASE_ITEM") and f["status"] == "confirmed"
        ]
        if not products:
            products = [
                {"value": f["normalized_value"] or f["string_value"], "origin": "structured_match"}
                for f in structured
                if f["fact_type"] in ("product", "purchase_item")
            ]
        return {
            "process_id": str(metadata["id"]),
            "secop_id": metadata["id_del_proceso"],
            "opportunity_id": opportunity["id"] if opportunity else None,
            "title": metadata["title"],
            "entity": metadata["entity_name"],
            "department": metadata["department"],
            "municipality": metadata["municipality"],
            "published_on": metadata["published_on"],
            "budget_cop": budget,
            "budget_origin": budget_origin,
            "score": opportunity["score"] if opportunity else None,
            "priority": opportunity["priority"] if opportunity else None,
            "categories": opportunity["categories"] if opportunity else [],
            "has_alert": opportunity["has_alert"] if opportunity else False,
            "products": products[:5],
            "match_type": best["type"],
            "match_mode": best["mode"],
            "search_rank": best["rank"],
            "matches": matches[: self.policy["max_reasons"]],
            "detail_url": "/eureka/" + opportunity["id"] if opportunity else None,
            "source_url": metadata["source_url"],
            "_mode_rank": modes[best["mode"]],
            "_source_rank": SOURCE_RANK[best["type"]],
        }

    def search(self, query: SearchQuery) -> dict[str, Any]:
        started = time.perf_counter()
        expressions = {
            key: tsquery(variants(getattr(query, key), self.vocabulary["aliases"]))
            for key in ("q", "product", "brand")
            if normalize(getattr(query, key))
        }
        candidates: set[uuid.UUID] | None = None
        for expression in expressions.values():
            found = self.source.candidates(expression, query)
            candidates = found if candidates is None else candidates & found
            if not candidates:
                break
        eligible = self.source.eligible(query, candidates)
        identifiers = sorted(eligible)
        results = []
        size = self.policy["batch_size"]
        for start in range(0, len(identifiers), size):
            for data in self.source.batch(identifiers[start : start + size], expressions):
                result = self.evaluate(data, query)
                if result is not None:
                    results.append(result)
        priority = {"high": 3, "medium": 2, "low": 1, None: 0}
        results.sort(
            key=lambda r: (
                -r["search_rank"],
                -r["_source_rank"],
                -r["_mode_rank"],
                -priority[r["priority"]],
                -(r["published_on"].toordinal() if r["published_on"] else 0),
                r["process_id"],
            )
        )
        for result in results:
            result.pop("_mode_rank")
            result.pop("_source_rank")
        start = (query.page - 1) * query.page_size
        items = results[start : start + query.page_size]
        counts: dict[str, int] = {}
        for item in items:
            counts[item["match_type"]] = counts.get(item["match_type"], 0) + 1
        elapsed = round((time.perf_counter() - started) * 1000, 3)
        log_event(
            logger,
            "search_completed",
            duration_ms=elapsed,
            total=len(results),
            filters=[
                k for k, v in query.model_dump().items() if v and k not in ("page", "page_size")
            ],
            match_types=counts,
            query_length=len(query.q),
        )
        return {
            "items": items,
            "total": len(results),
            "page": query.page,
            "page_size": query.page_size,
            "duration_ms": elapsed,
            "ranking_version": self.policy["version"],
        }


def build_search_service(session: Session, settings: Settings) -> SearchService:
    policy = json.loads(
        (Path(__file__).resolve().parents[3] / "config" / "search.v1.json").read_text(
            encoding="utf-8"
        )
    )
    return SearchService(PersistedSearchSource(session), search_vocabulary(settings), policy)


class SearchQueries:
    def __init__(self, sessions: sessionmaker[Session], settings: Settings) -> None:
        self.sessions, self.settings = sessions, settings

    def search(self, query: SearchQuery) -> dict[str, Any]:
        with self.sessions() as session:
            # Consistent reads across metadata, versions and snapshot validation.
            session.connection(execution_options={"isolation_level": "REPEATABLE READ"})
            session.execute(text("SET TRANSACTION READ ONLY"))
            if not session.scalar(
                text("SELECT to_regprocedure('public.search_normalize_v1(text)')")
            ):
                raise HTTPException(
                    503, "Búsqueda pendiente de la migración 0014_transversal_search."
                )
            return build_search_service(session, self.settings).search(query)

    def evidence(
        self, process_id: uuid.UUID, canonical_id: uuid.UUID | None, fragment_id: uuid.UUID | None
    ) -> list[dict[str, Any]]:
        with self.sessions() as session:
            session.execute(text("SET TRANSACTION READ ONLY"))
            if not session.scalar(
                text("SELECT to_regprocedure('public.search_normalize_v1(text)')")
            ):
                raise HTTPException(503, "Búsqueda pendiente de la migración 0014.")
            return PersistedSearchSource(session).evidence(process_id, canonical_id, fragment_id)
