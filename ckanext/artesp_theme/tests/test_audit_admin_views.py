from __future__ import annotations

from datetime import datetime

import ckan.model as model
import pytest
from ckan.tests import factories

from ckanext.artesp_theme.audit_model import AuditEvent, audit_event_table


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.usefixtures("with_plugins"),
]


@pytest.fixture(autouse=True)
def _ensure_audit_table(clean_db):
    bind = model.Session.get_bind()
    audit_event_table.create(bind=bind, checkfirst=True)
    yield


def test_audit_admin_route_returns_403_for_anonymous(app):
    response = app.get("/admin/audit", expect_errors=True)

    assert response.status_code == 403


def test_audit_admin_route_returns_403_for_non_sysadmin(app):
    user = factories.User()

    response = app.get(
        "/admin/audit",
        environ_base={"REMOTE_USER": user["name"]},
        expect_errors=True,
    )

    assert response.status_code == 403


def test_audit_admin_route_renders_filters_table_and_nav(app):
    sysadmin = factories.Sysadmin()
    event = AuditEvent(
        event_family="dataset",
        event_action="package_update",
        success=True,
        actor_id=sysadmin["id"],
        actor_name=sysadmin["name"],
        actor_type="sysadmin",
        channel="web",
        package_name="malha-rodoviaria",
    )
    event.occurred_at = datetime.utcnow()
    model.Session.add(event)
    model.Session.commit()

    response = app.get(
        "/admin/audit",
        environ_base={"REMOTE_USER": sysadmin["name"]},
        expect_errors=True,
    )

    assert response.status_code == 200
    assert "Auditoria" in response.text
    assert 'name="date_from"' in response.text
    assert 'name="date_to"' in response.text
    assert 'name="scope"' in response.text
    assert 'name="provider"' in response.text
    assert 'name="channel"' in response.text
    assert 'name="user"' in response.text
    assert 'name="ip"' in response.text
    assert 'name="object"' in response.text
    assert "Data/hora" in response.text
    assert "Tipo de usuário" in response.text
    assert "Dataset" in response.text
    assert "Resource" in response.text
    assert "malha-rodoviaria" in response.text
    assert 'href="/admin/audit"' in response.text
