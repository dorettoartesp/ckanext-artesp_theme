from __future__ import annotations

from datetime import datetime, timedelta
import ckan.model as model
import pytest

from ckanext.artesp_theme.audit_model import AuditEvent, audit_event_table
from ckanext.artesp_theme.logic import audit_query


pytestmark = [
    pytest.mark.integration,
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.usefixtures("with_plugins"),
]


@pytest.fixture(autouse=True)
def _ensure_audit_table():
    bind = model.Session.get_bind()
    audit_event_table.create(bind=bind, checkfirst=True)
    model.Session.execute(audit_event_table.delete())
    model.Session.commit()
    yield
    model.Session.rollback()


def _add_event(**overrides):
    event = AuditEvent(
        event_family=overrides.pop("event_family", "authentication"),
        event_action=overrides.pop("event_action", "login_success"),
        success=overrides.pop("success", True),
        actor_type=overrides.pop("actor_type", "internal"),
        channel=overrides.pop("channel", "web"),
        actor_id=overrides.pop("actor_id", None),
        actor_name=overrides.pop("actor_name", None),
        auth_provider=overrides.pop("auth_provider", None),
        ip_address=overrides.pop("ip_address", None),
        package_name=overrides.pop("package_name", None),
        resource_name=overrides.pop("resource_name", None),
    )
    event.occurred_at = overrides.pop("occurred_at", datetime.utcnow())
    for key, value in overrides.items():
        setattr(event, key, value)
    model.Session.add(event)
    model.Session.commit()
    return event


def test_search_audit_events_filters_and_orders_descending():
    older = _add_event(
        event_family="dataset",
        event_action="package_create",
        actor_name="alice",
        package_name="rodovias-antigas",
        channel="api",
        occurred_at=datetime.utcnow() - timedelta(days=2),
    )
    newer = _add_event(
        event_family="dataset",
        event_action="package_update",
        actor_name="alice",
        package_name="rodovias-atuais",
        channel="api",
        occurred_at=datetime.utcnow() - timedelta(hours=1),
    )
    _add_event(
        event_family="authentication",
        event_action="login_success",
        actor_name="bob",
        auth_provider="govbr",
        occurred_at=datetime.utcnow(),
    )

    result = audit_query.search_audit_events(
        {
            "scope": "dataset",
            "channel": "api",
            "user": "alice",
            "object": "rodovias",
            "page": "1",
        }
    )

    assert result["item_count"] == 2
    assert [event.id for event in result["events"]] == [newer.id, older.id]


def test_search_audit_events_applies_provider_ip_and_page_filters():
    sysadmin = {"id": "sysadmin-id", "name": "sysadmin"}
    for index in range(55):
        _add_event(
            event_family="authentication",
            event_action="login_success",
            actor_id=sysadmin["id"],
            actor_name=sysadmin["name"],
            actor_type="sysadmin",
            auth_provider="govbr" if index < 52 else "ldap",
            ip_address="203.0.113.10" if index < 52 else "198.51.100.9",
            occurred_at=datetime.utcnow() - timedelta(minutes=index),
        )

    result = audit_query.search_audit_events(
        {
            "scope": "authentication",
            "provider": "govbr",
            "ip": "203.0.113.10",
            "page": "2",
        }
    )

    assert result["item_count"] == 52
    assert len(result["events"]) == 2
    assert all(event.auth_provider == "govbr" for event in result["events"])
    assert all(event.ip_address == "203.0.113.10" for event in result["events"])


def test_search_audit_events_applies_requested_sorting():
    _add_event(
        event_family="dataset",
        event_action="package_update",
        actor_name="alice",
        package_name="zeta-dataset",
        occurred_at=datetime.utcnow() - timedelta(hours=2),
    )
    _add_event(
        event_family="dataset",
        event_action="package_update",
        actor_name="alice",
        package_name="alpha-dataset",
        occurred_at=datetime.utcnow() - timedelta(hours=1),
    )

    result = audit_query.search_audit_events(
        {
            "scope": "dataset",
            "sort_by": "package_name",
            "sort_dir": "asc",
        }
    )

    assert [event.package_name for event in result["events"]] == [
        "alpha-dataset",
        "zeta-dataset",
    ]
    assert result["filters"]["sort_by"] == "package_name"
    assert result["filters"]["sort_dir"] == "asc"
