"""Inventario documental compartido, versiones e intentos de adquisición.

Revision ID: 0007_documents_schema
Revises: 0006_ingestion_processes
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_documents_schema"
down_revision: str | None = "0006_ingestion_processes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS documents")
    op.create_table(
        "document",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("dataset_id", sa.String(16), nullable=False),
        sa.Column("id_documento", sa.String(128), nullable=False),
        sa.Column("portfolio_id", sa.String(128), nullable=False),
        sa.Column("original_name", sa.Text(), nullable=False),
        sa.Column("fecha_carga", sa.DateTime()),
        sa.Column("source_url", sa.Text()),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("last_error_code", sa.String(64)),
        sa.Column("last_error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("queried_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("downloaded_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("dataset_id", "id_documento"),
        schema="documents",
    )
    op.create_index(
        "ix_documents_document_portfolio_id", "document", ["portfolio_id"], schema="documents"
    )
    op.create_table(
        "document_process",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("document_id", sa.Uuid(), sa.ForeignKey("documents.document.id"), nullable=False),
        sa.Column("process_id", sa.Uuid(), nullable=False),
        sa.Column("portfolio_id", sa.String(128), nullable=False),
        sa.UniqueConstraint("document_id", "process_id"),
        schema="documents",
    )
    op.create_index(
        "ix_documents_document_process_process_id",
        "document_process",
        ["process_id"],
        schema="documents",
    )
    op.create_table(
        "document_version",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("document_id", sa.Uuid(), sa.ForeignKey("documents.document.id"), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("content_type", sa.Text(), nullable=False),
        sa.Column("observed_size", sa.BigInteger(), nullable=False),
        sa.Column("original_name", sa.Text(), nullable=False),
        sa.Column("fecha_carga", sa.DateTime()),
        sa.Column("source_url", sa.Text()),
        sa.Column("downloaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("document_id", "sha256"),
        schema="documents",
    )
    for column in ("document_id", "sha256"):
        op.create_index(
            f"ix_documents_document_version_{column}",
            "document_version",
            [column],
            schema="documents",
        )
    op.create_table(
        "acquisition_attempt",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("document_id", sa.Uuid(), sa.ForeignKey("documents.document.id"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("error_code", sa.String(64)),
        sa.Column("error_message", sa.Text()),
        sa.Column("version_id", sa.Uuid(), sa.ForeignKey("documents.document_version.id")),
        schema="documents",
    )
    op.create_index(
        "ix_documents_acquisition_attempt_document_id",
        "acquisition_attempt",
        ["document_id"],
        schema="documents",
    )


def downgrade() -> None:
    for table in ("acquisition_attempt", "document_version", "document_process", "document"):
        op.drop_table(table, schema="documents")
    op.execute("DROP SCHEMA documents")
