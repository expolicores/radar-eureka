"""Hechos estructurados con evidencia y reglas versionadas."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_structured_extraction"
down_revision: str | None = "0009_extraction_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    json_type = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")
    op.create_table(
        "structured_fact",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("process_id", sa.Uuid(), nullable=False),
        sa.Column(
            "document_version_id",
            sa.Uuid(),
            sa.ForeignKey("documents.document_version.id"),
            nullable=False,
        ),
        sa.Column(
            "content_fragment_id", sa.Uuid(), sa.ForeignKey("extraction.content_fragment.id")
        ),
        sa.Column("fact_type", sa.String(64), nullable=False),
        sa.Column("string_value", sa.Text()),
        sa.Column("numeric_value", sa.Numeric(24, 6)),
        sa.Column("boolean_value", sa.Boolean()),
        sa.Column("unit", sa.String(64)),
        sa.Column("normalized_value", json_type),
        sa.Column("confidence", sa.Numeric(2, 1), nullable=False),
        sa.Column("evidence_text", sa.Text(), nullable=False),
        sa.Column("source_locator", json_type, nullable=False),
        sa.Column("rule_name", sa.String(64), nullable=False),
        sa.Column("rule_version", sa.String(64), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "process_id",
            "document_version_id",
            "rule_version",
            "fingerprint",
            name="uq_structured_fact_evidence",
        ),
        schema="extraction",
    )
    op.create_index(
        "ix_extraction_structured_fact_process_id",
        "structured_fact",
        ["process_id"],
        schema="extraction",
    )
    op.create_index(
        "ix_extraction_structured_fact_document_version_id",
        "structured_fact",
        ["document_version_id"],
        schema="extraction",
    )


def downgrade() -> None:
    op.drop_table("structured_fact", schema="extraction")
