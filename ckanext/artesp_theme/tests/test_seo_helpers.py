"""Tests for SEO helpers."""
from unittest.mock import MagicMock

import pytest

import ckanext.artesp_theme.helpers as helpers


def test_seo_canonical_url_returns_base_url_without_query(monkeypatch):
    mock_request = MagicMock()
    mock_request.base_url = 'http://dados.artesp.sp.gov.br/dataset/test'
    monkeypatch.setattr('ckanext.artesp_theme.helpers.flask_request', mock_request)

    result = helpers.seo_canonical_url()

    assert result == 'http://dados.artesp.sp.gov.br/dataset/test'


def test_seo_canonical_url_returns_root_url_as_is(monkeypatch):
    mock_request = MagicMock()
    mock_request.base_url = 'http://dados.artesp.sp.gov.br/'
    monkeypatch.setattr('ckanext.artesp_theme.helpers.flask_request', mock_request)

    result = helpers.seo_canonical_url()

    assert result == 'http://dados.artesp.sp.gov.br/'


def test_seo_meta_description_extracts_from_pkg_notes(monkeypatch):
    pkg = {
        'notes': 'Dados de **pedágio** no estado de São Paulo.',
        'notes_translated': {},
    }
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.h.get_translated',
        lambda d, f: d.get(f, ''),
    )
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.h.markdown_extract',
        lambda text, extract_length=155: text.replace('**', ''),
    )

    result = helpers.seo_meta_description(pkg_dict=pkg)

    assert 'pedágio' in result
    assert '**' not in result


def test_seo_meta_description_extracts_from_org_description(monkeypatch):
    org = {'description': 'Órgão regulador de transporte.', 'description_translated': {}}
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.h.get_translated',
        lambda d, f: d.get(f, ''),
    )
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.h.markdown_extract',
        lambda text, extract_length=155: text,
    )

    result = helpers.seo_meta_description(org_dict=org)

    assert 'regulador' in result


def test_seo_meta_description_extracts_from_group_description(monkeypatch):
    group = {'description': 'Grupo de dados ambientais.', 'description_translated': {}}
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.h.get_translated',
        lambda d, f: d.get(f, ''),
    )
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.h.markdown_extract',
        lambda text, extract_length=155: text,
    )

    result = helpers.seo_meta_description(group_dict=group)

    assert 'ambientais' in result


def test_seo_meta_description_falls_back_to_site_description(monkeypatch):
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.config.get',
        lambda key, default='': 'Portal de Dados Abertos ARTESP' if key == 'ckan.site_description' else default,
    )
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.h.markdown_extract',
        lambda text, extract_length=155: text,
    )

    result = helpers.seo_meta_description()

    assert 'ARTESP' in result


def test_seo_meta_description_returns_empty_when_no_data(monkeypatch):
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.config.get',
        lambda key, default='': default,
    )
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.h.markdown_extract',
        lambda text, extract_length=155: text,
    )

    result = helpers.seo_meta_description()

    assert result == ''


def test_seo_meta_description_guards_against_none_from_get_translated(monkeypatch):
    pkg = {'notes': None, 'notes_translated': {}}
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.h.get_translated',
        lambda d, f: None,
    )
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.h.markdown_extract',
        lambda text, extract_length=155: text,
    )

    result = helpers.seo_meta_description(pkg_dict=pkg)

    assert result == ''


def test_seo_meta_description_forwards_custom_length(monkeypatch):
    captured = {}
    pkg = {'notes': 'texto longo', 'notes_translated': {}}
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.h.get_translated',
        lambda d, f: d.get(f, ''),
    )
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.h.markdown_extract',
        lambda text, extract_length=155: captured.update({'extract_length': extract_length}) or text,
    )

    helpers.seo_meta_description(pkg_dict=pkg, length=50)

    assert captured['extract_length'] == 50


def _make_pkg():
    return {
        'name': 'tarifas-pedagio-2024',
        'title': 'Tarifas de Pedágio 2024',
        'title_translated': {},
        'notes': 'Dados sobre tarifas de pedágio.',
        'notes_translated': {},
        'tags': [{'name': 'pedágio'}, {'name': 'transporte'}],
        'license_url': 'https://creativecommons.org/licenses/by/4.0/',
        'license_title': 'CC BY 4.0',
        'organization': {'name': 'artesp', 'title': 'ARTESP'},
        'metadata_created': '2024-01-15T10:00:00',
        'metadata_modified': '2024-06-01T12:00:00',
        'resources': [
            {
                'id': 'res-1',
                'name': 'Tabela CSV',
                'url': 'https://dados.artesp.sp.gov.br/dataset/tarifas/resource/res-1',
                'mimetype': 'text/csv',
                'format': 'CSV',
            }
        ],
    }


