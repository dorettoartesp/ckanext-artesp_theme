"""Tests for SEO helpers."""
from unittest.mock import MagicMock, patch

import pytest

import ckanext.artesp_theme.helpers as helpers


def test_seo_canonical_url_returns_base_url_without_query(monkeypatch):
    mock_request = MagicMock()
    mock_request.base_url = 'http://dados.artesp.sp.gov.br/dataset/test'
    monkeypatch.setattr('ckanext.artesp_theme.helpers.flask_request', mock_request)

    result = helpers.seo_canonical_url()

    assert result == 'http://dados.artesp.sp.gov.br/dataset/test'


def test_seo_canonical_url_no_trailing_slash(monkeypatch):
    mock_request = MagicMock()
    mock_request.base_url = 'http://dados.artesp.sp.gov.br/'
    monkeypatch.setattr('ckanext.artesp_theme.helpers.flask_request', mock_request)

    result = helpers.seo_canonical_url()

    assert result == 'http://dados.artesp.sp.gov.br/'
