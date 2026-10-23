"""Separate first tray entry from human assessment; do not invent historical dates."""

import sqlalchemy as sa
from alembic import op

revision = "0020_review_temporal_trace"
down_revision = "0019_manual_process_review"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "manual_process_review",
        sa.Column("review_first_seen_at", sa.DateTime(timezone=True), nullable=True),
        schema="eureka",
    )
    op.add_column(
        "manual_process_review",
        sa.Column(
            "review_first_seen_origin",
            sa.String(32),
            nullable=False,
            server_default="legacy_unknown",
        ),
        schema="eureka",
    )
    op.alter_column("manual_process_review", "reviewed_at", nullable=True, schema="eureka")
    # Existing human assessments prove existence, not the exact original tray-entry time.
    # Keep their first_seen NULL and explicitly legacy_unknown. Never copy reviewed_at/run dates.


def downgrade():
    # Unreviewed entry-only records have no human assessment to preserve in the old schema.
    op.execute("DELETE FROM eureka.manual_process_review WHERE reviewed_at IS NULL")
    op.alter_column("manual_process_review", "reviewed_at", nullable=False, schema="eureka")
    op.drop_column("manual_process_review", "review_first_seen_origin", schema="eureka")
    op.drop_column("manual_process_review", "review_first_seen_at", schema="eureka")
