"""init tables

Revision ID: 20250816_000001
Revises:
Create Date: 2025-08-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20250816_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("params", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("finished_at", sa.DateTime, nullable=True),
        sa.Column("error", sa.Text, nullable=True),
    )
    op.create_table(
        "pairs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("job_id", sa.Integer, sa.ForeignKey("jobs.id", ondelete="CASCADE"), index=True),
        sa.Column("similarity", sa.Float, index=True),
        sa.Column("label", sa.String(length=32)),
        sa.Column("file_a", sa.Text, nullable=False),
        sa.Column("size_a", sa.BigInteger),
        sa.Column("duration_a", sa.Float),
        sa.Column("res_a", sa.String(length=32)),
        sa.Column("file_b", sa.Text, nullable=False),
        sa.Column("size_b", sa.BigInteger),
        sa.Column("duration_b", sa.Float),
        sa.Column("res_b", sa.String(length=32)),
    )
    op.create_table(
        "groups",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("job_id", sa.Integer, sa.ForeignKey("jobs.id", ondelete="CASCADE"), index=True),
        sa.Column("representative_path", sa.Text, nullable=False),
        sa.Column("count", sa.Integer, server_default="0"),
        sa.Column("total_size", sa.BigInteger, server_default="0"),
    )
    op.create_table(
        "group_files",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("group_id", sa.Integer, sa.ForeignKey("groups.id", ondelete="CASCADE"), index=True),
        sa.Column("path", sa.Text, nullable=False),
        sa.Column("size", sa.BigInteger),
        sa.Column("duration", sa.Float),
        sa.Column("res", sa.String(length=32)),
        sa.Column("is_representative", sa.Boolean, server_default=sa.text("false")),
    )


def downgrade():
    op.drop_table("group_files")
    op.drop_table("groups")
    op.drop_table("pairs")
    op.drop_table("jobs")
