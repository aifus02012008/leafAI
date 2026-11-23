"""Disease radar: opt-in, coarsened location on diagnoses.

Revision ID: 0004_radar_location
Revises: 0003_treatments
Create Date: 2026-11-23
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_radar_location"
down_revision = "0003_treatments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("diagnosis_history") as batch:
        batch.add_column(sa.Column("latitude", sa.Float(), nullable=True))
        batch.add_column(sa.Column("longitude", sa.Float(), nullable=True))
        batch.add_column(sa.Column("share_to_radar", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_diagnosis_history_lat_lng", "diagnosis_history", ["latitude", "longitude"])


def downgrade() -> None:
    op.drop_index("ix_diagnosis_history_lat_lng", table_name="diagnosis_history")
    with op.batch_alter_table("diagnosis_history") as batch:
        batch.drop_column("share_to_radar")
        batch.drop_column("longitude")
        batch.drop_column("latitude")
