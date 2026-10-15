"""Adaptador interno: solo metadata persistida, sin Socrata ni documentos."""

from collections.abc import Iterator
from typing import Any

from public_procurement.ingestion.services import ProcessQueryService

from ..domain.discovery import ProcessFacts


class IngestionProcessSource:
    def __init__(self, processes: ProcessQueryService) -> None:
        self.processes = processes

    def header(self, reference: str) -> dict[str, Any]:
        stored = next(self.processes.iter_processes(reference=reference), None)
        if stored is None:
            raise ValueError("Proceso persistido no encontrado.")
        process = stored.process
        return {
            "process_id": stored.id,
            "secop_id": process.id_del_proceso,
            "reference": process.reference,
            "description": process.description,
            "source_url": process.source_url,
            "title": process.title or process.description,
            "entity": process.entity_name,
            "department": process.department,
            "municipality": process.municipality,
            "budget": process.base_price_cop,
            "published_at": process.published_on,
        }

    def iter_processes(
        self, reference: str | None, department: str | None
    ) -> Iterator[ProcessFacts]:
        for stored in self.processes.iter_processes(reference, department):
            process = stored.process
            yield ProcessFacts(
                stored.id,
                process.id_del_proceso,
                process.title,
                process.description,
                process.entity_name,
                process.department,
                process.base_price_cop,
                process.category_code,
                process.status,
                process.phase,
            )
