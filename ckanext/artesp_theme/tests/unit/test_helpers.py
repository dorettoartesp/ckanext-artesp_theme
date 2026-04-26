"""Tests for helpers.py."""
from unittest.mock import MagicMock, patch

import pytest
from markupsafe import Markup

import ckan.plugins.toolkit as tk

import ckanext.artesp_theme.helpers as helpers


def test_artesp_theme_hello():
    assert helpers.artesp_theme_hello() == "Hello, artesp_theme!"


def test_get_dashboard_statistics_delegates_to_dashboard_module(monkeypatch):
    captured = {}

    def fake_get_dashboard_statistics(data_dict=None):
        captured["data_dict"] = dict(data_dict or {})
        return {"ok": True}

    monkeypatch.setattr(
        helpers.dashboard_statistics,
        "get_dashboard_statistics",
        fake_get_dashboard_statistics,
    )

    assert helpers.get_dashboard_statistics({"period": "6m"}) == {"ok": True}
    assert captured["data_dict"] == {"period": "6m"}


def test_clear_dashboard_statistics_cache_delegates_to_dashboard_module(monkeypatch):
    captured = {"called": False}

    def fake_clear():
        captured["called"] = True

    monkeypatch.setattr(
        helpers.dashboard_statistics,
        "clear_dashboard_statistics_cache",
        fake_clear,
    )

    helpers.clear_dashboard_statistics_cache()

    assert captured["called"] is True


# ---------------------------------------------------------------------------
# safe_html
# ---------------------------------------------------------------------------

class TestSafeHtml:
    def test_returns_falsy_unchanged(self):
        assert helpers.safe_html("") == ""
        assert helpers.safe_html(None) is None

    def test_plain_string_returned_as_is(self):
        result = helpers.safe_html("Hello world")
        assert result == "Hello world"

    def test_fixes_double_encoded_html(self):
        double_encoded = '&amp;lt;i class=&amp;quot;fa fa-star&amp;quot;&amp;gt;&amp;lt;/i&amp;gt;'
        result = helpers.safe_html(double_encoded)
        assert isinstance(result, Markup)
        assert '<i class=' in result

    def test_double_encoded_result_is_markup(self):
        double_encoded = '&amp;lt;i class=&amp;quot;fa fa-check&amp;quot;&amp;gt;&amp;lt;/i&amp;gt;'
        result = helpers.safe_html(double_encoded)
        assert isinstance(result, Markup)


# ---------------------------------------------------------------------------
# fix_fontawesome_icon
# ---------------------------------------------------------------------------

class TestFixFontawesomeIcon:
    def test_returns_markup_object(self):
        result = helpers.fix_fontawesome_icon("star")
        assert isinstance(result, Markup)

    def test_contains_correct_class(self):
        result = helpers.fix_fontawesome_icon("check")
        assert 'fa fa-check' in result

    def test_contains_html_tag(self):
        result = helpers.fix_fontawesome_icon("home")
        assert '<i' in result
        assert '</i>' in result


# ---------------------------------------------------------------------------
# get_package_count
# ---------------------------------------------------------------------------

class TestGetPackageCount:
    def setup_method(self):
        helpers._HELPERS_CACHE.clear()

    def test_returns_count_on_success(self, monkeypatch):
        monkeypatch.setattr(
            helpers.toolkit, "get_action",
            lambda name: (lambda ctx, dd: {"count": 42}),
        )
        assert helpers.get_package_count() == 42

    def test_returns_zero_on_exception(self, monkeypatch):
        def fail_action(name):
            def raise_err(ctx, dd):
                raise Exception("Search unavailable")
            return raise_err

        monkeypatch.setattr(helpers.toolkit, "get_action", fail_action)
        assert helpers.get_package_count() == 0


# ---------------------------------------------------------------------------
# get_resource_count
# ---------------------------------------------------------------------------

class TestGetResourceCount:
    def test_returns_resource_count(self, monkeypatch):
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.count.return_value = 3
        monkeypatch.setattr(helpers, "Session", mock_session)
        assert helpers.get_resource_count() == 3

    def test_returns_zero_on_exception(self, monkeypatch):
        mock_session = MagicMock()
        mock_session.query.side_effect = Exception("DB error")
        monkeypatch.setattr(helpers, "Session", mock_session)
        assert helpers.get_resource_count() == 0


