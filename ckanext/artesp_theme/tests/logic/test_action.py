"""Tests for action.py."""

from ckanext.artesp_theme.logic import action as artesp_action


def test_artesp_theme_get_sum():
    result = artesp_action.artesp_theme_get_sum(
        {"ignore_auth": True},
        {"left": 10, "right": 30},
    )
    assert result["sum"] == 40
