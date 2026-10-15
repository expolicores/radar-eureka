"""Outbox and cross-type alert claims; no backfill or historical table changes."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0015_eureka_notifications"
down_revision = "0014_transversal_search"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA notifications")
    op.create_table(
        "notification",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("alert_id", sa.Uuid(), sa.ForeignKey("eureka.alert.id")),
        sa.Column("channel", sa.String(16), nullable=False),
        sa.Column("recipient", sa.String(254), nullable=False),
        sa.Column("notification_type", sa.String(16), nullable=False),
        sa.Column("delivery_scope", sa.String(16), nullable=False),
        sa.Column("delivery_mode", sa.String(16), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        *[
            sa.Column(
                name, sa.DateTime(timezone=True), nullable=name not in ("created_at", "updated_at")
            )
            for name in (
                "created_at",
                "updated_at",
                "sent_at",
                "captured_at",
                "failed_at",
                "processing_started_at",
                "next_retry_at",
                "provider_idempotency_until",
                "digest_from",
                "digest_to",
            )
        ],
        sa.Column("delivery_ambiguous", sa.Boolean(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("provider_message_id", sa.String(256)),
        sa.Column("error_code", sa.String(64)),
        sa.Column("error_message", sa.Text()),
        sa.Column("payload_snapshot", JSONB(), nullable=False),
        sa.Column("attempt_history", JSONB(), nullable=False),
        sa.Column("idempotency_key", sa.String(64), nullable=False),
        sa.UniqueConstraint("idempotency_key"),
        sa.UniqueConstraint(
            "id", "recipient", "channel", "delivery_scope", name="uq_notification_membership_parent"
        ),
        sa.CheckConstraint(
            "status IN ('pending','processing','captured','sent','retryable','failed','skipped')",
            name="status",
        ),
        sa.CheckConstraint("delivery_scope IN ('capture','real')", name="scope"),
        sa.CheckConstraint("channel='email'", name="channel"),
        sa.CheckConstraint(
            "recipient=lower(recipient) AND recipient=trim(recipient)", name="recipient_normalized"
        ),
        sa.CheckConstraint("notification_type IN ('immediate','digest')", name="type"),
        sa.CheckConstraint("attempt_count>=0 AND retry_count>=0", name="attempts"),
        schema="notifications",
    )
    op.create_index(
        "ix_notification_ready",
        "notification",
        ["delivery_scope", "status", "next_retry_at"],
        schema="notifications",
    )
    op.create_index(
        "ix_notification_created", "notification", ["created_at", "id"], schema="notifications"
    )
    op.create_table(
        "notification_alert",
        sa.Column("notification_id", sa.Uuid(), primary_key=True),
        sa.Column("alert_id", sa.Uuid(), sa.ForeignKey("eureka.alert.id"), primary_key=True),
        sa.Column("recipient", sa.String(254), nullable=False),
        sa.Column("channel", sa.String(16), nullable=False),
        sa.Column("delivery_scope", sa.String(16), nullable=False),
        sa.ForeignKeyConstraint(
            ["notification_id", "recipient", "channel", "delivery_scope"],
            [
                "notifications.notification.id",
                "notifications.notification.recipient",
                "notifications.notification.channel",
                "notifications.notification.delivery_scope",
            ],
        ),
        sa.UniqueConstraint(
            "alert_id", "recipient", "channel", "delivery_scope", name="uq_notification_alert_claim"
        ),
        schema="notifications",
    )
    op.create_index(
        "ix_notification_alert_alert_id", "notification_alert", ["alert_id"], schema="notifications"
    )


def downgrade() -> None:
    op.drop_table("notification_alert", schema="notifications")
    op.drop_table("notification", schema="notifications")
    op.execute("DROP SCHEMA notifications")
