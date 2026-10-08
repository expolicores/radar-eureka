"""Esquema `market`: observaciones de mercado de solo inserción.

Revision ID: 0003_market_schema
Revises: 0002_ingestion_schema
Create Date: 2026-10-07 18:50:26.272494
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_market_schema"
down_revision: str | None = "0002_ingestion_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS market")
    op.create_table(
        "observation",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("store", sa.String(length=32), nullable=False),
        sa.Column("source_reference", sa.String(length=128), nullable=False),
        sa.Column("product_description", sa.Text(), nullable=False),
        sa.Column("brand", sa.String(length=64), nullable=True),
        sa.Column("model", sa.String(length=64), nullable=True),
        sa.Column("ean", sa.String(length=14), nullable=True),
        sa.Column("screen_size_inches", sa.Integer(), nullable=False),
        sa.Column("resolution", sa.String(length=16), nullable=False),
        sa.Column("panel", sa.String(length=16), nullable=False),
        sa.Column("effective_price_cop", sa.BigInteger(), nullable=False),
        sa.Column("list_price_cop", sa.BigInteger(), nullable=True),
        sa.Column("vat_basis", sa.String(length=16), nullable=False),
        sa.Column("seller_is_store", sa.Boolean(), nullable=False),
        sa.Column("has_special_conditions", sa.Boolean(), nullable=False),
        sa.Column("observed_on", sa.Date(), nullable=False),
        sa.Column("method", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_observation")),
        sa.UniqueConstraint(
            "store", "source_reference", name=op.f("uq_observation_store_source_reference")
        ),
        schema="market",
    )
    op.create_index(
        op.f("ix_market_observation_observed_on"),
        "observation",
        ["observed_on"],
        unique=False,
        schema="market",
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_market_observation_observed_on"), table_name="observation", schema="market"
    )
    op.drop_table("observation", schema="market")
    op.execute("DROP SCHEMA IF EXISTS market")
