"""Esquema `investigation`: casos privados, instantáneas y notas (solo inserción).

Revision ID: 0005_investigation_schema
Revises: 0004_comparison_schema
Create Date: 2026-10-07 19:27:29.849735
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_investigation_schema"
down_revision: str | None = "0004_comparison_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS investigation")
    op.create_table(
        "case",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_case")),
        schema="investigation",
    )
    op.create_index(
        op.f("ix_investigation_case_owner_id"),
        "case",
        ["owner_id"],
        unique=False,
        schema="investigation",
    )
    op.create_table(
        "case_item",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("reference", sa.String(length=64), nullable=False),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["case_id"], ["investigation.case.id"], name=op.f("fk_case_item_case_id_case")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_case_item")),
        sa.UniqueConstraint(
            "case_id", "kind", "reference", name=op.f("uq_case_item_case_id_kind_reference")
        ),
        schema="investigation",
    )
    op.create_index(
        op.f("ix_investigation_case_item_case_id"),
        "case_item",
        ["case_id"],
        unique=False,
        schema="investigation",
    )
    op.create_table(
        "case_note",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["case_id"], ["investigation.case.id"], name=op.f("fk_case_note_case_id_case")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_case_note")),
        schema="investigation",
    )
    op.create_index(
        op.f("ix_investigation_case_note_case_id"),
        "case_note",
        ["case_id"],
        unique=False,
        schema="investigation",
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_investigation_case_note_case_id"), table_name="case_note", schema="investigation"
    )
    op.drop_table("case_note", schema="investigation")
    op.drop_index(
        op.f("ix_investigation_case_item_case_id"), table_name="case_item", schema="investigation"
    )
    op.drop_table("case_item", schema="investigation")
    op.drop_index(op.f("ix_investigation_case_owner_id"), table_name="case", schema="investigation")
    op.drop_table("case", schema="investigation")
    op.execute("DROP SCHEMA IF EXISTS investigation")
