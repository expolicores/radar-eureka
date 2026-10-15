"""Extracciones versionadas y fragmentos de evidencia localizables.

Revision ID: 0009_extraction_schema
Revises: 0008_eureka_discovery
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_extraction_schema"
down_revision: str | None = "0008_eureka_discovery"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
CLAIM = sa.text("status IN ('running','completed','partial_text','requires_ocr','empty_text')")


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS extraction")
    op.create_table(
        "extraction_run",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "document_version_id",
            sa.Uuid(),
            sa.ForeignKey("documents.document_version.id"),
            nullable=False,
        ),
        sa.Column("original_name", sa.Text(), nullable=False),
        sa.Column("extractor_name", sa.String(64), nullable=False),
        sa.Column("extractor_version", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("error_code", sa.String(64)),
        sa.Column("error_message", sa.Text()),
        sa.Column("text_length", sa.Integer(), nullable=False),
        sa.Column("fragment_count", sa.Integer(), nullable=False),
        sa.Column("input_sha256", sa.String(64), nullable=False),
        sa.Column(
            "pages_without_text",
            sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
            nullable=False,
        ),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column(
            "format_counts",
            sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema="extraction",
    )
    op.create_index(
        "ix_extraction_extraction_run_document_version_id",
        "extraction_run",
        ["document_version_id"],
        schema="extraction",
    )
    op.create_index(
        "uq_extraction_claim",
        "extraction_run",
        ["document_version_id", "extractor_name", "extractor_version"],
        unique=True,
        postgresql_where=CLAIM,
        sqlite_where=CLAIM,
        schema="extraction",
    )
    op.create_table(
        "content_fragment",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "extraction_run_id",
            sa.Uuid(),
            sa.ForeignKey("extraction.extraction_run.id"),
            nullable=False,
        ),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        *[
            sa.Column(name, sa.Integer())
            for name in (
                "page_number",
                "paragraph_number",
                "table_number",
                "row_number",
                "column_number",
            )
        ],
        sa.Column("sheet_name", sa.Text()),
        sa.Column("cell_range", sa.String(64)),
        sa.Column(
            "source_locator",
            sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
            nullable=False,
        ),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("extraction_run_id", "ordinal"),
        schema="extraction",
    )
    op.create_index(
        "ix_extraction_content_fragment_extraction_run_id",
        "content_fragment",
        ["extraction_run_id"],
        schema="extraction",
    )


def downgrade() -> None:
    op.drop_table("content_fragment", schema="extraction")
    op.drop_table("extraction_run", schema="extraction")
    op.execute("DROP SCHEMA extraction")
