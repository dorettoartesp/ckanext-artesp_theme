"""Tests for /sitemap.xml route."""
import uuid

import pytest
import ckan.plugins.toolkit as tk
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


def test_sitemap_returns_200_with_xml_content_type(app):
    resp = app.get('/sitemap.xml')

    assert resp.status_code == 200
    assert 'application/xml' in resp.content_type


def test_sitemap_contains_urlset_element(app):
    resp = app.get('/sitemap.xml')

    assert '<urlset' in resp.text
    assert 'http://www.sitemaps.org/schemas/sitemap/0.9' in resp.text


def test_sitemap_includes_homepage_url(app):
    resp = app.get('/sitemap.xml')

    # The homepage entry should contain loc pointing to the root path
    assert '<loc>' in resp.text
    assert '/</loc>' in resp.text


def test_sitemap_includes_dataset_url(app):
    # This extension requires datasets to belong to the 'artesp' organization
    org = _artesp_org()
    dataset_name = _unique_name('meu-dataset-teste')
    factories.Dataset(name=dataset_name, owner_org=org['id'])

    resp = app.get('/sitemap.xml')

    assert dataset_name in resp.text


def test_sitemap_includes_organization_url(app):
    org_name = _unique_name('minha-org-teste')
    factories.Organization(name=org_name)

    resp = app.get('/sitemap.xml')

    assert org_name in resp.text


def test_sitemap_excludes_private_datasets(app):
    # This extension requires datasets to belong to the 'artesp' organization
    org = _artesp_org()
    dataset_name = _unique_name('dataset-privado')
    factories.Dataset(name=dataset_name, private=True, owner_org=org['id'])

    resp = app.get('/sitemap.xml')

    assert dataset_name not in resp.text
