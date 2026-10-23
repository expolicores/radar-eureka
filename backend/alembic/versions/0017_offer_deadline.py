"""Conserva el valor original de fecha de recepción; sin backfill ni inferencias."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0017_offer_deadline"
down_revision = "0016_eureka_operations"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "secop_process",
        sa.Column("offer_deadline_raw", JSONB(none_as_null=True), nullable=True),
        schema="ingestion",
    )


def downgrade():
    op.drop_column("secop_process", "offer_deadline_raw", schema="ingestion")
