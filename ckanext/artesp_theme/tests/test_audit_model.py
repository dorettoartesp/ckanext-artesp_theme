"""Tests for the audit event model and migration ownership filter."""

import ckan.model as model
import pytest
from ckan.tests import factories

from ckanext.artesp_theme.audit_model import AuditEvent, audit_event_table
from ckanext.artesp_theme.migration.artesp_theme.table_filter import (
    include_extension_table,
)


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.usefixtures("with_plugins"),
]


@pytest.fixture(autouse=True)
def _ensure_audit_event_table():
    bind = model.Session.get_bind()
    audit_event_table.create(bind=bind, checkfirst=True)
    model.Session.execute(audit_event_table.delete())
    model.Session.commit()
    yield
    model.Session.rollback()


@pytest.fixture
def user():
    return factories.User()


class TestAuditEvent:
    def test_create_and_persist(self, user):
        event = AuditEvent(
            event_family="authentication",
            event_action="login_success",
            success=True,
            actor_id=user["id"],
            actor_name=user["name"],
            actor_display_name=user["fullname"],
            actor_type="internal",
            auth_provider="local",
            channel="web",
            request_path="/user/login",
            ip_address="127.0.0.1",
            user_agent="pytest",
        )

        model.Session.add(event)
        model.Session.commit()

        loaded = model.Session.get(AuditEvent, event.id)
        assert loaded is not None
        assert loaded.event_family == "authentication"
        assert loaded.event_action == "login_success"
        assert loaded.success is True
        assert loaded.actor_type == "internal"
        assert loaded.auth_provider == "local"
        assert loaded.channel == "web"
        assert loaded.ip_address == "127.0.0.1"
        assert loaded.occurred_at is not None
        assert loaded.details == {}

    def test_defaults_details_to_empty_dict(self):
        event = AuditEvent(
            event_family="dataset",
            event_action="package_create",
            success=True,
            actor_type="sysadmin",
            channel="api",
        )

        assert event.details == {}
        assert event.occurred_at is not None
        assert event.id


class TestMigrationFilter:
    def test_include_object_accepts_audit_event_table(self):
        assert include_extension_table("audit_event", "table") is True

    def test_include_object_rejects_unowned_tables(self):
        assert include_extension_table("package", "table") is False
