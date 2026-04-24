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
