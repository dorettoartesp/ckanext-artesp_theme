"""Tests for dataset rating notification worker."""

import pytest

import ckan.model as model
from ckan.tests import factories

from ckanext.artesp_theme.logic import rating_notifications
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


def test_worker_sends_notifications_to_active_recipients(monkeypatch, artesp_org):
    author = factories.User()
    creator = factories.User()
    sysadmin = factories.Sysadmin()
    pkg = factories.Dataset(user=creator, owner_org=artesp_org["id"])

    rating = DatasetRating(
        user_id=author["id"],
        package_id=pkg["id"],
        overall_rating=5,
        comment="Helpful comment",
    )
    model.Session.add(rating)
    model.Session.commit()

    sent_to = []

    def fake_get_action(name):
        if name == "package_show":
            return lambda context, data_dict: {
                "id": pkg["id"],
                "name": pkg["name"],
                "title": pkg["title"],
                "creator_user_id": creator["id"],
            }
        if name == "package_collaborator_list":
            return lambda context, data_dict: []
        raise AssertionError(name)

    def fake_mail_user(user, subject, body):
        sent_to.append(user.id)

    monkeypatch.setattr(rating_notifications.tk, "get_action", fake_get_action)
    monkeypatch.setattr("ckan.lib.mailer.mail_user", fake_mail_user)

    rating_notifications.send_rating_comment_notifications(pkg["id"], rating.id)

    assert sorted(sent_to) == sorted([sysadmin["id"], creator["id"]])
