"""Tests for validators.py."""

import pytest

import ckan.plugins.toolkit as tk

from ckanext.artesp_theme.logic import validators


def test_artesp_theme_required_with_valid_value():
    assert validators.artesp_theme_required("value") == "value"


def test_artesp_theme_required_with_invalid_value():
    with pytest.raises(tk.Invalid):
        validators.artesp_theme_required(None)


def test_artesp_date_br_to_iso_empty_value():
    assert validators.artesp_date_br_to_iso("", {}) == ""
    assert validators.artesp_date_br_to_iso(None, {}) is None


def test_artesp_date_br_to_iso_valid_brazilian_date():
    assert validators.artesp_date_br_to_iso("15/03/2024", {}) == "2024-03-15"
    assert validators.artesp_date_br_to_iso("1/1/2024", {}) == "2024-01-01"
    assert validators.artesp_date_br_to_iso("31/12/2023", {}) == "2023-12-31"


def test_artesp_date_br_to_iso_already_iso_format():
    assert validators.artesp_date_br_to_iso("2024-03-15", {}) == "2024-03-15"


def test_artesp_date_br_to_iso_invalid_format():
    with pytest.raises(tk.Invalid):
        validators.artesp_date_br_to_iso("2024/03/15", {})

    with pytest.raises(tk.Invalid):
        validators.artesp_date_br_to_iso("15-03-2024", {})


def test_artesp_date_br_to_iso_invalid_date():
    with pytest.raises(tk.Invalid):
        validators.artesp_date_br_to_iso("32/01/2024", {})  # Invalid day

    with pytest.raises(tk.Invalid):
        validators.artesp_date_br_to_iso("15/13/2024", {})  # Invalid month


def test_artesp_date_iso_to_br_empty_value():
    assert validators.artesp_date_iso_to_br("", {}) == ""
    assert validators.artesp_date_iso_to_br(None, {}) is None


def test_artesp_date_iso_to_br_valid_iso_date():
    assert validators.artesp_date_iso_to_br("2024-03-15", {}) == "15/3/2024"
    assert validators.artesp_date_iso_to_br("2024-01-01", {}) == "1/1/2024"
    assert validators.artesp_date_iso_to_br("2023-12-31", {}) == "31/12/2023"


def test_artesp_date_iso_to_br_already_brazilian_format():
    assert validators.artesp_date_iso_to_br("15/3/2024", {}) == "15/3/2024"


def test_artesp_date_iso_to_br_invalid_format():
    assert validators.artesp_date_iso_to_br("invalid-date", {}) == "invalid-date"


def test_artesp_boolean_validator_empty_value():
    assert validators.artesp_boolean_validator("", {}) == ""
    assert validators.artesp_boolean_validator(None, {}) is None


def test_artesp_boolean_validator_already_boolean():
    assert validators.artesp_boolean_validator(True, {}) is True
    assert validators.artesp_boolean_validator(False, {}) is False


def test_artesp_boolean_validator_true_strings():
    assert validators.artesp_boolean_validator("true", {}) is True
    assert validators.artesp_boolean_validator("True", {}) is True
    assert validators.artesp_boolean_validator("1", {}) is True
    assert validators.artesp_boolean_validator("yes", {}) is True
    assert validators.artesp_boolean_validator("sim", {}) is True


def test_artesp_boolean_validator_false_strings():
    assert validators.artesp_boolean_validator("false", {}) is False
    assert validators.artesp_boolean_validator("False", {}) is False
    assert validators.artesp_boolean_validator("0", {}) is False
    assert validators.artesp_boolean_validator("no", {}) is False
    assert validators.artesp_boolean_validator("não", {}) is False
    assert validators.artesp_boolean_validator("nao", {}) is False


def test_artesp_boolean_validator_invalid_string():
    assert validators.artesp_boolean_validator("invalid", {}) == "invalid"
