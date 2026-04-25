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
    with pytest.raises(tk.Invalid):
        validators.artesp_boolean_validator("invalid", {})


class TestRatingOverallValidator:
    def test_accepts_int_in_range(self):
        for v in (1, 2, 3, 4, 5):
            assert validators.rating_overall_validator(v, {}) == v

    def test_accepts_numeric_string(self):
        assert validators.rating_overall_validator("3", {}) == 3

    def test_rejects_out_of_range(self):
        with pytest.raises(tk.Invalid):
            validators.rating_overall_validator(0, {})
        with pytest.raises(tk.Invalid):
            validators.rating_overall_validator(6, {})

    def test_rejects_non_integer(self):
        with pytest.raises(tk.Invalid):
            validators.rating_overall_validator("abc", {})
        with pytest.raises(tk.Invalid):
            validators.rating_overall_validator(3.5, {})

    def test_rejects_missing(self):
        with pytest.raises(tk.Invalid):
            validators.rating_overall_validator(None, {})
        with pytest.raises(tk.Invalid):
            validators.rating_overall_validator("", {})


class TestRatingCriteriaValidator:
    def test_accepts_full_dict_of_bools(self):
        criteria = {"links_work": True, "up_to_date": False, "well_structured": True}
        assert validators.rating_criteria_validator(criteria, {}) == criteria

    def test_accepts_json_string(self):
        result = validators.rating_criteria_validator(
            '{"links_work": true, "up_to_date": false, "well_structured": true}', {}
        )
        assert result == {
            "links_work": True,
            "up_to_date": False,
            "well_structured": True,
        }

    def test_accepts_empty_dict(self):
        assert validators.rating_criteria_validator({}, {}) == {}

    def test_coerces_truthy_strings(self):
        result = validators.rating_criteria_validator(
            {"links_work": "true", "up_to_date": "false", "well_structured": 1}, {}
        )
        assert result == {
            "links_work": True,
            "up_to_date": False,
            "well_structured": True,
        }

    def test_rejects_unknown_keys(self):
        with pytest.raises(tk.Invalid):
            validators.rating_criteria_validator({"unexpected": True}, {})

    def test_rejects_non_dict(self):
        with pytest.raises(tk.Invalid):
            validators.rating_criteria_validator("not a dict", {})
        with pytest.raises(tk.Invalid):
            validators.rating_criteria_validator(["links_work"], {})

    def test_rejects_non_boolean_values(self):
        with pytest.raises(tk.Invalid):
            validators.rating_criteria_validator({"links_work": "maybe"}, {})


class TestRatingCommentValidator:
    def test_strips_whitespace(self):
        assert validators.rating_comment_validator("  hello  ", {}) == "hello"

    def test_empty_becomes_none(self):
        assert validators.rating_comment_validator("", {}) is None
        assert validators.rating_comment_validator("   ", {}) is None
        assert validators.rating_comment_validator(None, {}) is None

    def test_internal_whitespace_preserved(self):
        assert validators.rating_comment_validator("a  b", {}) == "a  b"

    def test_rejects_oversize_comment(self):
        too_long = "x" * 5001
        with pytest.raises(tk.Invalid):
            validators.rating_comment_validator(too_long, {})

    def test_accepts_max_length(self):
        ok = "x" * 5000
        assert validators.rating_comment_validator(ok, {}) == ok

    def test_rejects_non_string(self):
        with pytest.raises(tk.Invalid):
            validators.rating_comment_validator(123, {})
