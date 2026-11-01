"""Compact, allowlisted outputs. No raw snapshots, logs or document bodies."""

import json
from collections.abc import Callable
from typing import Any

from .tools import LatestCdpRunTool


def short(value: Any, length: int = 500) -> Any:
    return value[:length] if isinstance(value, str) else value


def fields(value: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
    return {out: short(value.get(key)) for out, key in mapping.items()}


PROCESS = {
    "identity": "canonical_identity",
    "process_code": "codigo_proceso",
    "entity": "entity_name",
    "object": "object",
    "municipality": "municipality",
    "department": "department",
    "amount": "amount",
    "published_at": "published_at",
    "deadline": "deadline_at",
    "validity": "validity_status",
    "source": "sources",
    "score": "score",
    "review_first_seen_at": "review_first_seen_at",
    "commercial_decision": "commercial_decision",
    "no_alert_reason": "no_alert_reason",
    "manual_review_required": "requires_manual_document_review",
    "manual_review_reasons": "manual_review_reasons",
    "has_alert": "has_alert",
}


class EurekaReadTools(LatestCdpRunTool):
    def __init__(
        self, queries: Any, reads: Any, profile: Callable[[], dict[str, Any]] | None = None
    ) -> None:
        super().__init__(queries)
        self.reads = reads
        self.profile = profile

    def get_eureka_commercial_profile(self) -> dict[str, Any]:
        if self.profile is None:
            raise ValueError("El lector de configuración comercial no está configurado.")
        return self.profile()

    def get_run_alerts(self, run_id: str) -> dict[str, Any]:
        try:
            result = self.reads.run_alerts(run_id)
        except LookupError:
            return {"found": False, "run_id": run_id, "items": [], "total": 0}
        alerts = []
        for a in result["items"][:10]:
            s = a.get("snapshot") or {}
            alerts.append(
                {
                    "alert_id": str(a["id"]),
                    "process_identity": s.get("canonical_identity"),
                    "process_code": s.get("codigo_proceso") or s.get("process_code"),
                    "entity": short(s.get("entity")),
                    "object": short(s.get("title")),
                    "location": {
                        "municipality": s.get("municipality"),
                        "department": s.get("department"),
                    },
                    "amount": s.get("budget"),
                    "deadline": s.get("deadline_at"),
                    "score": s.get("score"),
                    "source": a.get("source"),
                    "created_at": a.get("created_at"),
                    "review_required": a.get("review_required"),
                    "reasons": [short(r.get("code"), 80) for r in a.get("reasons", [])][:10],
                }
            )
        return {
            "found": True,
            "run_id": run_id,
            "scope": "created_in_run",
            "items": alerts,
            "total": result["total"],
            "limit": 10,
            "truncated": result["total"] > 10,
        }

    def get_run_review_candidates(self, run_id: str) -> dict[str, Any]:
        try:
            result = self.reads.run_review(run_id)
        except LookupError:
            return {"found": False, "run_id": run_id, "items": [], "total": 0}
        return {
            "found": True,
            "run_id": run_id,
            "scope": "currently_visible_review_members_from_run",
            "items": [fields(r, PROCESS) for r in result["items"][:10]],
            "total": result["total"],
            "limit": 10,
            "truncated": result["total"] > 10,
        }

    def get_process_detail(self, identity: str) -> dict[str, Any]:
        try:
            row = self.reads.process(identity)
        except LookupError:
            return {"found": False, "identity": identity}
        return {
            "found": True,
            **fields(row, PROCESS),
            "evidence_level": "persisted_metadata_and_decision",
            "funnel_state": row.get("funnel_state"),
            "review_exists": row.get("review_exists"),
            "review_membership_persisted": row.get("review_membership_persisted"),
            "alert_ids": row.get("alert_ids", [])[:10],
            "source_url": row.get("source_url"),
            "associated_runs": [
                fields(h, {"run_id": "run_id", "source": "source", "at": "run_at"})
                for h in row.get("history", [])[-10:]
            ],
            "runs_total": len(row.get("history", [])),
        }

    def get_process_evidence(self, identity: str) -> dict[str, Any]:
        try:
            row = self.reads.process(identity)
            evidence = self.reads.evidence(identity)
        except LookupError:
            return {"found": False, "identity": identity}
        raw = evidence.get("facts") or []
        docs = evidence.get("documents") or []
        docs = [dict(d) for d in docs]
        for doc in docs:
            total = doc.get("total_pages")
            if doc.get("coverage_complete") is True:
                doc.update(processed_pages=total, coverage_ratio=1.0)
            elif total and doc.get("omitted_pages") is not None:
                processed = total - len(doc["omitted_pages"])
                doc.update(processed_pages=processed, coverage_ratio=processed / total)
        canonical = evidence.get("canonical_facts") or []
        facts = []
        preferred = {
            "product",
            "purchase_item",
            "official_budget_cop",
            "execution_term",
            "payment_method",
            "experience",
            "guarantee",
            "quantity",
        }
        selected_facts = sorted(raw, key=lambda f: f.get("fact_type") not in preferred)
        for f in selected_facts[:20]:
            normalized = f.get("normalized_value")
            suspicious = f.get(
                "suspicious", normalized.get("suspicious") if isinstance(normalized, dict) else None
            )
            loc = f.get("source_locator") or {}
            sources = loc.get("sources") or []
            facts.append(
                {
                    **fields(
                        f,
                        {
                            "fact_id": "id",
                            "type": "fact_type",
                            "string_value": "string_value",
                            "numeric_value": "numeric_value",
                            "boolean_value": "boolean_value",
                            "unit": "unit",
                            "confidence": "confidence",
                            "document_version_id": "document_version_id",
                        },
                    ),
                    "suspicious": suspicious,
                    "evidence_text": short(f.get("evidence_text"), 250),
                    "references": [
                        {
                            "document_name": short(s.get("original_name"), 150),
                            "page": (s.get("locator") or {}).get("page_number"),
                            "extraction_method": (s.get("locator") or {}).get("extraction_method"),
                        }
                        for s in sources[:2]
                    ],
                }
            )
        canonicals = []
        for c in canonical[:20]:
            value = c.get("canonical_value") or {}
            val = value.get("value") if isinstance(value, dict) else value
            if isinstance(val, (dict, list)):
                val = short(json.dumps(val, default=str), 250)
            canonicals.append(
                {
                    **fields(
                        c,
                        {
                            "id": "id",
                            "type": "canonical_type",
                            "status": "status",
                            "confidence": "confidence",
                        },
                    ),
                    "value": short(val, 250),
                }
            )
        return {
            "found": True,
            "identity": row["canonical_identity"],
            "metadata": fields(row, PROCESS),
            "inventory": evidence.get("inventory", [])[:10],
            "inventory_total": len(evidence.get("inventory", [])),
            "documentary_evidence_available": bool(raw or docs),
            "facts": facts,
            "facts_total": len(raw),
            "facts_truncated": len(raw) > 20,
            "canonicals": canonicals,
            "canonicals_total": len(canonical),
            "canonicals_truncated": len(canonical) > 20,
            "documents": [
                fields(
                    d,
                    {
                        "name": "name",
                        "document_version_id": "document_version_id",
                        "status": "status",
                        "extraction_mode": "extraction_mode",
                        "total_pages": "total_pages",
                        "processed_pages": "processed_pages",
                        "coverage_ratio": "coverage_ratio",
                        "text_length": "text_length",
                        "warning": "warning",
                    },
                )
                for d in docs[:10]
            ],
            "documents_total": len(docs),
            "documents_truncated": len(docs) > 10,
            "ocr_used": any(d.get("extraction_mode") in {"ocr", "mixed"} for d in docs),
            "partial_coverage": any(
                d.get("coverage_ratio") is not None and d["coverage_ratio"] < 1 for d in docs
            ),
            "manual_review_reasons": row.get("manual_review_reasons", []),
            "suspicious_facts_reported": "suspicious_facts" in row.get("manual_review_reasons", []),
            "provenance": {
                "sources": row.get("sources"),
                "source_url": row.get("source_url"),
                "process_id": row.get("process_id"),
            },
        }

    def dispatch(self, name: str, arguments: dict[str, Any]) -> Any:
        functions: dict[str, Callable[..., Any]] = {
            "get_eureka_commercial_profile": self.get_eureka_commercial_profile,
            "get_run_alerts": self.get_run_alerts,
            "get_run_review_candidates": self.get_run_review_candidates,
            "get_process_detail": self.get_process_detail,
            "get_process_evidence": self.get_process_evidence,
        }
        if name in functions:
            return functions[name](**arguments)
        return super().dispatch(name, arguments)