def test_seo_jsonld_dataset_has_required_schema_fields(monkeypatch):
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.config.get',
        lambda key, default='': 'https://dados.artesp.sp.gov.br' if key == 'ckan.site_url' else default,
    )
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.url_for',
        lambda route, **kw: f"/dataset/{kw.get('id', '')}",
    )
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.h.get_translated',
        lambda d, f: d.get(f, ''),
    )
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.h.markdown_extract',
        lambda text, extract_length=500: text,
    )

    result = helpers.seo_jsonld_dataset(_make_pkg())

    assert result['@context'] == 'https://schema.org'
    assert result['@type'] == 'Dataset'
    assert result['name'] == 'Tarifas de Pedágio 2024'
    assert result['description'] == 'Dados sobre tarifas de pedágio.'
    assert result['url'] == 'https://dados.artesp.sp.gov.br/dataset/tarifas-pedagio-2024'
    assert 'pedágio' in result['keywords']
    assert 'transporte' in result['keywords']
    assert result['license'] == 'https://creativecommons.org/licenses/by/4.0/'
    assert result['datePublished'] == '2024-01-15'
    assert result['dateModified'] == '2024-06-01'


def test_seo_jsonld_dataset_has_creator_from_organization(monkeypatch):
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.config.get',
        lambda key, default='': 'https://dados.artesp.sp.gov.br' if key == 'ckan.site_url' else default,
    )
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.url_for',
        lambda route, **kw: f"/dataset/{kw.get('id', '')}",
    )
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.h.get_translated',
        lambda d, f: d.get(f, ''),
    )
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.h.markdown_extract',
        lambda text, extract_length=500: text,
    )

    result = helpers.seo_jsonld_dataset(_make_pkg())

    assert result['creator']['@type'] == 'Organization'
    assert result['creator']['name'] == 'ARTESP'


def test_seo_jsonld_dataset_has_distribution(monkeypatch):
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.config.get',
        lambda key, default='': 'https://dados.artesp.sp.gov.br' if key == 'ckan.site_url' else default,
    )
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.url_for',
        lambda route, **kw: f"/dataset/{kw.get('id', '')}",
    )
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.h.get_translated',
        lambda d, f: d.get(f, ''),
    )
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.h.markdown_extract',
        lambda text, extract_length=500: text,
    )

    result = helpers.seo_jsonld_dataset(_make_pkg())

    assert len(result['distribution']) == 1
    dist = result['distribution'][0]
    assert dist['@type'] == 'DataDownload'
    assert dist['encodingFormat'] == 'text/csv'
    assert 'res-1' in dist['contentUrl']


def test_seo_jsonld_dataset_uses_license_title_as_fallback(monkeypatch):
    pkg = _make_pkg()
    pkg['license_url'] = ''
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.config.get',
        lambda key, default='': 'https://dados.artesp.sp.gov.br' if key == 'ckan.site_url' else default,
    )
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.url_for',
        lambda route, **kw: f"/dataset/{kw.get('id', '')}",
    )
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.h.get_translated',
        lambda d, f: d.get(f, ''),
    )
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.h.markdown_extract',
        lambda text, extract_length=500: text,
    )

    result = helpers.seo_jsonld_dataset(pkg)

    assert result['license'] == 'CC BY 4.0'


def test_seo_jsonld_organization_has_required_fields(monkeypatch):
    org = {
        'name': 'artesp',
        'title': 'ARTESP',
        'display_name': 'ARTESP',
        'description': 'Agência de Transporte do Estado de São Paulo.',
        'description_translated': {},
    }
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.config.get',
        lambda key, default='': 'https://dados.artesp.sp.gov.br' if key == 'ckan.site_url' else default,
    )
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.url_for',
        lambda route, **kw: f"/organization/{kw.get('id', '')}",
    )
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.h.get_translated',
        lambda d, f: d.get(f, ''),
    )
    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.h.markdown_extract',
        lambda text, extract_length=300: text,
    )

    result = helpers.seo_jsonld_organization(org)

    assert result['@context'] == 'https://schema.org'
    assert result['@type'] == 'GovernmentOrganization'
    assert result['name'] == 'ARTESP'
    assert result['description'] == 'Agência de Transporte do Estado de São Paulo.'
    assert result['url'] == 'https://dados.artesp.sp.gov.br/organization/artesp'


def test_seo_jsonld_site_has_required_fields(monkeypatch):
    def fake_config_get(key, default=''):
        return {
            'ckan.site_url': 'https://dados.artesp.sp.gov.br',
            'ckan.site_title': 'Dados Abertos ARTESP',
            'ckan.site_description': 'Portal de dados da ARTESP.',
        }.get(key, default)

    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.config.get',
        fake_config_get,
    )

    result = helpers.seo_jsonld_site()

    assert result['@context'] == 'https://schema.org'
    assert result['@type'] == 'GovernmentOrganization'
    assert result['name'] == 'Dados Abertos ARTESP'
    assert result['url'] == 'https://dados.artesp.sp.gov.br'
    assert result['description'] == 'Portal de dados da ARTESP.'


def test_seo_jsonld_site_omits_description_when_empty(monkeypatch):
    def fake_config_get(key, default=''):
        return {
            'ckan.site_url': 'https://dados.artesp.sp.gov.br',
            'ckan.site_title': 'Dados Abertos ARTESP',
            'ckan.site_description': '',
        }.get(key, default)

    monkeypatch.setattr(
        'ckanext.artesp_theme.helpers.toolkit.config.get',
        fake_config_get,
    )

    result = helpers.seo_jsonld_site()

    assert 'description' not in result
