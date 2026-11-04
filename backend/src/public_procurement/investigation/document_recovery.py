"""Research-only inventory augmentation. Exact official keys; no new discovery."""

from dataclasses import asdict, replace
from typing import Any, Protocol

from public_procurement.documents.services import SourceDocument


class InventorySource(Protocol):
    def fetch(self, portfolio_id: str) -> list[SourceDocument]: ...

    def fetch_by_contract(self, contract_id: str) -> list[SourceDocument]: ...


def recover_inventory(
    source: InventorySource,
    *,
    portfolio_id: str,
    contracts: list[dict[str, Any]],
    cached_documents: list[SourceDocument] | None = None,
) -> dict[str, Any]:
    """Keep canonical association separate from provider keys in a sidecar receipt."""
    primary = cached_documents if cached_documents is not None else source.fetch(portfolio_id)
    if any(d.portfolio_id != portfolio_id for d in primary):
        raise ValueError("Primary inventory belongs to another official portfolio")
    documents: dict[tuple[str, str], SourceDocument] = {}
    origins: dict[str, list[dict[str, str]]] = {}
    warnings, lookups = [], []

    def include(rows: list[SourceDocument], kind: str, key: str, field: str) -> None:
        for d in rows:
            normalized = replace(d, portfolio_id=portfolio_id)
            identity = d.dataset_id, d.id_documento
            origin = {
                "kind": kind,
                "value": key,
                "provider_field": field,
                "provider_process_identifier": d.portfolio_id,
                "associated_portfolio_id": portfolio_id,
                "dataset": d.dataset_id,
                "lookup_mode": "existing_inventory_receipt"
                if kind == "process_identifier" and cached_documents is not None
                else "official_identifier_lookup",
            }
            provenance = origins.setdefault(d.id_documento, [])
            if origin not in provenance:
                provenance.append(origin)
            if identity in documents and documents[identity] != normalized:
                warnings.append(
                    {"reason": "unresolved_document_relationship", "document_id": d.id_documento}
                )
                continue  # Keep primary evidence, never replace a version silently.
            if d.portfolio_id != portfolio_id:
                warnings.append(
                    {"reason": "provider_process_key_variant", "document_id": d.id_documento}
                )
            documents[identity] = normalized

    include(primary, "process_identifier", portfolio_id, "proceso")
    primary_ids = {d.id_documento for d in primary}
    for contract_id in sorted(
        {
            c["id_contrato"]
            for c in contracts
            if c.get("proceso_de_compra") == portfolio_id
            and isinstance(c.get("id_contrato"), str)
            and c["id_contrato"].startswith("CO1.PCCNTR.")
        }
    ):
        try:
            rows = source.fetch_by_contract(contract_id)
            lookups.append(
                {
                    "kind": "contract_identifier",
                    "value": contract_id,
                    "provider_field": "n_mero_de_contrato",
                    "count": len(rows),
                }
            )
            include(rows, "contract_identifier", contract_id, "n_mero_de_contrato")
        except (RuntimeError, ValueError) as exc:
            warnings.append(
                {
                    "reason": "incomplete_document_cycle",
                    "key": contract_id,
                    "error_type": type(exc).__name__,
                }
            )
    return {
        "documents": [asdict(d) for d in documents.values()],
        "discovery_provenance": origins,
        "primary_count": len(primary_ids),
        "merged_count": len(documents),
        "additional_document_ids": sorted(
            d.id_documento for d in documents.values() if d.id_documento not in primary_ids
        ),
        "lookups": lookups,
        "warnings": warnings,
    }
