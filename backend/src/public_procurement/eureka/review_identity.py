"""Deterministic presentation aliases from persisted provider provenance only."""

import re
from typing import Any

from public_procurement.ingestion.services import canonical_process_identity


def observation_identity(item: dict[str, Any]) -> str:
    metadata = item.get("metadata") or {}
    reference = (
        metadata.get("source_identity")
        or metadata.get("id_ultima_fase")
        or metadata.get("process_reference")
        or item.get("secop_id", "")
    )
    return canonical_process_identity(
        str(reference), metadata.get("raw_source_reference", {}).get("Link")
    )


def review_aliases(observations: list[dict[str, Any]]) -> dict[str, str]:
    candidates: dict[str, set[str]] = {}
    for observation in observations:
        if observation["source"] != "licitaciones_info_cdp":
            continue
        item = observation["result"]
        if not isinstance(item, dict) or not isinstance(item.get("metadata"), dict):
            continue
        local = item["metadata"].get("process_reference")
        if not isinstance(local, str) or not re.fullmatch(r"licitaciones_info:\d+:\d+", local):
            continue
        official = observation_identity(item)
        if re.fullmatch(r"secop:CO1\.(?:NTC|REQ)\.\d+|secop1:\d+-\d+-\d+", official):
            candidates.setdefault(local, set()).add(official)
    # An ambiguous local identifier is not proof of equivalence.
    return {local: next(iter(values)) for local, values in candidates.items() if len(values) == 1}
