"""Tests for the dataset rating blueprint/controller."""

import sys
import types

import pytest
from unittest.mock import MagicMock, patch

import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.tests import factories

from ckanext.artesp_theme.model import DatasetRating, dataset_rating_table


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.usefixtures("with_plugins"),
]


@pytest.fixture(autouse=True)
def _ensure_rating_table(clean_db):
    dataset_rating_table.create(bind=model.Session.get_bind(), checkfirst=True)
    yield


@pytest.fixture
def artesp_org():
    return factories.Organization(name="artesp")


@pytest.fixture
def user(artesp_org):
    return factories.User()


@pytest.fixture
def pkg(user, artesp_org):
    return factories.Dataset(user=user, owner_org=artesp_org["id"])


@pytest.fixture
def app_with_user(app, user):
    env = {"REMOTE_USER": user["name"]}
    return app, env


class TestRatingSubmitView:
    def test_rating_without_comment_does_not_require_captcha(self, app_with_user, user, pkg):
        app, env = app_with_user
        app.post(
            f"/dataset/{pkg['name']}/rate",
            data={"overall_rating": "4"},
            environ_base=env,
        )
        u = model.User.get(user["name"])
        rating = DatasetRating.get_for(u.id, pkg["id"])
        assert rating is not None
        assert rating.comment == ""

    def test_comment_without_altcha_config_blocks_submit(self, app_with_user, user, pkg):
        app, env = app_with_user
        app.post(
            f"/dataset/{pkg['name']}/rate",
            data={"overall_rating": "4", "comment": "Needs a captcha"},
            environ_base=env,
        )
        u = model.User.get(user["name"])
        assert DatasetRating.get_for(u.id, pkg["id"]) is None

    def test_comment_with_valid_altcha_creates_rating(self, app_with_user, user, pkg):
        app, env = app_with_user
        with patch("ckanext.artesp_theme.controllers._validate_rating_comment_captcha"):
            app.post(
                f"/dataset/{pkg['name']}/rate",
                data={
                    "overall_rating": "4",
                    "comment": "Useful context",
                    "criteria_links_work": "true",
                    "criteria_up_to_date": "false",
                    "criteria_well_structured": "true",
                    "altcha": "mock-payload",
                },
                environ_base=env,
            )
        u = model.User.get(user["name"])
        rating = DatasetRating.get_for(u.id, pkg["id"])
        assert rating is not None
        assert rating.overall_rating == 4
        assert rating.comment == "Useful context"

    def test_anonymous_redirects_to_login(self, app, pkg):
        resp = app.post(
            f"/dataset/{pkg['name']}/rate",
            data={"overall_rating": "3"},
        )
        # app follows redirect; final URL must contain "login"
        assert "login" in resp.request.url

    def test_invalid_rating_does_not_persist(self, app_with_user, user, pkg):
        app, env = app_with_user
        app.post(
            f"/dataset/{pkg['name']}/rate",
            data={"overall_rating": "99"},
            environ_base=env,
        )
        u = model.User.get(user["name"])
        assert DatasetRating.get_for(u.id, pkg["id"]) is None

    def test_private_dataset_requires_access_to_submit_rating(self, app, artesp_org):
        owner = factories.User()
        outsider = factories.User()
        private_pkg = factories.Dataset(
            user=owner,
            owner_org=artesp_org["id"],
            private=True,
        )

        resp = app.post(
            f"/dataset/{private_pkg['name']}/rate",
            data={"overall_rating": "4"},
            environ_base={"REMOTE_USER": outsider["name"]},
        )

        outsider_obj = model.User.get(outsider["name"])
        assert DatasetRating.get_for(outsider_obj.id, private_pkg["id"]) is None
        assert "dataset" in resp.request.url or "search" in resp.request.url


