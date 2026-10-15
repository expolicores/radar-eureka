"""Diagnósticos de extracción separados del mapa de contadores.

Revision ID: 0013_ocr_diagnostics
Revises: 0012_eureka_radar
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0013_ocr_diagnostics"
down_revision: str | None = "0012_eureka_radar"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "extraction_run_diagnostic",
        sa.Column(
            "extraction_run_id",
            sa.Uuid(),
            sa.ForeignKey("extraction.extraction_run.id"),
            primary_key=True,
        ),
        sa.Column("payload", sa.JSON().with_variant(JSONB(), "postgresql"), nullable=False),
        schema="extraction",
    )


def downgrade() -> None:
    op.drop_table("extraction_run_diagnostic", schema="extraction")
