"""Watched farms, in-app notifications and Web Push subscriptions.

Revision ID: 0005_farms_notifications
Revises: 0004_radar_location
Create Date: 2026-11-23
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_farms_notifications"
down_revision = "0004_radar_location"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "watched_farms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("radius_km", sa.Float(), nullable=False),
        sa.Column("crop_code", sa.String(32), nullable=True),
        sa.Column("alerts_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_watched_farms_id", "watched_farms", ["id"])
    op.create_index("ix_watched_farms_user_id", "watched_farms", ["user_id"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("link", sa.String(255), nullable=True),
        sa.Column("dedupe_key", sa.String(200), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("pushed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_notifications_id", "notifications", ["id"])
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("uq_notifications_user_dedupe", "notifications", ["user_id", "dedupe_key"], unique=True)

    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("endpoint", sa.String(1000), nullable=False, unique=True),
        sa.Column("p256dh", sa.String(255), nullable=False),
        sa.Column("auth", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_push_subscriptions_id", "push_subscriptions", ["id"])
    op.create_index("ix_push_subscriptions_user_id", "push_subscriptions", ["user_id"])


def downgrade() -> None:
    op.drop_table("push_subscriptions")
    op.drop_table("notifications")
    op.drop_table("watched_farms")
