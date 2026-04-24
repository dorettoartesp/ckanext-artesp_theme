"""Add sysadmin audit event table.

Revision ID: 20260424_01
Revises: 20260422_01
Create Date: 2026-04-24

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260424_01"
down_revision = "20260422_01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "audit_event",
        sa.Column("id", sa.UnicodeText(), primary_key=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("event_family", sa.Unicode(length=50), nullable=False),
        sa.Column("event_action", sa.Unicode(length=100), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("actor_id", sa.UnicodeText(), nullable=True),
        sa.Column("actor_name", sa.UnicodeText(), nullable=True),
        sa.Column("actor_display_name", sa.UnicodeText(), nullable=True),
        sa.Column("actor_type", sa.Unicode(length=50), nullable=False),
        sa.Column("auth_provider", sa.Unicode(length=50), nullable=True),
        sa.Column("channel", sa.Unicode(length=20), nullable=False),
        sa.Column("request_path", sa.UnicodeText(), nullable=True),
        sa.Column("ip_address", sa.Unicode(length=128), nullable=True),
        sa.Column("user_agent", sa.UnicodeText(), nullable=True),
        sa.Column("package_id", sa.UnicodeText(), nullable=True),
        sa.Column("package_name", sa.UnicodeText(), nullable=True),
        sa.Column("resource_id", sa.UnicodeText(), nullable=True),
        sa.Column("resource_name", sa.UnicodeText(), nullable=True),
        sa.Column(
            "details",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.create_index("ix_audit_event_occurred_at", "audit_event", ["occurred_at"])
    op.create_index(
        "ix_audit_event_family_action",
        "audit_event",
        ["event_family", "event_action"],
    )
    op.create_index("ix_audit_event_actor_id", "audit_event", ["actor_id"])
    op.create_index("ix_audit_event_package_id", "audit_event", ["package_id"])
    op.create_index("ix_audit_event_resource_id", "audit_event", ["resource_id"])
    op.create_index("ix_audit_event_ip_address", "audit_event", ["ip_address"])


def downgrade():
    op.drop_index("ix_audit_event_ip_address", table_name="audit_event")
    op.drop_index("ix_audit_event_resource_id", table_name="audit_event")
    op.drop_index("ix_audit_event_package_id", table_name="audit_event")
    op.drop_index("ix_audit_event_actor_id", table_name="audit_event")
    op.drop_index("ix_audit_event_family_action", table_name="audit_event")
    op.drop_index("ix_audit_event_occurred_at", table_name="audit_event")
    op.drop_table("audit_event")
