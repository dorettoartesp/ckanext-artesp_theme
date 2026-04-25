"""Additional focused tests for helpers.py coverage gaps."""

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch
import uuid

import pytest
import ckan.model as model
from ckan.tests import factories

import ckanext.artesp_theme.helpers as helpers


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.usefixtures("with_plugins"),
]


class TestGetLatestResources:
    def _package(self, title="Dataset", owner_org="artesp"):
        package = model.Package(
            name="dataset-{}".format(uuid.uuid4().hex[:8]),
            title=title,
            owner_org=owner_org,
            state="active",
        )
        model.Session.add(package)
        model.Session.commit()
        return package

    def _resource(self, package, name, seconds=0):
        resource = model.Resource(
            package_id=package.id,
            name=name,
            url="https://example.com/{}.csv".format(uuid.uuid4().hex[:8]),
            metadata_modified=datetime.utcnow() + timedelta(seconds=seconds),
        )
        resource.state = "active"
        model.Session.add(resource)
        model.Session.commit()
        return resource

    def _patch_package_show(self, monkeypatch, *packages):
        package_dicts = {
            package.id: {"id": package.id, "title": package.title, "name": package.name}
            for package in packages
        }

        def fake_get_action(name):
            assert name == "package_show"
            return lambda context, data_dict: package_dicts[data_dict["id"]]

        monkeypatch.setattr(helpers.toolkit, "get_action", fake_get_action)

    def test_returns_latest_resources_with_dataset_context(self, monkeypatch):
        dataset = self._package(title="Dataset title")
        resource = self._resource(dataset, "latest-resource", seconds=86400)
        self._patch_package_show(monkeypatch, dataset)

        results = helpers.get_latest_resources(limit=1)

        assert len(results) == 1
        assert results[0]["resource"].id == resource.id
        assert results[0]["dataset"]["id"] == dataset.id
        assert results[0]["parent_dataset_title"] == dataset.title

    def test_filters_latest_resources_by_dataset_id(self, monkeypatch):
        dataset = self._package()
        other_dataset = self._package()
        self._resource(dataset, "dataset-resource")
        self._resource(other_dataset, "other-resource", seconds=1)
        self._patch_package_show(monkeypatch, dataset, other_dataset)

        results = helpers.get_latest_resources(limit=10, dataset_id=dataset.id)

        assert results
        assert all(item["resource"].package_id == dataset.id for item in results)

    def test_filters_latest_resources_by_org_id(self, monkeypatch):
        artesp_org_id = "artesp-org"
        dataset = self._package(owner_org=artesp_org_id)
        other_package = self._package(title="Other org dataset", owner_org="other-org")

        self._resource(dataset, "artesp-resource")
        self._resource(other_package, "other-resource", seconds=1)
        self._patch_package_show(monkeypatch, dataset, other_package)

        results = helpers.get_latest_resources(limit=10, org_id=artesp_org_id)

        assert results
        assert all(item["resource"].package_id == dataset.id for item in results)

    def test_skips_resource_when_package_lookup_fails(self, monkeypatch):
        dataset = self._package()
        self._resource(dataset, "broken-package-resource")

        monkeypatch.setattr(
            helpers.toolkit,
            "get_action",
            lambda name: (
                lambda context, data_dict: (_ for _ in ()).throw(Exception("boom"))
            ),
        )

        assert helpers.get_latest_resources(limit=5) == []

    def test_returns_empty_when_query_raises(self):
        with patch(
            "ckanext.artesp_theme.helpers.Session.query",
            side_effect=Exception("database down"),
        ):
            assert helpers.get_latest_resources(limit=5) == []


class TestAdditionalHelperWrappers:
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
        monkeypatch.setattr(helpers.auth_helpers, "is_external_user", lambda user: user and getattr(user, "plugin_extras", {}).get("artesp", {}).get("user_type") == "external")

        db_user = SimpleNamespace(name="govbr_user", plugin_extras={"artesp": {"user_type": "external"}})

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
