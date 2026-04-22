"""Add rating administration status and audit trail.

Revision ID: 20260422_01
Revises: 20260419_01
Create Date: 2026-04-22

"""

from alembic import op
import sqlalchemy as sa


revision = "20260422_01"
down_revision = "20260419_01"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "dataset_rating",
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pendente"),
    )
    op.execute(
        """
        UPDATE dataset_rating
           SET status = 'finalizado'
         WHERE comment IS NULL OR btrim(comment) = ''
        """
    )
    op.create_table(
        "rating_action",
        sa.Column("id", sa.UnicodeText(), primary_key=True),
        sa.Column("rating_id", sa.UnicodeText(), sa.ForeignKey("dataset_rating.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", sa.UnicodeText(), nullable=False),
        sa.Column("status_before", sa.String(length=50), nullable=True),
        sa.Column("status_after", sa.String(length=50), nullable=False),
        sa.Column("note", sa.UnicodeText(), nullable=True),
        sa.Column("email_sent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_rating_action_rating_id",
        "rating_action",
        ["rating_id"],
    )


def downgrade():
    op.drop_index("ix_rating_action_rating_id", table_name="rating_action")
    op.drop_table("rating_action")
    op.drop_column("dataset_rating", "status")
