"""Tests for validators.py."""

import pytest

import ckan.plugins.toolkit as tk

from ckanext.artesp_theme.logic import validators


def test_artesp_theme_reauired_with_valid_value():
    assert validators.artesp_theme_required("value") == "value"


def test_artesp_theme_reauired_with_invalid_value():
    with pytest.raises(tk.Invalid):
        validators.artesp_theme_required(None)
