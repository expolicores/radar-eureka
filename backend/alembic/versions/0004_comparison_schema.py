"""Esquema `comparison`: comparaciones de ítems (solo inserción, versionadas) y sus vínculos.

Revision ID: 0004_comparison_schema
Revises: 0003_market_schema
Create Date: 2026-10-07 18:53:56.378090
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_comparison_schema"
down_revision: str | None = "0003_market_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS comparison")
    op.create_table(
        "comparison_run",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("config_version_id", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evaluated_count", sa.Integer(), nullable=False),
        sa.Column("signal_count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_comparison_run")),
        schema="comparison",
    )
    op.create_table(
        "item_comparison",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("config_version_id", sa.String(length=32), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.Column("purchase_id", sa.Uuid(), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("signal_code", sa.String(length=32), nullable=True),
        sa.Column("unit_price_cop", sa.BigInteger(), nullable=True),
        sa.Column("match_type", sa.String(length=16), nullable=True),
        sa.Column("window_months", sa.Integer(), nullable=True),
        sa.Column("comparable_count", sa.Integer(), nullable=False),
        sa.Column("threshold_rule", sa.String(length=16), nullable=True),
        sa.Column("q1_cop", sa.BigInteger(), nullable=True),
        sa.Column("median_cop", sa.BigInteger(), nullable=True),
        sa.Column("q3_cop", sa.BigInteger(), nullable=True),
        sa.Column("threshold_cop", sa.BigInteger(), nullable=True),
        sa.Column("low_threshold_cop", sa.BigInteger(), nullable=True),
        sa.Column("deviation_pct", sa.Numeric(precision=8, scale=1), nullable=True),
        sa.Column("market_status", sa.String(length=16), nullable=True),
        sa.Column("market_reference_cop", sa.BigInteger(), nullable=True),
        sa.Column("market_deviation_pct", sa.Numeric(precision=8, scale=1), nullable=True),
        sa.Column("market_observation_count", sa.Integer(), nullable=False),
        sa.Column("market_store_count", sa.Integer(), nullable=False),
        sa.Column("confidence_score", sa.Integer(), nullable=True),
        sa.Column("confidence_level", sa.String(length=16), nullable=True),
        sa.Column("penalties", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["comparison.comparison_run.id"],
            name=op.f("fk_item_comparison_run_id_comparison_run"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_item_comparison")),
        schema="comparison",
    )
    op.create_index(
        "ix_comparison_item_comparison_current_outcome",
        "item_comparison",
        ["is_current", "outcome"],
        unique=False,
        schema="comparison",
    )
    op.create_index(
        op.f("ix_comparison_item_comparison_purchase_id"),
        "item_comparison",
        ["purchase_id"],
        unique=False,
        schema="comparison",
    )
    op.create_index(
        op.f("ix_comparison_item_comparison_signal_code"),
        "item_comparison",
        ["signal_code"],
        unique=False,
        schema="comparison",
    )
    op.create_table(
        "item_comparable",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("comparison_id", sa.Uuid(), nullable=False),
        sa.Column("purchase_id", sa.Uuid(), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("reference", sa.String(length=64), nullable=False),
        sa.Column("entity_name", sa.Text(), nullable=False),
        sa.Column("signed_on", sa.Date(), nullable=False),
        sa.Column("unit_price_cop", sa.BigInteger(), nullable=False),
        sa.Column("same_model", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["comparison_id"],
            ["comparison.item_comparison.id"],
            name=op.f("fk_item_comparable_comparison_id_item_comparison"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_item_comparable")),
        schema="comparison",
    )
    op.create_index(
        op.f("ix_comparison_item_comparable_comparison_id"),
        "item_comparable",
        ["comparison_id"],
        unique=False,
        schema="comparison",
    )
    op.create_table(
        "item_market_observation",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("comparison_id", sa.Uuid(), nullable=False),
        sa.Column("observation_id", sa.Uuid(), nullable=False),
        sa.Column("effective_price_cop", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["comparison_id"],
            ["comparison.item_comparison.id"],
            name=op.f("fk_item_market_observation_comparison_id_item_comparison"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_item_market_observation")),
        schema="comparison",
    )
    op.create_index(
        op.f("ix_comparison_item_market_observation_comparison_id"),
        "item_market_observation",
        ["comparison_id"],
        unique=False,
        schema="comparison",
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_comparison_item_market_observation_comparison_id"),
        table_name="item_market_observation",
        schema="comparison",
    )
    op.drop_table("item_market_observation", schema="comparison")
    op.drop_index(
        op.f("ix_comparison_item_comparable_comparison_id"),
        table_name="item_comparable",
        schema="comparison",
    )
    op.drop_table("item_comparable", schema="comparison")
    op.drop_index(
        op.f("ix_comparison_item_comparison_signal_code"),
        table_name="item_comparison",
        schema="comparison",
    )
    op.drop_index(
        op.f("ix_comparison_item_comparison_purchase_id"),
        table_name="item_comparison",
        schema="comparison",
    )
    op.drop_index(
        "ix_comparison_item_comparison_current_outcome",
        table_name="item_comparison",
        schema="comparison",
    )
    op.drop_table("item_comparison", schema="comparison")
    op.drop_table("comparison_run", schema="comparison")
    op.execute("DROP SCHEMA IF EXISTS comparison")
