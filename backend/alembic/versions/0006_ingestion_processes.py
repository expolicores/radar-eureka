"""Procesos SECOP y bitácora separada de las compras simuladas.

Revision ID: 0006_ingestion_processes
Revises: 0005_investigation_schema
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_ingestion_processes"
down_revision: str | None = "0005_investigation_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "secop_process",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("dataset_id", sa.String(16), nullable=False),
        sa.Column("id_del_proceso", sa.String(128), nullable=False),
        sa.Column("id_del_portafolio", sa.String(128)),
        *[
            sa.Column(name, sa.Text())
            for name in (
                "reference",
                "entity_name",
                "department",
                "municipality",
                "title",
                "description",
                "modality",
                "phase",
                "status",
                "category_code",
                "source_url",
            )
        ],
        sa.Column("published_on", sa.Date()),
        sa.Column("last_published_on", sa.Date()),
        sa.Column("base_price_cop", sa.BigInteger()),
        sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_secop_process")),
        sa.UniqueConstraint(
            "dataset_id", "id_del_proceso", name=op.f("uq_secop_process_dataset_id_id_del_proceso")
        ),
        schema="ingestion",
    )
    for column in ("id_del_portafolio", "published_on"):
        op.create_index(
            f"ix_ingestion_secop_process_{column}", "secop_process", [column], schema="ingestion"
        )
    op.create_table(
        "process_sync_run",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("read_count", sa.Integer(), nullable=False),
        sa.Column("unique_count", sa.Integer(), nullable=False),
        sa.Column("changed_count", sa.Integer(), nullable=False),
        sa.Column("published_from", sa.Date()),
        sa.Column("published_before", sa.Date()),
        sa.Column("portfolio_id", sa.String(128)),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_process_sync_run")),
        schema="ingestion",
    )


def downgrade() -> None:
    op.drop_table("process_sync_run", schema="ingestion")
    op.drop_table("secop_process", schema="ingestion")
