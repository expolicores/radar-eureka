"""Esquema documents: inventario, relaciones, versiones inmutables e intentos."""

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    case,
    or_,
    select,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Mapped, Session, mapped_column

from public_procurement.shared.persistence import Base

from .domain.document import (
    AcquisitionStatus,
    Document,
    DocumentVersion,
    SourceDocument,
    StoredBinary,
)

SCHEMA = "documents"


class DocumentRecord(Base):
    __tablename__ = "document"
    __table_args__ = (UniqueConstraint("dataset_id", "id_documento"), {"schema": SCHEMA})
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    dataset_id: Mapped[str] = mapped_column(String(16))
    id_documento: Mapped[str] = mapped_column(String(128))
    portfolio_id: Mapped[str] = mapped_column(String(128), index=True)
    original_name: Mapped[str] = mapped_column(Text)
    fecha_carga: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    source_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16))
    last_error_code: Mapped[str | None] = mapped_column(String(64))
    last_error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    queried_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    downloaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DocumentProcessRecord(Base):
    __tablename__ = "document_process"
    __table_args__ = (UniqueConstraint("document_id", "process_id"), {"schema": SCHEMA})
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(f"{SCHEMA}.document.id"))
    # Referencia externa al módulo ingestion: nunca se accede a su tabla desde documents.
    process_id: Mapped[uuid.UUID] = mapped_column(index=True)
    portfolio_id: Mapped[str] = mapped_column(String(128))


class DocumentVersionRecord(Base):
    __tablename__ = "document_version"
    __table_args__ = (UniqueConstraint("document_id", "sha256"), {"schema": SCHEMA})
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(f"{SCHEMA}.document.id"), index=True)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    storage_path: Mapped[str] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(Text)
    observed_size: Mapped[int] = mapped_column(BigInteger)
    original_name: Mapped[str] = mapped_column(Text)
    fecha_carga: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    source_url: Mapped[str | None] = mapped_column(Text)
    downloaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AcquisitionAttemptRecord(Base):
    __tablename__ = "acquisition_attempt"
    __table_args__ = ({"schema": SCHEMA},)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey(f"{SCHEMA}.document.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16))
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)
    version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(f"{SCHEMA}.document_version.id")
    )


def _source(record: DocumentRecord) -> SourceDocument:
    return SourceDocument(
        record.id_documento,
        record.portfolio_id,
        record.original_name,
        record.fecha_carga,
        record.source_url,
        record.dataset_id,
    )


class SqlDocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_document(self, reference: str) -> Document | None:
        try:
            identifier = uuid.UUID(reference)
        except ValueError:
            condition = DocumentRecord.id_documento == reference
        else:
            condition = DocumentRecord.id == identifier
        record = self.session.scalars(
            select(DocumentRecord).where(condition, DocumentRecord.dataset_id == "dmgg-8hin")
        ).one_or_none()
        return (
            Document(record.id, _source(record), AcquisitionStatus(record.status))
            if record
            else None
        )

    def get_version(self, version_id: uuid.UUID) -> DocumentVersion | None:
        record = self.session.get(DocumentVersionRecord, version_id)
        if record is None:
            return None
        return DocumentVersion(
            record.id,
            record.document_id,
            record.sha256,
            record.storage_path,
            record.observed_size,
            record.content_type,
            record.original_name,
            record.fecha_carga,
            record.source_url,
            record.downloaded_at,
        )

    def latest_version(self, document_id: uuid.UUID) -> DocumentVersion | None:
        version_id = self.session.scalar(
            select(AcquisitionAttemptRecord.version_id)
            .where(
                AcquisitionAttemptRecord.document_id == document_id,
                AcquisitionAttemptRecord.status == "available",
                AcquisitionAttemptRecord.version_id.is_not(None),
            )
            .order_by(
                AcquisitionAttemptRecord.finished_at.desc(), AcquisitionAttemptRecord.id.desc()
            )
            .limit(1)
        )
        return self.get_version(version_id) if version_id else None

    def versions(self, document_id: uuid.UUID) -> list[DocumentVersion]:
        records = self.session.scalars(
            select(DocumentVersionRecord)
            .where(DocumentVersionRecord.document_id == document_id)
            .order_by(DocumentVersionRecord.downloaded_at, DocumentVersionRecord.id)
        ).all()
        return [
            DocumentVersion(
                r.id,
                r.document_id,
                r.sha256,
                r.storage_path,
                r.observed_size,
                r.content_type,
                r.original_name,
                r.fecha_carga,
                r.source_url,
                r.downloaded_at,
            )
            for r in records
        ]

    def sync(self, process_id: uuid.UUID, source: SourceDocument, at: datetime) -> None:
        values = dict(
            dataset_id=source.dataset_id,
            id_documento=source.id_documento,
            portfolio_id=source.portfolio_id,
            original_name=source.original_name,
            fecha_carga=source.fecha_carga,
            source_url=source.source_url,
        )
        statement = insert(DocumentRecord).values(
            id=uuid.uuid4(),
            **values,
            status=AcquisitionStatus.PENDING.value,
            created_at=at,
            queried_at=at,
        )
        doc_id = self.session.scalar(
            statement.on_conflict_do_update(
                index_elements=["dataset_id", "id_documento"],
                set_={
                    **values,
                    "queried_at": at,
                    "status": case(
                        (
                            or_(
                                DocumentRecord.original_name.is_distinct_from(source.original_name),
                                DocumentRecord.fecha_carga.is_distinct_from(source.fecha_carga),
                                DocumentRecord.source_url.is_distinct_from(source.source_url),
                            ),
                            AcquisitionStatus.PENDING.value,
                        ),
                        else_=DocumentRecord.status,
                    ),
                },
                where=DocumentRecord.portfolio_id == source.portfolio_id,
            ).returning(DocumentRecord.id)
        )
        if doc_id is None:
            raise ValueError("Un documento existente pertenece a otro portafolio.")
        link = insert(DocumentProcessRecord).values(
            id=uuid.uuid4(),
            document_id=doc_id,
            process_id=process_id,
            portfolio_id=source.portfolio_id,
        )
        self.session.execute(
            link.on_conflict_do_nothing(index_elements=["document_id", "process_id"])
        )

    def list_for(self, process_id: uuid.UUID, portfolio_id: str) -> list[Document]:
        records = self.session.scalars(
            select(DocumentRecord)
            .join(DocumentProcessRecord, DocumentProcessRecord.document_id == DocumentRecord.id)
            .where(
                DocumentProcessRecord.process_id == process_id,
                DocumentRecord.portfolio_id == portfolio_id,
            )
            .order_by(DocumentRecord.id_documento)
        ).all()
        return [Document(r.id, _source(r), AcquisitionStatus(r.status)) for r in records]

    def start_attempt(self, document: Document, at: datetime) -> uuid.UUID:
        identifier = uuid.uuid4()
        self.session.add(
            AcquisitionAttemptRecord(
                id=identifier,
                document_id=document.id,
                started_at=at,
                status=AcquisitionStatus.PENDING.value,
            )
        )
        return identifier

    def finish(
        self,
        document: Document,
        attempt_id: uuid.UUID,
        at: datetime,
        binary: StoredBinary | None,
        error_code: str | None,
        message: str | None,
    ) -> bool:
        record = self.session.scalars(
            select(DocumentRecord).where(DocumentRecord.id == document.id).with_for_update()
        ).one()
        attempt = self.session.get(AcquisitionAttemptRecord, attempt_id)
        if attempt is None:
            raise ValueError("Intento de adquisición inexistente.")
        if binary is not None and _source(record) != document.source:
            binary, error_code, message = (
                None,
                "inventory_changed",
                "El inventario cambió durante la descarga; reintenta.",
            )
        attempt.finished_at = at
        attempt.status = (
            AcquisitionStatus.AVAILABLE.value if binary else AcquisitionStatus.FAILED.value
        )
        attempt.error_code, attempt.error_message = error_code, message
        record.status = attempt.status
        record.last_error_code, record.last_error_message = error_code, message
        if binary is not None:
            version = self.session.scalars(
                select(DocumentVersionRecord).where(
                    DocumentVersionRecord.document_id == document.id,
                    DocumentVersionRecord.sha256 == binary.sha256,
                )
            ).one_or_none()
            if version is None:
                version = DocumentVersionRecord(
                    id=uuid.uuid4(),
                    document_id=document.id,
                    sha256=binary.sha256,
                    storage_path=binary.storage_path,
                    observed_size=binary.observed_size,
                    content_type=binary.content_type,
                    original_name=document.source.original_name,
                    fecha_carga=document.source.fecha_carga,
                    source_url=document.source.source_url,
                    downloaded_at=at,
                )
                self.session.add(version)
                self.session.flush()
            attempt.version_id = version.id
            record.downloaded_at = at
        return binary is not None
