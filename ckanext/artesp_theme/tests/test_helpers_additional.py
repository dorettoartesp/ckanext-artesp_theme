"""Additional focused tests for helpers.py coverage gaps."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
import ckan.model as model
from ckan.tests import factories

import ckanext.artesp_theme.helpers as helpers


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.usefixtures("with_plugins", "clean_db"),
]


class TestGetLatestResources:
    def test_returns_latest_resources_with_dataset_context(self):
        org = factories.Organization(name="artesp")
        dataset = factories.Dataset(owner_org=org["id"])
        resource = factories.Resource(package_id=dataset["id"], name="latest-resource")

        results = helpers.get_latest_resources(limit=1)

        assert len(results) == 1
        assert results[0]["resource"].id == resource["id"]
        assert results[0]["dataset"]["id"] == dataset["id"]
        assert results[0]["parent_dataset_title"] == dataset["title"]

    def test_filters_latest_resources_by_dataset_id(self):
        org = factories.Organization(name="artesp")
        dataset = factories.Dataset(owner_org=org["id"])
        other_dataset = factories.Dataset(owner_org=org["id"])
        factories.Resource(package_id=dataset["id"], name="dataset-resource")
        factories.Resource(package_id=other_dataset["id"], name="other-resource")

        results = helpers.get_latest_resources(limit=10, dataset_id=dataset["id"])

        assert results
        assert all(item["resource"].package_id == dataset["id"] for item in results)

    def test_filters_latest_resources_by_org_id(self):
        artesp_org = factories.Organization(name="artesp")
        other_org = factories.Organization(name="other-org")
        dataset = factories.Dataset(owner_org=artesp_org["id"])
        other_package = model.Package(
            name="other-org-dataset",
            title="Other org dataset",
            owner_org=other_org["id"],
            state="active",
        )
        model.Session.add(other_package)
        model.Session.commit()

        factories.Resource(package_id=dataset["id"], name="artesp-resource")
        factories.Resource(package_id=other_package.id, name="other-resource")

        results = helpers.get_latest_resources(limit=10, org_id=artesp_org["id"])

        assert results
        assert all(item["resource"].package_id == dataset["id"] for item in results)

    def test_skips_resource_when_package_lookup_fails(self, monkeypatch):
        org = factories.Organization(name="artesp")
        dataset = factories.Dataset(owner_org=org["id"])
        factories.Resource(package_id=dataset["id"], name="broken-package-resource")

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