# ---------------------------------------------------------------------------
# get_latest_datasets
# ---------------------------------------------------------------------------

class TestGetLatestDatasets:
    def test_returns_dataset_list(self, monkeypatch):
        fake_datasets = [{"id": "d1"}, {"id": "d2"}]
        monkeypatch.setattr(
            helpers.toolkit, "get_action",
            lambda name: (lambda ctx, dd: {"results": fake_datasets}),
        )
        result = helpers.get_latest_datasets(limit=2)
        assert result == fake_datasets

    def test_returns_empty_on_exception(self, monkeypatch):
        def fail(name):
            def raise_err(ctx, dd):
                raise Exception("Search unavailable")
            return raise_err

        monkeypatch.setattr(helpers.toolkit, "get_action", fail)
        assert helpers.get_latest_datasets() == []


# ---------------------------------------------------------------------------
# get_featured_datasets
# ---------------------------------------------------------------------------

class TestGetFeaturedDatasets:
    def setup_method(self):
        helpers._HELPERS_CACHE.clear()

    def test_returns_datasets(self, monkeypatch):
        fake = [{"id": "feat-1"}]
        monkeypatch.setattr(
            helpers.toolkit, "get_action",
            lambda name: (lambda ctx, dd: {"results": fake}),
        )
        assert helpers.get_featured_datasets() == fake

    def test_returns_empty_on_exception(self, monkeypatch):
        def fail(name):
            def raise_err(ctx, dd):
                raise Exception("Fail")
            return raise_err

        monkeypatch.setattr(helpers.toolkit, "get_action", fail)
        assert helpers.get_featured_datasets() == []


# ---------------------------------------------------------------------------
# get_organization_count
# ---------------------------------------------------------------------------

class TestGetOrganizationCount:
    def setup_method(self):
        helpers._HELPERS_CACHE.clear()

    def test_returns_count(self, monkeypatch):
        monkeypatch.setattr(
            helpers.toolkit, "get_action",
            lambda name: (lambda ctx, dd: ["org1", "org2", "org3"]),
        )
        assert helpers.get_organization_count() == 3

    def test_returns_zero_on_exception(self, monkeypatch):
        def fail(name):
            def raise_err(ctx, dd):
                raise Exception("Fail")
            return raise_err

        monkeypatch.setattr(helpers.toolkit, "get_action", fail)
        assert helpers.get_organization_count() == 0


# ---------------------------------------------------------------------------
# get_group_count
# ---------------------------------------------------------------------------

class TestGetGroupCount:
    def setup_method(self):
        helpers._HELPERS_CACHE.clear()

    def test_returns_count(self, monkeypatch):
        monkeypatch.setattr(
            helpers.toolkit, "get_action",
            lambda name: (lambda ctx, dd: ["g1", "g2"]),
        )
        assert helpers.get_group_count() == 2

    def test_returns_zero_on_exception(self, monkeypatch):
        def fail(name):
            def raise_err(ctx, dd):
                raise Exception("Fail")
            return raise_err

        monkeypatch.setattr(helpers.toolkit, "get_action", fail)
        assert helpers.get_group_count() == 0


# ---------------------------------------------------------------------------
# get_featured_groups
# ---------------------------------------------------------------------------

