"""Multi-crop support: crop_code on diseases & diagnoses, model version, user feedback.

Revision ID: 0002_multi_crop
Revises: 0001_baseline
Create Date: 2026-11-23
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_multi_crop"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("diseases") as batch:
        batch.add_column(sa.Column("crop_code", sa.String(32), nullable=False, server_default="tea"))
    op.drop_index("ix_diseases_class_name", table_name="diseases")
    op.create_index("ix_diseases_class_name", "diseases", ["class_name"])
    op.create_index("ix_diseases_crop_code", "diseases", ["crop_code"])
    op.create_index("uq_diseases_crop_class", "diseases", ["crop_code", "class_name"], unique=True)

    with op.batch_alter_table("diagnosis_history") as batch:
        batch.add_column(sa.Column("crop_code", sa.String(32), nullable=False, server_default="tea"))
        batch.add_column(sa.Column("model_version", sa.String(64), nullable=True))
        batch.add_column(sa.Column("user_feedback", sa.String(16), nullable=True))
        batch.add_column(sa.Column("feedback_at", sa.DateTime(), nullable=True))
    op.create_index("ix_diagnosis_history_crop_code", "diagnosis_history", ["crop_code"])


def downgrade() -> None:
    op.drop_index("ix_diagnosis_history_crop_code", table_name="diagnosis_history")
    with op.batch_alter_table("diagnosis_history") as batch:
        batch.drop_column("feedback_at")
        batch.drop_column("user_feedback")
        batch.drop_column("model_version")
        batch.drop_column("crop_code")

    op.drop_index("uq_diseases_crop_class", table_name="diseases")
    op.drop_index("ix_diseases_crop_code", table_name="diseases")
    op.drop_index("ix_diseases_class_name", table_name="diseases")
    op.create_index("ix_diseases_class_name", "diseases", ["class_name"], unique=True)
    with op.batch_alter_table("diseases") as batch:
        batch.drop_column("crop_code")
