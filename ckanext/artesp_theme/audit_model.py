"""SQLAlchemy model for sysadmin audit events."""
from __future__ import annotations

import datetime as _dt
import uuid
from typing import Any, Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

import ckan.model.meta as meta
import ckan.model.domain_object as domain_object


audit_event_table = sa.Table(
    "audit_event",
    meta.metadata,
    sa.Column("id", sa.types.UnicodeText, primary_key=True),
    sa.Column("occurred_at", sa.types.DateTime, nullable=False),
    sa.Column("event_family", sa.types.Unicode(50), nullable=False),
    sa.Column("event_action", sa.types.Unicode(100), nullable=False),
    sa.Column("success", sa.types.Boolean, nullable=False),
    sa.Column("actor_id", sa.types.UnicodeText, nullable=True),
    sa.Column("actor_name", sa.types.UnicodeText, nullable=True),
    sa.Column("actor_display_name", sa.types.UnicodeText, nullable=True),
    sa.Column("actor_type", sa.types.Unicode(50), nullable=False),
    sa.Column("auth_provider", sa.types.Unicode(50), nullable=True),
    sa.Column("channel", sa.types.Unicode(20), nullable=False),
    sa.Column("request_path", sa.types.UnicodeText, nullable=True),
    sa.Column("ip_address", sa.types.Unicode(128), nullable=True),
    sa.Column("user_agent", sa.types.UnicodeText, nullable=True),
    sa.Column("package_id", sa.types.UnicodeText, nullable=True),
    sa.Column("package_name", sa.types.UnicodeText, nullable=True),
    sa.Column("resource_id", sa.types.UnicodeText, nullable=True),
    sa.Column("resource_name", sa.types.UnicodeText, nullable=True),
    sa.Column(
        "details",
        JSONB,
        nullable=False,
        default=dict,
        server_default=sa.text("'{}'::jsonb"),
    ),
    sa.Index("ix_audit_event_occurred_at", "occurred_at"),
    sa.Index("ix_audit_event_family_action", "event_family", "event_action"),
    sa.Index("ix_audit_event_actor_id", "actor_id"),
    sa.Index("ix_audit_event_package_id", "package_id"),
    sa.Index("ix_audit_event_resource_id", "resource_id"),
    sa.Index("ix_audit_event_ip_address", "ip_address"),
)


class AuditEvent(domain_object.DomainObject):
    """Single persisted audit entry for authentication or CRUD activity."""

    id: str
    occurred_at: _dt.datetime
    event_family: str
    event_action: str
    success: bool
    actor_id: Optional[str]
    actor_name: Optional[str]
    actor_display_name: Optional[str]
    actor_type: str
    auth_provider: Optional[str]
    channel: str
    request_path: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    package_id: Optional[str]
    package_name: Optional[str]
    resource_id: Optional[str]
    resource_name: Optional[str]
    details: dict[str, Any]

    def __init__(
        self,
        event_family: str,
        event_action: str,
        success: bool,
        actor_type: str,
        channel: str,
        *,
        actor_id: Optional[str] = None,
        actor_name: Optional[str] = None,
        actor_display_name: Optional[str] = None,
        auth_provider: Optional[str] = None,
        request_path: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        package_id: Optional[str] = None,
        package_name: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        self.id = str(uuid.uuid4())
        self.occurred_at = _dt.datetime.utcnow()
        self.event_family = event_family
        self.event_action = event_action
        self.success = success
        self.actor_id = actor_id
        self.actor_name = actor_name
        self.actor_display_name = actor_display_name
        self.actor_type = actor_type
        self.auth_provider = auth_provider
        self.channel = channel
        self.request_path = request_path
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.package_id = package_id
        self.package_name = package_name
        self.resource_id = resource_id
        self.resource_name = resource_name
        self.details = details or {}


meta.registry.map_imperatively(AuditEvent, audit_event_table)
