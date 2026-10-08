"""Esquema `ingestion`: compras de televisores, sus ítems y la bitácora de ingesta.

Revision ID: 0002_ingestion_schema
Revises: 0001_initial
Create Date: 2026-10-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_ingestion_schema"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = "ingestion"


def _timestamps() -> list[sa.Column[object]]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
    op.create_table(
        "purchase",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("id_contrato", sa.String(64), nullable=True),
        sa.Column("identificador_de_la_orden", sa.String(64), nullable=True),
        sa.Column("proceso_de_compra", sa.String(64), nullable=True),
        sa.Column("entity_name", sa.Text(), nullable=False),
        sa.Column("entity_department", sa.String(64), nullable=False),
        sa.Column("entity_municipality", sa.String(128), nullable=True),
        sa.Column("supplier_name", sa.Text(), nullable=False),
        sa.Column("supplier_nit", sa.String(32), nullable=True),
        sa.Column("supplier_is_natural_person", sa.Boolean(), nullable=False),
        sa.Column("object_description", sa.Text(), nullable=False),
        sa.Column("modality", sa.String(96), nullable=False),
        sa.Column("total_value_cop", sa.BigInteger(), nullable=True),
        sa.Column("signed_on", sa.Date(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id", name="pk_purchase"),
        sa.UniqueConstraint("source", "id_contrato", name="uq_purchase_source_id_contrato"),
        sa.UniqueConstraint(
            "source",
            "identificador_de_la_orden",
            name="uq_purchase_source_identificador_de_la_orden",
        ),
        sa.CheckConstraint(
            "(source = 'secop_ii' AND id_contrato IS NOT NULL"
            " AND identificador_de_la_orden IS NULL)"
            " OR (source = 'tvec' AND identificador_de_la_orden IS NOT NULL"
            " AND id_contrato IS NULL)",
            name="ck_purchase_source_identifier",
        ),
        sa.CheckConstraint(
            "NOT supplier_is_natural_person OR supplier_nit IS NULL",
            name="ck_purchase_natural_person_without_document",
        ),
        schema=SCHEMA,
    )
    op.create_index("ix_ingestion_purchase_signed_on", "purchase", ["signed_on"], schema=SCHEMA)
    op.create_table(
        "purchase_item",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("purchase_id", sa.Uuid(), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("classification", sa.String(32), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=True),
        sa.Column("unit_price_cop", sa.BigInteger(), nullable=True),
        sa.Column("unit_price_status", sa.String(32), nullable=False),
        sa.Column("vat_basis", sa.String(32), nullable=False),
        sa.Column("screen_size_inches", sa.Integer(), nullable=True),
        sa.Column("resolution", sa.String(16), nullable=True),
        sa.Column("panel", sa.String(16), nullable=True),
        sa.Column("is_smart", sa.Boolean(), nullable=True),
        sa.Column("brand", sa.String(64), nullable=True),
        sa.Column("model", sa.String(64), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_purchase_item"),
        sa.ForeignKeyConstraint(
            ["purchase_id"],
            [f"{SCHEMA}.purchase.id"],
            name="fk_purchase_item_purchase_id_purchase",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "purchase_id", "line_number", name="uq_purchase_item_purchase_id_line_number"
        ),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_ingestion_purchase_item_classification",
        "purchase_item",
        ["classification"],
        schema=SCHEMA,
    )
    op.create_table(
        "ingestion_run",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cutoff_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("read_count", sa.Integer(), nullable=False),
        sa.Column("new_count", sa.Integer(), nullable=False),
        sa.Column("updated_count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_ingestion_run"),
        schema=SCHEMA,
    )
    op.create_index("ix_ingestion_ingestion_run_source", "ingestion_run", ["source"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_table("ingestion_run", schema=SCHEMA)
    op.drop_table("purchase_item", schema=SCHEMA)
    op.drop_table("purchase", schema=SCHEMA)
    op.execute(f"DROP SCHEMA IF EXISTS {SCHEMA}")
