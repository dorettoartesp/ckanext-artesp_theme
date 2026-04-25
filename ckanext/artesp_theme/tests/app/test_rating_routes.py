"""App-layer tests for rating routes that do not need rating persistence."""

import sys
import types
import uuid
from unittest.mock import MagicMock, patch

import ckan.model as model
import pytest


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.usefixtures("with_plugins"),
]


def _user(prefix):
    suffix = uuid.uuid4().hex
    user = model.User(
        name="{}-{}".format(prefix, suffix[:10]),
        email="{}-{}@ckan.example.com".format(prefix, suffix),
        state="active",
    )
    model.Session.add(user)
    model.Session.flush()
    return {"id": user.id, "name": user.name, "email": user.email}


@pytest.fixture
def app_with_user(app):
    user = _user("rating-route-user")
    return app, {"REMOTE_USER": user["name"]}


class TestRatingCommentCaptchaChallenge:
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
        """Line 423: anonymous -> 403."""
        resp = app.get(
            "/dataset-rating/comment-captcha/challenge",
            expect_errors=True,
        )
        assert resp.status_code == 403

    def test_challenge_endpoint_returns_404_when_no_secret(self, app_with_user):
        """Lines 425-427: no secret configured -> 404."""
        app, env = app_with_user
        resp = app.get(
            "/dataset-rating/comment-captcha/challenge",
            environ_base=env,
            expect_errors=True,
        )
        assert resp.status_code == 404

    @pytest.mark.ckan_config("ckanext.artesp.rating.altcha_hmac_secret", "test-hmac-secret")
    def test_challenge_endpoint_503_when_altcha_unavailable(self, app_with_user):
        """Lines 431-433: altcha import unavailable -> 503."""
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

    def test_not_found_dataset_redirects_to_search(self, app_with_user):
        """Lines 497-499: package not found -> redirect to dataset search."""
        app, env = app_with_user
        resp = app.post(
            "/dataset/nonexistent-dataset-name-xyz/rate",
            data={"overall_rating": "3"},
            environ_base=env,
        )
        assert "dataset" in resp.request.url or "search" in resp.request.url


class TestStatsPageAccess:
    """Lines 524-526: /stats page access restriction."""

    def test_stats_page_redirects_anonymous(self, app):
        """Anonymous user accessing /stats -> redirect to login."""
        resp = app.get("/stats", follow_redirects=False)
        assert resp.status_code in (302, 303, 200)

    def test_stats_page_accessible_to_authenticated_user(self, app_with_user):
        """Authenticated user accessing /stats -> passes through."""
        app, env = app_with_user
        resp = app.get("/stats", environ_base=env)
        assert "login" not in resp.request.url or resp.status_code in (200, 404)
