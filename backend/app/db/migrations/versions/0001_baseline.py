"""Baseline schema (as created by the pre-Alembic ``create_all``).

Revision ID: 0001_baseline
Revises:
Create Date: 2026-11-23
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "diseases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("class_name", sa.String(100), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("symptoms", sa.Text()),
        sa.Column("prevention", sa.Text()),
        sa.Column("treatment", sa.Text()),
        sa.Column("treatment_steps", sa.Text()),
        sa.Column("recovery_info", sa.Text()),
        sa.Column("image_path", sa.String(500)),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_diseases_id", "diseases", ["id"])
    op.create_index("ix_diseases_class_name", "diseases", ["class_name"], unique=True)

    op.create_table(
        "diagnosis_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_image_path", sa.String(500), nullable=False),
        sa.Column("result_image_path", sa.String(500)),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("inference_time", sa.Float()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_diagnosis_history_id", "diagnosis_history", ["id"])
    op.create_index("ix_diagnosis_history_user_id", "diagnosis_history", ["user_id"])

    op.create_table(
        "detection_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "history_id",
            sa.Integer(),
            sa.ForeignKey("diagnosis_history.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("class_name", sa.String(100), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("x1", sa.Float(), nullable=False),
        sa.Column("y1", sa.Float(), nullable=False),
        sa.Column("x2", sa.Float(), nullable=False),
        sa.Column("y2", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_detection_results_id", "detection_results", ["id"])
    op.create_index("ix_detection_results_history_id", "detection_results", ["history_id"])


def downgrade() -> None:
    op.drop_table("detection_results")
    op.drop_table("diagnosis_history")
    op.drop_table("diseases")
    op.drop_table("users")
