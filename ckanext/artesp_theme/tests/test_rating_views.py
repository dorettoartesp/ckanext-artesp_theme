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
    def test_captcha_not_configured_blocks_submit(self, app_with_user, user, pkg):
        app, env = app_with_user
        app.post(
            f"/dataset/{pkg['name']}/rate",
            data={"overall_rating": "4", "g-recaptcha-response": "token"},
            environ_base=env,
        )
        u = model.User.get(user["name"])
        assert DatasetRating.get_for(u.id, pkg["id"]) is None

    def test_captcha_configured_and_valid_creates_rating(self, app_with_user, user, pkg):
        app, env = app_with_user
        with patch("ckanext.artesp_theme.controllers._check_captcha_fail_closed"):
            app.post(
                f"/dataset/{pkg['name']}/rate",
                data={
                    "overall_rating": "4",
                    "criteria_links_work": "true",
                    "criteria_up_to_date": "false",
                    "criteria_well_structured": "true",
                    "g-recaptcha-response": "token",
                },
                environ_base=env,
            )
        u = model.User.get(user["name"])
        rating = DatasetRating.get_for(u.id, pkg["id"])
        assert rating is not None
        assert rating.overall_rating == 4

    def test_anonymous_redirects_to_login(self, app, pkg):
        resp = app.post(
            f"/dataset/{pkg['name']}/rate",
            data={"overall_rating": "3"},
        )
        # app follows redirect; final URL must contain "login"
        assert "login" in resp.request.url

    def test_invalid_rating_does_not_persist(self, app_with_user, user, pkg):
        app, env = app_with_user
        with patch("ckanext.artesp_theme.controllers._check_captcha_fail_closed"):
            app.post(
                f"/dataset/{pkg['name']}/rate",
                data={"overall_rating": "99", "g-recaptcha-response": "token"},
                environ_base=env,
            )
        u = model.User.get(user["name"])
        assert DatasetRating.get_for(u.id, pkg["id"]) is None


class TestRatingCaptchaFailClosed:
    def test_missing_privatekey_blocks_even_with_token(self, app_with_user, user, pkg):
        """No privatekey configured → must block (fail-closed), not allow."""
        app, env = app_with_user
        app.post(
            f"/dataset/{pkg['name']}/rate",
            data={"overall_rating": "4", "g-recaptcha-response": "any-token"},
            environ_base=env,
        )
        u = model.User.get(user["name"])
        assert DatasetRating.get_for(u.id, pkg["id"]) is None
