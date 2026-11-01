"""Read facade for conversational adapters; no acquisition or commercial decisions."""

import uuid
from typing import Any

from .review_services import project


class AssistantReadQueries:
    def __init__(self, review: Any, radar: Any, canonical: Any, documents: Any) -> None:
        self.review, self.radar, self.canonical, self.documents = (
            review,
            radar,
            canonical,
            documents,
        )
        self._process_cache: dict[str, dict[str, Any]] = {}

    def run_alerts(self, run_id: str) -> dict[str, Any]:
        self.radar.get_run(uuid.UUID(run_id))  # distinguish missing run from zero alerts
        return dict(self.radar.alerts_for_run(uuid.UUID(run_id), 10))

    def run_review(self, run_id: str) -> dict[str, Any]:
        self.radar.get_run(uuid.UUID(run_id))
        return dict(self.review.list({"run_id": run_id, "page": 1, "page_size": 10}))

    def process(self, identity: str) -> dict[str, Any]:
        if identity not in self._process_cache:
            data = self.review.repository.read(identity=identity)
            metadata = self.review.scoped_metadata(data["observations"])
            rows = project(data, metadata, self.review.clock())
            row = next((r for r in rows if identity in r["equivalent_identities"]), None)
            if row is None:
                raise LookupError("Proceso no encontrado")
            row["review_membership_persisted"] = any(
                i in data["ratings"] for i in row["equivalent_identities"]
            )
            row["review_exists"] = bool(
                self.review.list({"identity": row["canonical_identity"], "page_size": 1})["total"]
            )
            self._process_cache[identity] = row
        return self._process_cache[identity]

    def evidence(self, identity: str) -> dict[str, Any]:
        row = self.process(identity)
        evidence = self.review.evidence(row)
        reference = row.get("process_id")
        evidence["canonical_facts"] = self.canonical(reference) if reference else []
        evidence["inventory"] = self.documents(reference) if reference else []
        return dict(evidence)