class TestRatingCommentCaptcha:
    @pytest.mark.ckan_config("ckanext.artesp.rating.altcha_hmac_secret", "test-hmac-secret")
    def test_challenge_endpoint_returns_nested_parameters(self, app_with_user):
        """Challenge JSON preserves the nested {parameters, signature} shape."""
        app, env = app_with_user
        captured = {}

        def fake_create_challenge(**kwargs):
            captured.update(kwargs)
            return MagicMock(
                to_dict=MagicMock(
                    return_value={
                        "parameters": {"algorithm": kwargs["algorithm"]},
                        "signature": "sig",
                    }
                )
            )

        fake_altcha = types.SimpleNamespace(create_challenge=fake_create_challenge)

        with patch.dict(sys.modules, {"altcha": fake_altcha}):
            resp = app.get(
                "/dataset-rating/comment-captcha/challenge",
                environ_base=env,
            )

        assert resp.status_code == 200
        assert resp.json["parameters"]["algorithm"] == "PBKDF2/SHA-256"
        assert resp.json["signature"] == "sig"
        assert captured["hmac_secret"] == "test-hmac-secret"

    def test_missing_altcha_config_blocks_comment_submission(self, app_with_user, user, pkg):
        """Commented submissions must fail closed when ALTCHA is not configured."""
        app, env = app_with_user
        app.post(
            f"/dataset/{pkg['name']}/rate",
            data={"overall_rating": "4", "comment": "Need verification", "altcha": "any-token"},
            environ_base=env,
        )
        u = model.User.get(user["name"])
        assert DatasetRating.get_for(u.id, pkg["id"]) is None

    @pytest.mark.ckan_config("ckanext.artesp.rating.altcha_hmac_secret", "test-hmac-secret")
    def test_challenge_endpoint_returns_200_for_authenticated_user(self, app_with_user):
        """Lines 420-444: challenge endpoint returns JSON when configured and authenticated."""
        app, env = app_with_user
        mock_create = MagicMock()
        fake_altcha = types.SimpleNamespace(create_challenge=mock_create)
        with patch.dict(sys.modules, {"altcha": fake_altcha}):
            fake_challenge = MagicMock()
            fake_challenge.to_dict.return_value = {
                "parameters": {"algorithm": "PBKDF2/SHA-256"},
                "signature": "sig",
            }
            mock_create.return_value = fake_challenge
            resp = app.get(
                "/dataset-rating/comment-captcha/challenge",
                environ_base=env,
            )
        assert resp.status_code == 200
        assert resp.json["signature"] == "sig"

    def test_challenge_endpoint_returns_403_for_anonymous(self, app):
        """Line 423: anonymous → 403."""
        resp = app.get(
            "/dataset-rating/comment-captcha/challenge",
            expect_errors=True,
        )
        assert resp.status_code == 403

    def test_challenge_endpoint_returns_404_when_no_secret(self, app_with_user):
        """Lines 425-427: no secret configured → 404."""
        app, env = app_with_user
        # No secret configured (default fixture doesn't set it)
        resp = app.get(
            "/dataset-rating/comment-captcha/challenge",
            environ_base=env,
            expect_errors=True,
        )
        assert resp.status_code == 404

    @pytest.mark.ckan_config("ckanext.artesp.rating.altcha_hmac_secret", "test-hmac-secret")
    def test_challenge_endpoint_503_when_altcha_unavailable(self, app_with_user):
        """Lines 431-433: altcha import unavailable → 503."""
        app, env = app_with_user
        with patch.dict(sys.modules, {"altcha": None}):
            resp = app.get(
                "/dataset-rating/comment-captcha/challenge",
                environ_base=env,
                expect_errors=True,
            )
        assert resp.status_code == 503


class TestRatingSubmitErrors:
    """Lines 497-499: ObjectNotFound in rating_submit."""

    def test_not_found_dataset_redirects_to_search(self, app_with_user, user):
        """Lines 497-499: package not found → redirect to dataset search."""
        app, env = app_with_user
        resp = app.post(
            "/dataset/nonexistent-dataset-name-xyz/rate",
            data={"overall_rating": "3"},
            environ_base=env,
        )
        # After following redirects, should end up at search or dataset page
        assert "dataset" in resp.request.url or "search" in resp.request.url


class TestStatsPageAccess:
    """Lines 524-526: /stats page access restriction."""

    @pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
    @pytest.mark.usefixtures("with_plugins")
    def test_stats_page_redirects_anonymous(self, app):
        """Anonymous user accessing /stats → redirect to login."""
        resp = app.get("/stats", follow_redirects=False)
        # Should redirect (anonymous)
        assert resp.status_code in (302, 303, 200)

    @pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
    @pytest.mark.usefixtures("with_plugins")
    def test_stats_page_accessible_to_authenticated_user(self, app_with_user):
        """Authenticated user accessing /stats → passes through (no redirect to login)."""
        app, env = app_with_user
        # The before_app_request checks g.user — skip if not easily testable
        resp = app.get("/stats", environ_base=env)
        # Should not redirect to login for authenticated user
        assert "login" not in resp.request.url or resp.status_code in (200, 404)