class TestGetFeaturedGroups:
    def setup_method(self):
        helpers._HELPERS_CACHE.clear()

    def test_returns_sorted_by_package_count(self, monkeypatch):
        fake_groups = [
            {"id": "g1", "name": "g1", "package_count": 5},
            {"id": "g2", "name": "g2", "package_count": 20},
            {"id": "g3", "name": "g3", "package_count": 1},
        ]
        monkeypatch.setattr(
            helpers.toolkit, "get_action",
            lambda name: (lambda ctx, dd: list(fake_groups)),
        )
        result = helpers.get_featured_groups(limit=3)
        assert result[0]["id"] == "g2"
        assert result[1]["id"] == "g1"
        assert result[2]["id"] == "g3"

    def test_respects_limit(self, monkeypatch):
        fake_groups = [
            {"id": "g1", "package_count": 5},
            {"id": "g2", "package_count": 20},
            {"id": "g3", "package_count": 1},
        ]
        monkeypatch.setattr(
            helpers.toolkit, "get_action",
            lambda name: (lambda ctx, dd: list(fake_groups)),
        )
        result = helpers.get_featured_groups(limit=2)
        assert len(result) == 2

    def test_returns_empty_on_object_not_found(self, monkeypatch):
        def fail(name):
            def raise_err(ctx, dd):
                raise helpers.toolkit.ObjectNotFound("No groups")
            return raise_err

        monkeypatch.setattr(helpers.toolkit, "get_action", fail)
        assert helpers.get_featured_groups() == []

    def test_returns_empty_on_general_exception(self, monkeypatch):
        def fail(name):
            def raise_err(ctx, dd):
                raise Exception("Unknown error")
            return raise_err

        monkeypatch.setattr(helpers.toolkit, "get_action", fail)
        assert helpers.get_featured_groups() == []


# ---------------------------------------------------------------------------
# artesp_ldap_enabled
# ---------------------------------------------------------------------------

class TestArtespLdapEnabled:
    def test_returns_true_when_ldap_uri_set(self, monkeypatch):
        monkeypatch.setattr(
            helpers.toolkit.config, "get",
            lambda key, default="": "ldap://ldap:389" if key == "ckanext.ldap.uri" else default,
        )
        assert helpers.artesp_ldap_enabled() is True

    def test_returns_false_when_ldap_uri_empty(self, monkeypatch):
        monkeypatch.setattr(
            helpers.toolkit.config, "get",
            lambda key, default="": "",
        )
        assert helpers.artesp_ldap_enabled() is False


# ---------------------------------------------------------------------------
# artesp_govbr_login_enabled
# ---------------------------------------------------------------------------

class TestArtespGovbrLoginEnabled:
    def test_returns_true_when_enabled_and_client_id_set(self, monkeypatch):
        def fake_get(key, default=""):
            if key == "ckanext.artesp.govbr.enabled":
                return "true"
            if key == "ckanext.artesp.govbr.client_id":
                return "my-client-id"
            return default

        monkeypatch.setattr(helpers.toolkit.config, "get", fake_get)
        monkeypatch.setattr(helpers.toolkit, "asbool", lambda v: v == "true")
        assert helpers.artesp_govbr_login_enabled() is True

    def test_returns_false_when_disabled(self, monkeypatch):
        def fake_get(key, default=""):
            if key == "ckanext.artesp.govbr.enabled":
                return "false"
            if key == "ckanext.artesp.govbr.client_id":
                return "my-client-id"
            return default

        monkeypatch.setattr(helpers.toolkit.config, "get", fake_get)
        monkeypatch.setattr(helpers.toolkit, "asbool", lambda v: v == "true")
        assert helpers.artesp_govbr_login_enabled() is False

    def test_returns_false_when_no_client_id(self, monkeypatch):
        def fake_get(key, default=""):
            if key == "ckanext.artesp.govbr.enabled":
                return "true"
            if key == "ckanext.artesp.govbr.client_id":
                return ""
            return default

        monkeypatch.setattr(helpers.toolkit.config, "get", fake_get)
        monkeypatch.setattr(helpers.toolkit, "asbool", lambda v: v == "true")
        assert helpers.artesp_govbr_login_enabled() is False


# ---------------------------------------------------------------------------
# get_artesp_organization
# ---------------------------------------------------------------------------

class TestGetArtespOrganization:
    def test_returns_none_when_org_not_found(self, monkeypatch):
        monkeypatch.setattr(helpers.auth_helpers, "get_artesp_org", lambda: None)
        assert helpers.get_artesp_organization() is None

    def test_returns_org_dict_when_found(self, monkeypatch):
        fake_org = MagicMock()
        fake_org.id = "org-id"
        fake_org.name = "artesp"
        fake_org.title = "ARTESP"
        monkeypatch.setattr(helpers.auth_helpers, "get_artesp_org", lambda: fake_org)
        monkeypatch.setattr(helpers.auth_helpers, "get_artesp_org_display_name", lambda: "ARTESP")

        result = helpers.get_artesp_organization()
        assert result is not None
        assert result["name"] == "artesp"
        assert result["id"] == "org-id"


