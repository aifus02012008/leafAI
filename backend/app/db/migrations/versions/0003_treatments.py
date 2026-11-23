"""Treatment tracking: spray log, follow-ups, lesion severity on diagnoses.

Revision ID: 0003_treatments
Revises: 0002_multi_crop
Create Date: 2026-11-23
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_treatments"
down_revision = "0002_multi_crop"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("diagnosis_history") as batch:
        batch.add_column(sa.Column("severity_pct", sa.Float(), nullable=True))

    op.create_table(
        "treatments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("diagnosis_id", sa.Integer(), sa.ForeignKey("diagnosis_history.id", ondelete="SET NULL"), nullable=True),
        sa.Column("crop_code", sa.String(32), nullable=False),
        sa.Column("disease_name", sa.String(200), nullable=True),
        sa.Column("active_code", sa.String(64), nullable=False),
        sa.Column("product_name", sa.String(200), nullable=True),
        sa.Column("applied_on", sa.Date(), nullable=False),
        sa.Column("phi_days", sa.Integer(), nullable=True),
        sa.Column("followup_due_on", sa.Date(), nullable=False),
        sa.Column("area_m2", sa.Float(), nullable=True),
        sa.Column("total_product", sa.Float(), nullable=True),
        sa.Column("estimated_cost", sa.Float(), nullable=True),
        sa.Column("severity_before", sa.Float(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="awaiting_followup"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_treatments_id", "treatments", ["id"])
    op.create_index("ix_treatments_user_id", "treatments", ["user_id"])
    op.create_index("ix_treatments_crop_code", "treatments", ["crop_code"])
    op.create_index("ix_treatments_active_code", "treatments", ["active_code"])

    op.create_table(
        "treatment_followups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("treatment_id", sa.Integer(), sa.ForeignKey("treatments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("diagnosis_id", sa.Integer(), sa.ForeignKey("diagnosis_history.id", ondelete="SET NULL"), nullable=True),
        sa.Column("severity_after", sa.Float(), nullable=True),
        sa.Column("relative_change", sa.Float(), nullable=True),
        sa.Column("verdict", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_treatment_followups_id", "treatment_followups", ["id"])
    op.create_index("ix_treatment_followups_treatment_id", "treatment_followups", ["treatment_id"])


def downgrade() -> None:
    op.drop_table("treatment_followups")
    op.drop_table("treatments")
    with op.batch_alter_table("diagnosis_history") as batch:
        batch.drop_column("severity_pct")
