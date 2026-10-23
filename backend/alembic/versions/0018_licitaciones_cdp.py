"""Source/progress on existing runs and atomic cross-provider alert identity."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

from public_procurement.ingestion.domain.identity import canonical_process_identity

revision = "0018_licitaciones_cdp"
down_revision = "0017_offer_deadline"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "radar_run",
        sa.Column("source", sa.String(32), nullable=False, server_default="socrata"),
        schema="eureka",
    )
    op.add_column(
        "radar_run",
        sa.Column("metrics", JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        schema="eureka",
    )
    op.add_column("alert", sa.Column("canonical_key", sa.String(180)), schema="eureka")
    # Preserve historical alerts. Only the earliest owns each key; never delete history.
    connection = op.get_bind()
    seen = set()
    rows = connection.execute(
        sa.text("""
        SELECT a.id, p.id_del_proceso, p.source_url FROM eureka.alert a
        JOIN eureka.opportunity o ON o.id = a.opportunity_id
        JOIN ingestion.secop_process p ON p.id = o.process_id
        ORDER BY a.created_at, a.id
    """)
    ).mappings()
    for row in rows:
        key = canonical_process_identity(row["id_del_proceso"], row["source_url"])
        if key not in seen:
            connection.execute(
                sa.text("UPDATE eureka.alert SET canonical_key=:key WHERE id=:id"),
                {"key": key, "id": row["id"]},
            )
            seen.add(key)
    op.create_unique_constraint(
        "uq_alert_canonical_key", "alert", ["canonical_key"], schema="eureka"
    )


def downgrade():
    op.drop_constraint("uq_alert_canonical_key", "alert", schema="eureka", type_="unique")
    op.drop_column("alert", "canonical_key", schema="eureka")
    op.drop_column("radar_run", "metrics", schema="eureka")
    op.drop_column("radar_run", "source", schema="eureka")