# ---------------------------------------------------------------------------
# artesp_is_user_external
# ---------------------------------------------------------------------------

class TestArtespIsUserExternal:
    def test_returns_false_for_none(self):
        assert helpers.artesp_is_user_external(None) is False

    def test_returns_false_for_empty_dict(self):
        assert helpers.artesp_is_user_external({}) is False

    def test_returns_true_when_plugin_extras_present(self):
        user_dict = {
            "name": "extuser",
            "plugin_extras": {"artesp": {"user_type": "external"}},
        }
        assert helpers.artesp_is_user_external(user_dict) is True

    def test_returns_false_for_internal_user(self):
        user_dict = {
            "name": "intuser",
            "plugin_extras": {"artesp": {"user_type": "internal"}},
        }
        assert helpers.artesp_is_user_external(user_dict) is False

    def test_falls_back_to_model_when_plugin_extras_missing(self, monkeypatch):
        user_dict = {"name": "someuser", "id": "uid-123"}

        fake_user = MagicMock()
        fake_user.plugin_extras = {"artesp": {"user_type": "external"}}

        with patch("ckan.model.User.get", return_value=fake_user):
            result = helpers.artesp_is_user_external(user_dict)
        assert result is True

    def test_returns_false_when_model_lookup_raises(self, monkeypatch):
        user_dict = {"name": "erroruser", "id": "uid-error"}

        with patch("ckan.model.User.get", side_effect=Exception("DB error")):
            result = helpers.artesp_is_user_external(user_dict)
        assert result is False


# ---------------------------------------------------------------------------
# get_dataset_rating_summary
# ---------------------------------------------------------------------------

class TestGetDatasetRatingSummary:
    def test_returns_summary_on_success(self, monkeypatch):
        fake_summary = {"package_id": "pkg-1", "overall": {"count": 5}}
        monkeypatch.setattr(
            helpers.toolkit, "get_action",
            lambda name: (lambda ctx, dd: fake_summary),
        )
        result = helpers.get_dataset_rating_summary("pkg-1")
        assert result == fake_summary

    def test_returns_default_on_exception(self, monkeypatch):
        def fail(name):
            def raise_err(ctx, dd):
                raise Exception("Unavailable")
            return raise_err

        monkeypatch.setattr(helpers.toolkit, "get_action", fail)
        result = helpers.get_dataset_rating_summary("pkg-1")
        assert result["package_id"] == "pkg-1"
        assert result["overall"]["count"] == 0


# ---------------------------------------------------------------------------
# get_current_user_dataset_rating
# ---------------------------------------------------------------------------

class TestGetCurrentUserDatasetRating:
    def test_returns_none_when_not_authenticated(self, monkeypatch):
        fake_user = MagicMock()
        fake_user.is_authenticated = False

        with patch("ckan.common.current_user", fake_user):
            result = helpers.get_current_user_dataset_rating("pkg-1")
        assert result is None

    def test_returns_rating_when_authenticated(self, monkeypatch):
        fake_user = MagicMock()
        fake_user.is_authenticated = True
        fake_user.name = "testuser"

        fake_rating = {"package_id": "pkg-1", "overall_rating": 4}
        monkeypatch.setattr(
            helpers.toolkit, "get_action",
            lambda name: (lambda ctx, dd: fake_rating),
        )

        with patch("ckan.common.current_user", fake_user):
            result = helpers.get_current_user_dataset_rating("pkg-1")
        assert result == fake_rating

    def test_returns_none_on_exception(self, monkeypatch):
        fake_user = MagicMock()
        fake_user.is_authenticated = True
        fake_user.name = "testuser"

        def fail(name):
            def raise_err(ctx, dd):
                raise Exception("Not found")
            return raise_err

        monkeypatch.setattr(helpers.toolkit, "get_action", fail)

        with patch("ckan.common.current_user", fake_user):
            result = helpers.get_current_user_dataset_rating("pkg-1")
        assert result is None
