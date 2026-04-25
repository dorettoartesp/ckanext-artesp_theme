from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest

import ckanext.artesp_theme.helpers as helpers


class TestGetLatestResources:
    pytestmark = [
        pytest.mark.app,
        pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
        pytest.mark.usefixtures("with_plugins"),
    ]

    class _FakeQuery:
        def __init__(self, resources):
            self._resources = list(resources)
            self._dataset_id = None
            self._org_id = None
            self._limit = None

        def autoflush(self, *args, **kwargs):
            return self

        def filter(self, condition):
            left = getattr(condition, "left", None)
            right = getattr(condition, "right", None)
            key = getattr(left, "key", None)
            value = getattr(right, "value", None)

            if key == "state" and value == "active":
                return self
            if key == "package_id":
                self._dataset_id = value
                return self
            if key == "owner_org":
                self._org_id = value
                return self
            return self

        def join(self, *args, **kwargs):
            return self

        def order_by(self, *args, **kwargs):
            return self

        def limit(self, limit_value):
            self._limit = limit_value
            return self

        def first(self):
            resources = self.all()
            return resources[0] if resources else None

        def one_or_none(self):
            resources = self.all()
            return resources[0] if resources else None

        def delete(self, *args, **kwargs):
            return 0

        def all(self):
            resources = list(self._resources)
            if self._dataset_id is not None:
                resources = [r for r in resources if r.package_id == self._dataset_id]
            if self._org_id is not None:
                resources = [r for r in resources if r.owner_org == self._org_id]
            resources.sort(key=lambda resource: resource.metadata_modified, reverse=True)
            if self._limit is not None:
                return resources[: self._limit]
            return resources

    def _resource(self, package_id, resource_id, metadata_modified, owner_org=None):
        return SimpleNamespace(
            id=resource_id,
            package_id=package_id,
            owner_org=owner_org,
            metadata_modified=metadata_modified,
        )

    def _patch_package_show(self, monkeypatch, package_dicts):
        def fake_get_action(name):
            assert name == "package_show"
            return lambda context, data_dict: package_dicts[data_dict["id"]]

        monkeypatch.setattr(helpers.toolkit, "get_action", fake_get_action)

    def test_returns_latest_resources_with_dataset_context(self, monkeypatch):
        dataset = SimpleNamespace(id="pkg-1", title="Dataset title", name="dataset-1")
        resource = self._resource("pkg-1", "res-1", datetime(2026, 4, 25, 0, 0, 0))
        self._patch_package_show(
            monkeypatch,
            {"pkg-1": {"id": "pkg-1", "title": dataset.title, "name": dataset.name}},
        )

        with patch.object(helpers.Session, "query", return_value=self._FakeQuery([resource])):
            results = helpers.get_latest_resources(limit=1)

        assert len(results) == 1
        assert results[0]["resource"].id == resource.id
        assert results[0]["dataset"]["id"] == dataset.id
        assert results[0]["parent_dataset_title"] == dataset.title

    def test_filters_latest_resources_by_dataset_id(self, monkeypatch):
        resource = self._resource("pkg-1", "res-1", datetime(2026, 4, 25, 0, 0, 0))
        other_resource = self._resource("pkg-2", "res-2", datetime(2026, 4, 25, 0, 0, 1))
        self._patch_package_show(
            monkeypatch,
            {
                "pkg-1": {"id": "pkg-1", "title": "Dataset 1", "name": "dataset-1"},
                "pkg-2": {"id": "pkg-2", "title": "Dataset 2", "name": "dataset-2"},
            },
        )

        with patch.object(
            helpers.Session, "query", return_value=self._FakeQuery([resource, other_resource])
        ):
            results = helpers.get_latest_resources(limit=10, dataset_id="pkg-1")

        assert results
        assert all(item["resource"].package_id == "pkg-1" for item in results)

    def test_filters_latest_resources_by_org_id(self, monkeypatch):
        resource = self._resource(
            "pkg-1", "res-1", datetime(2026, 4, 25, 0, 0, 0), owner_org="artesp-org"
        )
        other_resource = self._resource(
            "pkg-2", "res-2", datetime(2026, 4, 25, 0, 0, 1), owner_org="other-org"
        )
        self._patch_package_show(
            monkeypatch,
            {
                "pkg-1": {
                    "id": "pkg-1",
                    "title": "Dataset 1",
                    "name": "dataset-1",
                    "groups": [],
                },
                "pkg-2": {
                    "id": "pkg-2",
                    "title": "Dataset 2",
                    "name": "dataset-2",
                    "groups": [],
                },
            },
        )

        with patch.object(
            helpers.Session, "query", return_value=self._FakeQuery([resource, other_resource])
        ):
            results = helpers.get_latest_resources(limit=10, org_id="artesp-org")

        assert results
        assert all(item["resource"].package_id == "pkg-1" for item in results)

    def test_skips_resource_when_package_lookup_fails(self, monkeypatch):
        resource = self._resource("pkg-1", "res-1", datetime(2026, 4, 25, 0, 0, 0))
        with patch.object(
            helpers.Session, "query", return_value=self._FakeQuery([resource])
        ), patch.object(
            helpers.toolkit,
            "get_action",
            lambda name: (
                lambda context, data_dict: (_ for _ in ()).throw(Exception("boom"))
            ),
        ):
            assert helpers.get_latest_resources(limit=5) == []

    def test_returns_empty_when_query_raises(self):
        with patch.object(helpers.Session, "query", side_effect=Exception("database down")):
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
