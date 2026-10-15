"""Corridas, estado inicial y alertas auditables de Radar Eureka.

Revision ID: 0012_eureka_radar
Revises: 0011_fact_consolidation
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0012_eureka_radar"
down_revision: str | None = "0011_fact_consolidation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    json_type = sa.JSON().with_variant(JSONB(), "postgresql")
    op.create_table(
        "radar_run",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("before_date", sa.Date(), nullable=False),
        sa.Column("regions", json_type, nullable=False),
        sa.Column("rule_version", sa.String(64), nullable=False),
        sa.Column("config_hash", sa.String(64), nullable=False),
        sa.Column("config_snapshot", json_type, nullable=False),
        *[
            sa.Column(name, sa.Integer(), nullable=False)
            for name in (
                "processes_seen",
                "new_processes",
                "candidates",
                "enriched",
                "alerts_created",
                "skipped",
                "failures",
            )
        ],
        sa.Column("errors", json_type, nullable=False),
        schema="eureka",
    )
    op.create_table(
        "radar_process_state",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("dataset_id", sa.String(16), nullable=False),
        sa.Column("secop_id", sa.String(128), nullable=False),
        sa.Column("process_id", sa.Uuid(), sa.ForeignKey("ingestion.secop_process.id")),
        sa.Column("first_run_id", sa.Uuid(), sa.ForeignKey("eureka.radar_run.id"), nullable=False),
        sa.Column("last_run_id", sa.Uuid(), sa.ForeignKey("eureka.radar_run.id"), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("dataset_id", "secop_id"),
        schema="eureka",
    )
    op.create_table(
        "radar_run_process",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("run_id", sa.Uuid(), sa.ForeignKey("eureka.radar_run.id"), nullable=False),
        sa.Column("dataset_id", sa.String(16), nullable=False),
        sa.Column("secop_id", sa.String(128), nullable=False),
        sa.Column("result", json_type, nullable=False),
        sa.UniqueConstraint("run_id", "dataset_id", "secop_id"),
        schema="eureka",
    )
    op.create_index(
        "ix_eureka_radar_run_process_run_id", "radar_run_process", ["run_id"], schema="eureka"
    )
    op.create_table(
        "alert",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "opportunity_id", sa.Uuid(), sa.ForeignKey("eureka.opportunity.id"), nullable=False
        ),
        sa.Column("run_id", sa.Uuid(), sa.ForeignKey("eureka.radar_run.id"), nullable=False),
        sa.Column("alert_type", sa.String(32), nullable=False),
        sa.Column("rule_version", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("priority", sa.String(16), nullable=False),
        sa.Column("review_required", sa.Boolean(), nullable=False),
        sa.Column("reasons", json_type, nullable=False),
        sa.Column("snapshot", json_type, nullable=False),
        sa.UniqueConstraint("opportunity_id", "alert_type", "rule_version"),
        schema="eureka",
    )
    op.create_index("ix_eureka_alert_created_at", "alert", ["created_at"], schema="eureka")


def downgrade() -> None:
    for table in ("alert", "radar_run_process", "radar_process_state", "radar_run"):
        op.drop_table(table, schema="eureka")
