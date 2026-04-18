"""TDD: is_external_user helper."""
from unittest.mock import MagicMock, patch

import pytest

from ckanext.artesp_theme.logic.auth_helpers import is_external_user


def _make_user(user_type=None, name="testuser"):
    u = MagicMock()
    u.name = name
    u.id = "uid-123"
    if user_type is None:
        u.plugin_extras = {}
    else:
        u.plugin_extras = {"artesp": {"user_type": user_type}}
    return u


class TestIsExternalUser:
    def test_returns_true_for_external_user_type(self):
        user = _make_user(user_type="external")
        with patch("ckanext.artesp_theme.logic.auth_helpers.model.User.get", return_value=user):
            assert is_external_user("testuser") is True

    def test_returns_false_for_internal_user_type(self):
        user = _make_user(user_type="internal")
        with patch("ckanext.artesp_theme.logic.auth_helpers.model.User.get", return_value=user):
            assert is_external_user("testuser") is False

    def test_returns_false_when_plugin_extras_empty(self):
        user = _make_user(user_type=None)
        with patch("ckanext.artesp_theme.logic.auth_helpers.model.User.get", return_value=user):
            assert is_external_user("testuser") is False

    def test_returns_false_when_user_not_found(self):
        with patch("ckanext.artesp_theme.logic.auth_helpers.model.User.get", return_value=None):
            assert is_external_user("noone") is False

    def test_accepts_user_object_directly(self):
        user = _make_user(user_type="external")
        assert is_external_user(user) is True

    def test_accepts_internal_user_object_directly(self):
        user = _make_user(user_type="internal")
        assert is_external_user(user) is False

    def test_returns_false_for_none(self):
        assert is_external_user(None) is False
