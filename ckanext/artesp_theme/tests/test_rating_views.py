"""Tests for the dataset rating blueprint/controller."""

import pytest
from unittest.mock import patch

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
    def test_challenge_endpoint_returns_nested_parameters(self):
        """Challenge JSON must preserve the nested {parameters, signature} structure for PBKDF2."""
        from datetime import datetime, timezone, timedelta
        from altcha import create_challenge

        challenge = create_challenge(
            algorithm="PBKDF2/SHA-256",
            cost=1,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=1),
            hmac_secret="test-secret",
        )
        payload = challenge.to_dict()
        assert "parameters" in payload
        assert "signature" in payload
        assert payload["parameters"]["algorithm"] == "PBKDF2/SHA-256"

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
