"""Tests for the dataset rating blueprint/controller."""

import uuid

import pytest
from unittest.mock import patch

import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.tests import factories

from ckanext.artesp_theme.logic import auth_helpers
from ckanext.artesp_theme.model import DatasetRating, dataset_rating_table


pytestmark = [
    pytest.mark.integration,
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.usefixtures("with_plugins"),
]


@pytest.fixture(autouse=True)
def _ensure_rating_table():
    bind = model.Session.get_bind()
    dataset_rating_table.create(bind=bind, checkfirst=True)
    model.Session.execute(dataset_rating_table.delete())
    model.Session.commit()
    yield
    model.Session.rollback()


@pytest.fixture
def artesp_org():
    org = auth_helpers.get_artesp_org()
    if org:
        return {"id": org.id, "name": org.name}
    return factories.Organization(name="artesp")


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


def _dataset(owner_org, user=None, private=False):
    suffix = uuid.uuid4().hex[:10]
    package = model.Package(
        name="rating-view-dataset-{}".format(suffix),
        title="Rating view dataset {}".format(suffix),
        owner_org=owner_org,
        private=private,
        state="active",
    )
    if user:
        package.creator_user_id = user["id"]
    model.Session.add(package)
    model.Session.flush()
    return {"id": package.id, "name": package.name}


@pytest.fixture
def user(artesp_org):
    return _user("rating-view-user")


@pytest.fixture
def pkg(user, artesp_org):
    return _dataset(artesp_org["id"], user=user)


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
        owner = _user("rating-view-owner")
        outsider = _user("rating-view-outsider")
        private_pkg = _dataset(
            artesp_org["id"],
            user=owner,
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


class TestRatingCommentSubmit:
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
