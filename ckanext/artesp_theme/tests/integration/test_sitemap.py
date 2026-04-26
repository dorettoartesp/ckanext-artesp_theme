"""Tests for /sitemap.xml route."""
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


def _unique_name(prefix):
    return "{}-{}".format(prefix, uuid.uuid4().hex[:8])


def _artesp_org():
    org = auth_helpers.get_artesp_org()
    if org:
        return {"id": org.id, "name": org.name}
    return factories.Organization(name="artesp")


def test_sitemap_structure_and_org(app):
    org_name = _unique_name('minha-org-teste')
    org = model.Group(
        name=org_name,
        title=org_name,
        type="organization",
        is_organization=True,
    )
    org.state = "active"
    model.Session.add(org)
    model.Session.commit()

    resp = app.get('/sitemap.xml')

    assert resp.status_code == 200
    assert 'application/xml' in resp.content_type
    assert '<urlset' in resp.text
    assert 'http://www.sitemaps.org/schemas/sitemap/0.9' in resp.text
    assert '<loc>' in resp.text
    assert '/</loc>' in resp.text
    assert org_name in resp.text


def test_sitemap_dataset_visibility(app):
    org = _artesp_org()
    public_name = _unique_name('meu-dataset-public')
    private_name = _unique_name('dataset-privado')
    factories.Dataset(name=public_name, owner_org=org['id'])
    factories.Dataset(name=private_name, private=True, owner_org=org['id'])

    resp = app.get('/sitemap.xml')

    assert public_name in resp.text
    assert private_name not in resp.text
