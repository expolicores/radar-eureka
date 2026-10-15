"""Descubrimiento y priorización comercial de Eureka sobre procesos persistidos.

Revision ID: 0008_eureka_discovery
Revises: 0007_documents_schema
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_eureka_discovery"
down_revision: str | None = "0007_documents_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS eureka")
    op.create_table(
        "opportunity",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "process_id", sa.Uuid(), sa.ForeignKey("ingestion.secop_process.id"), nullable=False
        ),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("priority_band", sa.String(16), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        *[
            sa.Column(
                name, sa.JSON().with_variant(postgresql.JSONB(), "postgresql"), nullable=False
            )
            for name in (
                "matched_categories",
                "matched_unspsc",
                "matched_terms",
                "matched_context",
                "penalties",
                "reasons",
                "review_notes",
                "config_snapshot",
            )
        ],
        sa.Column("rule_version", sa.String(64), nullable=False),
        sa.Column("discovered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("process_id"),
        schema="eureka",
    )
    op.create_index("ix_eureka_opportunity_active", "opportunity", ["active"], schema="eureka")


def downgrade() -> None:
    op.drop_table("opportunity", schema="eureka")
    op.execute("DROP SCHEMA eureka")
