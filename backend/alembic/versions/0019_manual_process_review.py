"""Human assessment keyed by exact process identity; independent of runs and scores."""

import sqlalchemy as sa
from alembic import op

revision = "0019_manual_process_review"
down_revision = "0018_licitaciones_cdp"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "manual_process_review",
        sa.Column("canonical_identity", sa.String(180), primary_key=True),
        sa.Column("manual_rating", sa.String(12), nullable=True),
        sa.Column("manual_note", sa.Text(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), nullable=True),
        sa.CheckConstraint(
            "manual_rating IS NULL OR manual_rating IN ('high','medium','low','discard')",
            name="ck_manual_process_review_rating",
        ),
        schema="eureka",
    )


def downgrade():
    op.drop_table("manual_process_review", schema="eureka")
