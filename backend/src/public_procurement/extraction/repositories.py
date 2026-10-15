"""Runs por intento y fragmentos de evidencia; los resultados finalizados son inmutables."""

import uuid
from dataclasses import asdict
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    inspect,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.orm import Mapped, Session, mapped_column

from public_procurement.shared.persistence import Base

from .domain.content import (
    CLAIM_STATUSES,
    REUSABLE_STATUSES,
    DocumentInput,
    EvidenceFragment,
    ExtractionResult,
    ExtractionStatus,
    ExtractorIdentity,
    Fragment,
    ParsedContent,
    SearchHit,
)
from .domain.text import normalize_extracted_text

JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")
CLAIM_PREDICATE = text(
    "status IN ('running','completed','partial_text','requires_ocr','empty_text')"
)


class ExtractionRunRecord(Base):
    __tablename__ = "extraction_run"
    __table_args__ = (
        Index(
            "uq_extraction_claim",
            "document_version_id",
            "extractor_name",
            "extractor_version",
            unique=True,
            postgresql_where=CLAIM_PREDICATE,
            sqlite_where=CLAIM_PREDICATE,
        ),
        {"schema": "extraction"},
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    document_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.document_version.id"), index=True
    )
    original_name: Mapped[str] = mapped_column(Text)
    extractor_name: Mapped[str] = mapped_column(String(64))
    extractor_version: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)
    text_length: Mapped[int] = mapped_column(Integer)
    fragment_count: Mapped[int] = mapped_column(Integer)
    input_sha256: Mapped[str] = mapped_column(String(64))
    pages_without_text: Mapped[list[int]] = mapped_column(JSON_TYPE)
    page_count: Mapped[int] = mapped_column(Integer)
    format_counts: Mapped[dict[str, int]] = mapped_column(JSON_TYPE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ExtractionDiagnosticRecord(Base):
    __tablename__ = "extraction_run_diagnostic"
    __table_args__ = ({"schema": "extraction"},)
    extraction_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("extraction.extraction_run.id"), primary_key=True
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE)


class ContentFragmentRecord(Base):
    __tablename__ = "content_fragment"
    __table_args__ = (UniqueConstraint("extraction_run_id", "ordinal"), {"schema": "extraction"})
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    extraction_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("extraction.extraction_run.id"), index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    page_number: Mapped[int | None] = mapped_column(Integer)
    paragraph_number: Mapped[int | None] = mapped_column(Integer)
    table_number: Mapped[int | None] = mapped_column(Integer)
    row_number: Mapped[int | None] = mapped_column(Integer)
    column_number: Mapped[int | None] = mapped_column(Integer)
    sheet_name: Mapped[str | None] = mapped_column(Text)
    cell_range: Mapped[str | None] = mapped_column(String(64))
    source_locator: Mapped[dict[str, Any]] = mapped_column(JSON_TYPE)
    normalized_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def result_from_run(
    run: ExtractionRunRecord, document: DocumentInput, reused: bool = False
) -> ExtractionResult:
    return ExtractionResult(
        document,
        ExtractorIdentity(run.extractor_name, run.extractor_version),
        ExtractionStatus(run.status),
        run.id,
        run.fragment_count,
        run.text_length,
        tuple(run.pages_without_text),
        run.page_count,
        reused,
        run.error_code,
        run.error_message,
        format_counts=run.format_counts,
    )


class SqlExtractionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def result(
        self, run: ExtractionRunRecord, document: DocumentInput, reused: bool = False
    ) -> ExtractionResult:
        from dataclasses import replace

        diagnostic = (
            self.session.get(ExtractionDiagnosticRecord, run.id)
            if self.has_table("extraction_run_diagnostic")
            else None
        )
        return replace(
            result_from_run(run, document, reused),
            diagnostics=diagnostic.payload if diagnostic else {},
        )

    def fragments(self, run_id: uuid.UUID) -> tuple[Fragment, ...]:
        rows = self.session.scalars(
            select(ContentFragmentRecord)
            .where(ContentFragmentRecord.extraction_run_id == run_id)
            .order_by(ContentFragmentRecord.ordinal)
        ).all()
        fields = (
            "ordinal",
            "text",
            "source_locator",
            "page_number",
            "paragraph_number",
            "table_number",
            "row_number",
            "column_number",
            "sheet_name",
            "cell_range",
        )
        return tuple(Fragment(**{name: getattr(row, name) for name in fields}) for row in rows)

    def ocr_attempts(self, document: DocumentInput, prefix: str) -> list[ExtractionResult]:
        rows = self.session.scalars(
            select(ExtractionRunRecord)
            .where(
                ExtractionRunRecord.document_version_id == document.document_version_id,
                ExtractionRunRecord.extractor_name == "pdf-hybrid-local",
                ExtractionRunRecord.extractor_version.startswith(prefix, autoescape=True),
            )
            .order_by(ExtractionRunRecord.started_at, ExtractionRunRecord.id)
        ).all()
        return [self.result(row, document, reused=True) for row in rows]

    def has_table(self, name: str) -> bool:
        inspector = inspect(self.session.connection())
        return "extraction" in inspector.get_schema_names() and inspector.has_table(
            name, schema="extraction"
        )

    def list_runs(self, documents: list[DocumentInput]) -> list[ExtractionResult]:
        versions = {
            document.document_version_id: document
            for document in documents
            if document.document_version_id is not None
        }
        runs = self.session.scalars(
            select(ExtractionRunRecord)
            .where(ExtractionRunRecord.document_version_id.in_(versions))
            .order_by(ExtractionRunRecord.started_at, ExtractionRunRecord.id)
        ).all()
        return [self.result(run, versions[run.document_version_id]) for run in runs]

    def evidence(self, version_ids: list[uuid.UUID]) -> list[EvidenceFragment]:
        from sqlalchemy import func

        ranked = (
            select(
                ExtractionRunRecord.id,
                func.row_number()
                .over(
                    partition_by=ExtractionRunRecord.document_version_id,
                    order_by=(
                        ExtractionRunRecord.finished_at.desc(),
                        ExtractionRunRecord.id.desc(),
                    ),
                )
                .label("rank"),
            )
            .where(
                ExtractionRunRecord.document_version_id.in_(version_ids),
                ExtractionRunRecord.status.in_(REUSABLE_STATUSES),
                ExtractionRunRecord.fragment_count > 0,
            )
            .subquery()
        )
        rows = self.session.execute(
            select(ContentFragmentRecord, ExtractionRunRecord)
            .join(
                ExtractionRunRecord,
                ContentFragmentRecord.extraction_run_id == ExtractionRunRecord.id,
            )
            .where(
                ExtractionRunRecord.id.in_(select(ranked.c.id).where(ranked.c.rank == 1)),
            )
            .order_by(ExtractionRunRecord.id, ContentFragmentRecord.ordinal)
        ).all()
        return [
            EvidenceFragment(
                f.id,
                r.document_version_id,
                r.id,
                r.original_name,
                f.ordinal,
                f.text,
                f.source_locator,
            )
            for f, r in rows
        ]

    def claim(
        self, document: DocumentInput, identity: ExtractorIdentity, at: datetime
    ) -> ExtractionResult:
        identifier = uuid.uuid4()
        statement = (
            insert(ExtractionRunRecord)
            .values(
                id=identifier,
                document_version_id=document.document_version_id,
                original_name=document.original_name,
                extractor_name=identity.name,
                extractor_version=identity.version,
                status="running",
                started_at=at,
                text_length=0,
                fragment_count=0,
                input_sha256=document.input_sha256,
                pages_without_text=[],
                page_count=0,
                format_counts={},
                created_at=at,
            )
            .on_conflict_do_nothing(
                index_elements=["document_version_id", "extractor_name", "extractor_version"],
                index_where=CLAIM_PREDICATE,
            )
            .returning(ExtractionRunRecord.id)
        )
        created = self.session.scalar(statement)
        run = self.session.scalars(
            select(ExtractionRunRecord).where(
                ExtractionRunRecord.document_version_id == document.document_version_id,
                ExtractionRunRecord.extractor_name == identity.name,
                ExtractionRunRecord.extractor_version == identity.version,
                ExtractionRunRecord.status.in_(CLAIM_STATUSES),
            )
        ).one()
        return self.result(run, document, reused=created is None)

    def finish(
        self,
        run_id: uuid.UUID,
        document: DocumentInput,
        parsed: ParsedContent | None,
        at: datetime,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> ExtractionResult:
        run = self.session.scalars(
            select(ExtractionRunRecord).where(ExtractionRunRecord.id == run_id).with_for_update()
        ).one()
        if run.status != "running":
            raise ValueError("No se puede sobrescribir una extracción finalizada.")
        run.finished_at = at
        run.status = parsed.status.value if parsed else "failed"
        run.error_code, run.error_message = error_code, error_message
        if parsed:
            if parsed.diagnostics and self.has_table("extraction_run_diagnostic"):
                self.session.add(
                    ExtractionDiagnosticRecord(extraction_run_id=run.id, payload=parsed.diagnostics)
                )
            run.format_counts = parsed.format_counts
            run.text_length, run.fragment_count = parsed.text_length, len(parsed.fragments)
            run.pages_without_text, run.page_count = (
                list(parsed.pages_without_text),
                parsed.page_count,
            )
            for fragment in parsed.fragments:
                values = asdict(fragment)
                values["source_locator"] = {
                    **fragment.source_locator,
                    "document_version_id": str(document.document_version_id),
                    "original_name": document.original_name,
                    "input_sha256": document.input_sha256,
                    "extractor_name": run.extractor_name,
                    "extractor_version": run.extractor_version,
                }
                self.session.add(
                    ContentFragmentRecord(
                        id=uuid.uuid4(),
                        extraction_run_id=run.id,
                        created_at=at,
                        normalized_text=normalize_extracted_text(fragment.text),
                        **values,
                    )
                )
            self.session.flush()
        return self.result(run, document)

    def record_validation_failure(
        self,
        document: DocumentInput,
        identity: ExtractorIdentity,
        at: datetime,
        code: str,
        message: str,
    ) -> ExtractionResult:
        run = ExtractionRunRecord(
            id=uuid.uuid4(),
            document_version_id=document.document_version_id,
            original_name=document.original_name,
            extractor_name=identity.name,
            extractor_version=identity.version,
            status="failed",
            started_at=at,
            finished_at=at,
            error_code=code,
            error_message=message,
            text_length=0,
            fragment_count=0,
            input_sha256=document.input_sha256,
            pages_without_text=[],
            page_count=0,
            format_counts={},
            created_at=at,
        )
        self.session.add(run)
        self.session.flush()
        return self.result(run, document)

    def search(self, version_ids: list[uuid.UUID], term: str, limit: int) -> list[SearchHit]:
        # Último extractor completado por versión: evitar duplicar coincidencias históricas.
        from sqlalchemy import func

        ranked = (
            select(
                ExtractionRunRecord.id,
                func.row_number()
                .over(
                    partition_by=ExtractionRunRecord.document_version_id,
                    order_by=(
                        ExtractionRunRecord.finished_at.desc(),
                        ExtractionRunRecord.id.desc(),
                    ),
                )
                .label("rank"),
            )
            .where(
                ExtractionRunRecord.document_version_id.in_(version_ids),
                ExtractionRunRecord.status.in_(REUSABLE_STATUSES),
                ExtractionRunRecord.fragment_count > 0,
            )
            .subquery()
        )
        rows = self.session.execute(
            select(ContentFragmentRecord, ExtractionRunRecord)
            .join(
                ExtractionRunRecord,
                ContentFragmentRecord.extraction_run_id == ExtractionRunRecord.id,
            )
            .where(
                ExtractionRunRecord.id.in_(select(ranked.c.id).where(ranked.c.rank == 1)),
                ContentFragmentRecord.normalized_text.contains(term, autoescape=True),
            )
            .order_by(ExtractionRunRecord.original_name, ContentFragmentRecord.ordinal)
            .limit(limit)
        ).all()
        results = []
        for fragment, run in rows:
            context = select(ContentFragmentRecord).where(
                ContentFragmentRecord.extraction_run_id == run.id
            )
            if fragment.table_number is not None:
                context = context.where(
                    ContentFragmentRecord.table_number == fragment.table_number,
                    ContentFragmentRecord.row_number == fragment.row_number,
                )
            elif fragment.sheet_name is not None:
                context = context.where(
                    ContentFragmentRecord.sheet_name == fragment.sheet_name,
                    ContentFragmentRecord.row_number == fragment.row_number,
                )
            else:
                context = context.where(
                    ContentFragmentRecord.ordinal.between(
                        fragment.ordinal - 1, fragment.ordinal + 1
                    )
                )
            neighbors = self.session.scalars(
                context.order_by(ContentFragmentRecord.ordinal).limit(12)
            ).all()
            results.append(
                SearchHit(
                    run.document_version_id,
                    run.original_name,
                    run.input_sha256,
                    run.id,
                    fragment.id,
                    fragment.text,
                    fragment.source_locator,
                    tuple({"text": n.text, "source_locator": n.source_locator} for n in neighbors),
                )
            )
        return results
