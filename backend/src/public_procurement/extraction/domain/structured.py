import hashlib
import json
import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .content import EvidenceFragment

RULE_VERSION = "structured-v1"


@dataclass(frozen=True)
class StructuredFact:
    process_id: uuid.UUID
    document_version_id: uuid.UUID
    content_fragment_id: uuid.UUID | None
    fact_type: str
    string_value: str | None
    numeric_value: Decimal | None
    boolean_value: bool | None
    unit: str | None
    normalized_value: Any
    confidence: Decimal
    evidence_text: str
    source_locator: dict[str, Any]
    rule_name: str
    rule_version: str
    fingerprint: str
    id: uuid.UUID | None = None


def make_fact(
    process_id: uuid.UUID,
    sources: tuple[EvidenceFragment, ...],
    fact_type: str,
    rule: str,
    version: str,
    *,
    string: str | None = None,
    number: Decimal | None = None,
    boolean: bool | None = None,
    unit: str | None = None,
    normalized: Any = None,
    confidence: str = "0.8",
    span: tuple[int, int] | None = None,
    group: str | None = None,
    subject: str | None = None,
) -> StructuredFact:
    if not sources or len({source.document_version_id for source in sources}) != 1:
        raise ValueError("Un hecho requiere evidencia de una única versión documental.")
    evidence = []
    texts = []
    for source in sources:
        start, end = span if span is not None and len(sources) == 1 else (0, len(source.text))
        texts.append(source.text[start:end])
        evidence.append(
            {
                "content_fragment_id": str(source.id),
                "extraction_run_id": str(source.extraction_run_id),
                "original_name": source.original_name,
                "locator": source.source_locator,
                "fragment_char_start": start,
                "fragment_char_end": end,
                "text": source.text[start:end],
            }
        )
    locator = {"sources": evidence, "group_key": group, "subject": subject}
    fingerprint = hashlib.sha256(
        json.dumps(
            {
                "type": fact_type,
                "locator": locator,
                "string": string,
                "number": str(number) if number is not None else None,
                "boolean": boolean,
                "unit": unit,
                "normalized": normalized,
            },
            ensure_ascii=True,
            sort_keys=True,
        ).encode()
    ).hexdigest()
    return StructuredFact(
        process_id,
        sources[0].document_version_id,
        sources[0].id if len(sources) == 1 else None,
        fact_type,
        string,
        number,
        boolean,
        unit,
        normalized,
        Decimal(confidence),
        "\n".join(texts),
        locator,
        rule,
        version,
        fingerprint,
    )
