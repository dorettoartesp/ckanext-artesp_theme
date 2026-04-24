"""Tests for audit capture from CKAN action signals."""

from types import SimpleNamespace

import ckan.model as model
import pytest
from ckan.tests import factories

from ckanext.artesp_theme.audit_model import AuditEvent, audit_event_table
from ckanext.artesp_theme.logic import audit_capture


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.usefixtures("with_plugins"),
]


@pytest.fixture(autouse=True)
def _ensure_audit_event_table(clean_db):
    bind = model.Session.get_bind()
    audit_event_table.create(bind=bind, checkfirst=True)
    yield


def test_handle_action_succeeded_ignores_untracked_actions():
    audit_capture.handle_action_succeeded(
        "package_show",
        context={"user": "tester"},
        data_dict={"id": "pkg-1"},
        result={"id": "pkg-1"},
    )

    assert model.Session.query(AuditEvent).count() == 0


def test_handle_action_succeeded_persists_package_create_as_web(monkeypatch):
    user = factories.User()

    monkeypatch.setattr(
        audit_capture,
        "request",
        SimpleNamespace(
            path="/dataset/new",
            headers={},
            environ={"REMOTE_ADDR": "10.0.0.5"},
            user_agent=SimpleNamespace(string="pytest-browser"),
        ),
    )

    audit_capture.handle_action_succeeded(
        "package_create",
        context={"user": user["name"]},
        data_dict={"owner_org": "artesp"},
        result={"id": "pkg-1", "name": "meu-dataset", "title": "Meu Dataset"},
    )

    event = model.Session.query(AuditEvent).one()
    assert event.event_family == "dataset"
    assert event.event_action == "package_create"
    assert event.success is True
    assert event.actor_id == user["id"]
    assert event.actor_type == "internal"
    assert event.channel == "web"
    assert event.ip_address == "10.0.0.5"
    assert event.package_id == "pkg-1"
    assert event.package_name == "meu-dataset"


def test_handle_action_succeeded_persists_resource_delete_as_api(monkeypatch):
    sysadmin = factories.Sysadmin()

    monkeypatch.setattr(
        audit_capture,
        "request",
        SimpleNamespace(
            path="/api/3/action/resource_delete",
            headers={"X-Forwarded-For": "203.0.113.10, 10.0.0.1"},
            environ={"REMOTE_ADDR": "10.0.0.1"},
            user_agent=SimpleNamespace(string="pytest-api"),
        ),
    )
    monkeypatch.setattr(
        audit_capture.auth_helpers,
        "get_resource",
        lambda data_dict: SimpleNamespace(id=data_dict["id"], name="arquivo.csv"),
    )
    monkeypatch.setattr(
        audit_capture.auth_helpers,
        "get_package_from_resource",
        lambda data_dict: SimpleNamespace(id="pkg-9", name="dataset-9"),
    )

    audit_capture.handle_action_succeeded(
        "resource_delete",
        context={"user": sysadmin["name"]},
        data_dict={"id": "res-1"},
        result=None,
    )

    event = model.Session.query(AuditEvent).one()
    assert event.event_family == "resource"
    assert event.event_action == "resource_delete"
    assert event.actor_type == "sysadmin"
    assert event.channel == "api"
    assert event.ip_address == "203.0.113.10"
    assert event.package_id == "pkg-9"
    assert event.package_name == "dataset-9"
    assert event.resource_id == "res-1"
    assert event.resource_name == "arquivo.csv"


def test_handle_user_logged_in_persists_auth_event(monkeypatch):
    user = factories.User()

    monkeypatch.setattr(
        audit_capture,
        "request",
        SimpleNamespace(
            path="/user/login",
            headers={},
            environ={"REMOTE_ADDR": "127.0.0.1"},
            user_agent=SimpleNamespace(string="pytest-browser"),
        ),
    )
    monkeypatch.setattr(audit_capture, "session", {"artesp_auth_provider": "local"})

    audit_capture.handle_user_logged_in("app", user=SimpleNamespace(
        id=user["id"],
        name=user["name"],
        display_name=user["fullname"],
        sysadmin=False,
        plugin_extras={},
    ))

    event = model.Session.query(AuditEvent).one()
    assert event.event_family == "authentication"
    assert event.event_action == "login_success"
    assert event.auth_provider == "local"
    assert event.channel == "web"


def test_handle_user_logged_in_skips_user_verify_requests(monkeypatch):
    user = factories.User()

    monkeypatch.setattr(
        audit_capture,
        "request",
        SimpleNamespace(
            path="/user/verify",
            headers={},
            environ={"REMOTE_ADDR": "127.0.0.1"},
            user_agent=SimpleNamespace(string="pytest-browser"),
        ),
    )

    audit_capture.handle_user_logged_in("app", user=SimpleNamespace(
        id=user["id"],
        name=user["name"],
        display_name=user["fullname"],
        sysadmin=False,
        plugin_extras={},
    ))

    assert model.Session.query(AuditEvent).count() == 0


def test_handle_failed_login_persists_failure(monkeypatch):
    monkeypatch.setattr(
        audit_capture,
        "request",
        SimpleNamespace(
            path="/user/login",
            headers={},
            environ={"REMOTE_ADDR": "198.51.100.7"},
            user_agent=SimpleNamespace(string="pytest-browser"),
        ),
    )

    audit_capture.handle_failed_login("alice")

    event = model.Session.query(AuditEvent).one()
    assert event.event_family == "authentication"
    assert event.event_action == "login_failure"
    assert event.success is False
    assert event.actor_name == "alice"
    assert event.auth_provider == "local"
    assert event.ip_address == "198.51.100.7"
