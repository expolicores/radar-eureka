"""Local human review persistence; discovery and alert writers are not involved."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, String, Text, func, literal_column, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker

from public_procurement.shared.persistence import Base

from .radar_repositories import AlertRecord, RadarRunProcessRecord, RadarRunRecord
from .repositories import OpportunityRecord


class ManualProcessReviewRecord(Base):
    __tablename__ = "manual_process_review"
    __table_args__ = (
        CheckConstraint(
            "manual_rating IS NULL OR manual_rating IN ('high','medium','low','discard')",
            name="ck_manual_process_review_rating",
        ),
        {"schema": "eureka"},
    )

    canonical_identity: Mapped[str] = mapped_column(String(180), primary_key=True)
    manual_rating: Mapped[str | None] = mapped_column(String(12))
    manual_note: Mapped[str] = mapped_column(Text, default="")
    review_first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_first_seen_origin: Mapped[str] = mapped_column(String(32), default="observed")
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column()


class ReviewRepository:
    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self.sessions = sessions

    def read(self, since: datetime | None = None, identity: str | None = None) -> dict[str, Any]:
        with self.sessions() as session:
            result: Any = RadarRunProcessRecord.result
            if (
                since is not None or identity is not None
            ) and session.get_bind().dialect.name == "postgresql":
                # Page diagnostics can be megabytes per process. The list only needs
                # the persisted coverage flags; full diagnostics stay in detail/history.
                result = result.op("-")(literal_column("'extraction_coverage'")).op("#-")(
                    literal_column("'{decision,snapshot,extraction_coverage}'")
                )
            query = (
                select(result, RadarRunRecord)
                .join(RadarRunRecord, RadarRunProcessRecord.run_id == RadarRunRecord.id)
                .where(RadarRunRecord.source.in_(("socrata", "licitaciones_info_cdp")))
                .order_by(RadarRunRecord.started_at, RadarRunRecord.id)
            )
            if identity is not None:
                payload = RadarRunProcessRecord.result
                metadata = payload["metadata"]
                refs = {identity, identity.removeprefix("secop:").removeprefix("secop1:")}
                candidates = [
                    payload["secop_id"].as_string(),
                    *(
                        metadata[k].as_string()
                        for k in ("source_identity", "id_ultima_fase", "process_reference")
                    ),
                ]
                if session.get_bind().dialect.name == "postgresql":
                    link = metadata["raw_source_reference"]["Link"].as_string()
                    candidates.extend(
                        [
                            func.substring(link, "(CO1[.](NTC|REQ)[.][0-9]+)"),
                            func.substring(link, "numConstancia=([0-9]+-[0-9]+-[0-9]+)"),
                        ]
                    )
                match = or_(*(candidate.in_(refs) for candidate in candidates))
                local_refs = (
                    select(metadata["process_reference"].as_string()).where(match).correlate(None)
                )
                query = query.where(
                    or_(match, metadata["process_reference"].as_string().in_(local_refs))
                )
            if since is not None:
                query = query.where(RadarRunRecord.started_at >= since)
                # Only persisted review members can appear in this inbox. Resolve
                # exact provider/official references in SQL before decoding large JSON.
                if session.get_bind().dialect.name == "postgresql":
                    identities = list(
                        session.scalars(select(ManualProcessReviewRecord.canonical_identity))
                    )
                    references = set(identities)
                    references.update(
                        i.removeprefix("secop:").removeprefix("secop1:") for i in identities
                    )
                    payload = RadarRunProcessRecord.result
                    metadata = payload["metadata"]
                    link = metadata["raw_source_reference"]["Link"].as_string()
                    candidates = [
                        payload["secop_id"].as_string(),
                        *(
                            metadata[k].as_string()
                            for k in ("source_identity", "id_ultima_fase", "process_reference")
                        ),
                        func.substring(link, "(CO1[.](NTC|REQ)[.][0-9]+)"),
                        func.substring(link, "numConstancia=([0-9]+-[0-9]+-[0-9]+)"),
                    ]
                    query = query.where(
                        or_(*(candidate.in_(references) for candidate in candidates))
                    )
            observations = session.execute(query).all()
            return {
                "observations": [
                    {
                        "source": run.source,
                        "run_id": str(run.id),
                        "run_at": run.started_at,
                        "regions": run.regions,
                        "config_snapshot": run.config_snapshot,
                        "result": item,
                    }
                    for item, run in observations
                    if run.source in {"socrata", "licitaciones_info_cdp"}
                ],
                "alerts": [
                    {"id": str(a.id), "canonical_identity": a.canonical_key, "snapshot": a.snapshot}
                    for a in session.scalars(select(AlertRecord))
                ],
                "opportunities": {
                    str(o.process_id): {"id": str(o.id), "score": o.score}
                    for o in session.scalars(select(OpportunityRecord))
                },
                "ratings": {
                    r.canonical_identity: self.rating(r)
                    for r in session.scalars(select(ManualProcessReviewRecord))
                },
            }

    @staticmethod
    def rating(row: ManualProcessReviewRecord) -> dict[str, Any]:
        return {
            "review_first_seen_at": row.review_first_seen_at,
            "review_first_seen_origin": row.review_first_seen_origin,
            "manual_rating": row.manual_rating,
            "manual_note": row.manual_note,
            "reviewed_at": row.reviewed_at,
            "reviewed_by": row.reviewed_by,
        }

    def enter(self, identities: list[str], at: datetime, origin: str) -> dict[str, Any]:
        """Insert once, including concurrent observers; never update entry or human assessment."""
        with self.sessions.begin() as session:
            if identities:
                session.execute(
                    insert(ManualProcessReviewRecord)
                    .values(
                        [
                            {
                                "canonical_identity": identity,
                                "manual_note": "",
                                "review_first_seen_at": at,
                                "review_first_seen_origin": origin,
                            }
                            for identity in set(identities)
                        ]
                    )
                    .on_conflict_do_nothing(index_elements=["canonical_identity"])
                )
            return {
                row.canonical_identity: self.rating(row)
                for row in session.scalars(select(ManualProcessReviewRecord))
            }

    def save(
        self, identity: str, rating: str | None, note: str, user: uuid.UUID | None, at: datetime
    ) -> dict[str, Any]:
        values = {
            "canonical_identity": identity,
            "manual_rating": rating,
            "manual_note": note,
            "reviewed_by": user,
            "reviewed_at": at,
        }
        with self.sessions.begin() as session:
            session.execute(
                insert(ManualProcessReviewRecord)
                .values(
                    **values, review_first_seen_at=None, review_first_seen_origin="legacy_unknown"
                )
                .on_conflict_do_update(
                    index_elements=["canonical_identity"],
                    set_={k: v for k, v in values.items() if k != "canonical_identity"},
                )
            )
            record = session.get(ManualProcessReviewRecord, identity)
            if record is None:
                raise RuntimeError("No se guardó la evaluación humana")
            result = self.rating(record)
        return {"canonical_identity": identity, **result}
