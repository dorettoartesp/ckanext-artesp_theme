"""Unit tests for public helper wrapper functions."""

from types import SimpleNamespace
from unittest.mock import patch

import ckanext.artesp_theme.helpers as helpers


class TestHelperWrappers:
    def test_get_default_dataset_collaborator_capacity_delegates(self, monkeypatch):
        monkeypatch.setattr(
            helpers.auth_helpers,
            "get_default_dataset_collaborator_capacity",
            lambda: "member",
        )

        assert helpers.get_default_dataset_collaborator_capacity() == "member"

    def test_artesp_is_external_user_delegates(self, monkeypatch):
        monkeypatch.setattr(helpers.auth_helpers, "is_external_user", lambda user: True)

        with patch.object(helpers.toolkit, "c", SimpleNamespace(userobj=SimpleNamespace())):
            assert helpers.artesp_is_external_user() is True

    def test_artesp_is_external_user_falls_back_to_db_user(self, monkeypatch):
        monkeypatch.setattr(
            helpers.auth_helpers,
            "is_external_user",
            lambda user: user
            and getattr(user, "plugin_extras", {})
            .get("artesp", {})
            .get("user_type")
            == "external",
        )

        db_user = SimpleNamespace(
            name="govbr_user",
            plugin_extras={"artesp": {"user_type": "external"}},
        )

        with patch.object(
            helpers.toolkit,
            "c",
            SimpleNamespace(user="govbr_user", userobj=SimpleNamespace(name="govbr_user")),
        ), patch("ckan.model.User.get", return_value=db_user) as mock_user_get:
            assert helpers.artesp_is_external_user() is True
            mock_user_get.assert_called_once_with("govbr_user")

    def test_artesp_auth_provider_reads_session_marker(self):
        with patch.object(helpers, "ckan_session", {"artesp_auth_provider": "govbr"}):
            assert helpers.artesp_auth_provider() == "govbr"

    def test_artesp_auth_provider_returns_none_when_missing(self):
        with patch.object(helpers, "ckan_session", {}):
            assert helpers.artesp_auth_provider() is None

    def test_rating_comment_captcha_helpers_follow_config(self):
        with patch.object(
            helpers.toolkit,
            "config",
            {helpers.RATING_COMMENT_ALTCHA_CONFIG_KEY: "rating-secret"},
        ), patch.object(
            helpers.toolkit,
            "url_for",
            lambda endpoint: "/dataset-rating/comment-captcha/challenge",
        ):
            assert helpers.rating_comment_captcha_enabled() is True
            assert (
                helpers.get_rating_comment_captcha_challenge_url()
                == "/dataset-rating/comment-captcha/challenge"
            )
            assert (
                helpers.get_rating_comment_captcha_script_url()
                == helpers.RATING_COMMENT_ALTCHA_SCRIPT_URL
            )
            assert (
                helpers.get_rating_comment_captcha_stylesheet_url()
                == helpers.RATING_COMMENT_ALTCHA_STYLESHEET_URL
            )

    def test_rating_comment_captcha_challenge_url_returns_none_without_secret(self):
        with patch.object(helpers.toolkit, "config", {}):
            assert helpers.rating_comment_captcha_enabled() is False
            assert helpers.get_rating_comment_captcha_challenge_url() is None

    def test_get_helpers_exposes_artesp_theme_specific_wrappers(self):
        helper_dict = helpers.get_helpers()

        assert helper_dict["get_latest_resources"] is helpers.get_latest_resources
        assert helper_dict["artesp_is_external_user"] is helpers.artesp_is_external_user
        assert (
            helper_dict["rating_comment_captcha_enabled"]
            is helpers.rating_comment_captcha_enabled
        )
        assert (
            helper_dict["get_rating_comment_captcha_script_url"]
            is helpers.get_rating_comment_captcha_script_url
        )
