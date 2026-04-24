"""Tests for /sitemap.xml route."""
import pytest
import ckan.plugins.toolkit as tk


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.usefixtures("with_plugins", "clean_db"),
]


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
    from ckan.tests import factories
    # This extension requires datasets to belong to the 'artesp' organization
    org = factories.Organization(name='artesp')
    factories.Dataset(name='meu-dataset-teste', owner_org=org['id'])

    resp = app.get('/sitemap.xml')

    assert 'meu-dataset-teste' in resp.text


def test_sitemap_includes_organization_url(app):
    from ckan.tests import factories
    factories.Organization(name='minha-org-teste')

    resp = app.get('/sitemap.xml')

    assert 'minha-org-teste' in resp.text


def test_sitemap_excludes_private_datasets(app):
    from ckan.tests import factories
    # This extension requires datasets to belong to the 'artesp' organization
    org = factories.Organization(name='artesp')
    factories.Dataset(name='dataset-privado', private=True, owner_org=org['id'])

    resp = app.get('/sitemap.xml')

    assert 'dataset-privado' not in resp.text
