"""Operational cycles only: no backfill or historical table modifications."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0016_eureka_operations"
down_revision = "0015_eureka_notifications"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE SCHEMA operations")
    op.create_table(
        "automation_cycle",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("radar_run_id", sa.Uuid(), sa.ForeignKey("eureka.radar_run.id"), unique=True),
        sa.Column("payload", JSONB(), nullable=False),
        sa.CheckConstraint(
            "status IN ('running','completed','completed_with_warnings','failed','skipped')",
            name="status",
        ),
        schema="operations",
    )
    op.create_index("ix_cycle_started", "automation_cycle", ["started_at"], schema="operations")
    op.create_index(
        "ix_cycle_status_started", "automation_cycle", ["status", "started_at"], schema="operations"
    )


def downgrade():
    op.drop_table("automation_cycle", schema="operations")
    op.execute("DROP SCHEMA operations")
