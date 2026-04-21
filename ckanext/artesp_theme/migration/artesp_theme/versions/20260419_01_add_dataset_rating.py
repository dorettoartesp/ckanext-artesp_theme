"""Add dataset_rating

Revision ID: 20260419_01
Revises:
Create Date: 2026-04-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "20260419_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "dataset_rating",
        sa.Column("id", sa.UnicodeText, primary_key=True),
        sa.Column(
            "user_id",
            sa.UnicodeText,
            sa.ForeignKey("user.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "package_id",
            sa.UnicodeText,
            sa.ForeignKey("package.id", onupdate="CASCADE", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("overall_rating", sa.SmallInteger, nullable=False),
        sa.Column(
            "criteria",
            JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("comment", sa.UnicodeText, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.CheckConstraint(
            "overall_rating BETWEEN 1 AND 5",
            name="ck_dataset_rating_overall",
        ),
        sa.UniqueConstraint(
            "user_id", "package_id", name="uq_dataset_rating_user_pkg",
        ),
    )
    op.create_index(
        "ix_dataset_rating_pkg_updated",
        "dataset_rating",
        ["package_id", "updated_at"],
    )


def downgrade():
    op.drop_index("ix_dataset_rating_pkg_updated", table_name="dataset_rating")
    op.drop_table("dataset_rating")
