"""Testes de integração para a funcionalidade de seguir datasets."""

import uuid

import pytest

import ckan.model as model
from ckan.tests import factories
from ckanext.artesp_theme.logic import auth_helpers


pytestmark = [
    pytest.mark.integration,
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.usefixtures("with_plugins"),
]


def _make_user(user_type):
    suffix = uuid.uuid4().hex[:10]
    user = model.User(
        name=f"{user_type}-{suffix}",
        email=f"{user_type}-{suffix}@example.com",
        state="active",
        plugin_extras={"artesp": {"user_type": user_type}},
    )
    model.Session.add(user)
    model.Session.flush()
    return {"id": user.id, "name": user.name}


def _make_org():
    org = auth_helpers.get_artesp_org()
    if org:
        return {"id": org.id}
    return factories.Organization(name="artesp")


def _make_public_dataset(org_id, creator_id):
    suffix = uuid.uuid4().hex[:10]
    pkg = model.Package(
        name=f"follow-test-{suffix}",
        title=f"Follow Test Dataset {suffix}",
        owner_org=org_id,
        state="active",
        private=False,
        creator_user_id=creator_id,
    )
    model.Session.add(pkg)
    model.Session.flush()
    return {"id": pkg.id, "name": pkg.name}


@pytest.fixture
def external_user():
    user = _make_user("external")
    yield user
    model.Session.rollback()


@pytest.fixture
def internal_user():
    user = _make_user("internal")
    yield user
    model.Session.rollback()


@pytest.fixture
def org():
    return _make_org()


@pytest.fixture
def public_dataset(org):
    suffix = uuid.uuid4().hex[:10]
    creator = model.User(
        name=f"creator-{suffix}",
        email=f"creator-{suffix}@example.com",
        state="active",
    )
    model.Session.add(creator)
    model.Session.flush()
    return _make_public_dataset(org["id"], creator.id)


@pytest.mark.ckan_config("WTF_CSRF_ENABLED", "false")
def test_usuario_externo_pode_seguir_dataset_publico(app, external_user, public_dataset):
    """Usuário externo (GovBR) autenticado deve conseguir seguir um dataset público."""
    resp = app.post(
        f"/dataset/follow/{public_dataset['id']}",
        environ_base={"REMOTE_USER": external_user["name"]},
    )
    assert resp.status_code == 200


@pytest.mark.ckan_config("WTF_CSRF_ENABLED", "false")
def test_usuario_interno_pode_seguir_dataset_publico(app, internal_user, public_dataset):
    """Usuário interno (LDAP) autenticado deve conseguir seguir um dataset público."""
    resp = app.post(
        f"/dataset/follow/{public_dataset['id']}",
        environ_base={"REMOTE_USER": internal_user["name"]},
    )
    assert resp.status_code == 200


@pytest.mark.ckan_config("WTF_CSRF_ENABLED", "false")
def test_usuario_externo_pode_desseguir_dataset(app, external_user, public_dataset):
    """Usuário externo que já segue um dataset deve conseguir dessegui-lo."""
    env = {"REMOTE_USER": external_user["name"]}
    app.post(f"/dataset/follow/{public_dataset['id']}", environ_base=env)
    resp = app.post(f"/dataset/unfollow/{public_dataset['id']}", environ_base=env)
    assert resp.status_code == 200


@pytest.mark.ckan_config("WTF_CSRF_ENABLED", "false")
def test_usuario_interno_pode_desseguir_dataset(app, internal_user, public_dataset):
    """Usuário interno que já segue um dataset deve conseguir dessegui-lo."""
    env = {"REMOTE_USER": internal_user["name"]}
    app.post(f"/dataset/follow/{public_dataset['id']}", environ_base=env)
    resp = app.post(f"/dataset/unfollow/{public_dataset['id']}", environ_base=env)
    assert resp.status_code == 200


def test_pagina_inclui_hx_headers_csrf_no_body(app):
    """Todas as páginas devem enviar o token CSRF via hx-headers no body para requisições HTMX."""
    resp = app.get("/dataset")
    html = resp.get_data(as_text=True)
    assert 'hx-headers=' in html, "body deve ter hx-headers para incluir CSRF em requisições HTMX"
    assert "X-CSRFToken" in html, "hx-headers deve conter X-CSRFToken"
