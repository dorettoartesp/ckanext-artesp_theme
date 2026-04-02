"""Tests for auth.py."""

import ckan.model as model

from ckanext.artesp_theme.logic import auth as artesp_auth


def test_artesp_theme_get_sum():
    assert artesp_auth.artesp_theme_get_sum({"model": model}, {})["success"]
