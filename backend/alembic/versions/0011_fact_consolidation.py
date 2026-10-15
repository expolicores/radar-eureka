"""Snapshots canónicos inmutables y relaciones normalizadas de evidencia."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011_fact_consolidation"
down_revision: str | None = "0010_structured_extraction"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "canonical_fact",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("process_id", sa.Uuid(), nullable=False),
        sa.Column("canonical_type", sa.String(64), nullable=False),
        sa.Column("canonical_key", sa.String(64), nullable=False),
        sa.Column(
            "canonical_value",
            sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
            nullable=False,
        ),
        sa.Column("confidence", sa.Numeric(2, 1), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("rule_version", sa.String(64), nullable=False),
        sa.Column("input_digest", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "process_id",
            "rule_version",
            "input_digest",
            "canonical_type",
            "canonical_key",
            name="uq_canonical_snapshot_fact",
        ),
        schema="extraction",
    )
    op.create_index(
        "ix_extraction_canonical_fact_process_id",
        "canonical_fact",
        ["process_id"],
        schema="extraction",
    )
    op.create_table(
        "canonical_fact_evidence",
        sa.Column(
            "canonical_fact_id",
            sa.Uuid(),
            sa.ForeignKey("extraction.canonical_fact.id"),
            primary_key=True,
        ),
        sa.Column(
            "structured_fact_id",
            sa.Uuid(),
            sa.ForeignKey("extraction.structured_fact.id"),
            primary_key=True,
        ),
        schema="extraction",
    )


def downgrade() -> None:
    op.drop_table("canonical_fact_evidence", schema="extraction")
    op.drop_table("canonical_fact", schema="extraction")
