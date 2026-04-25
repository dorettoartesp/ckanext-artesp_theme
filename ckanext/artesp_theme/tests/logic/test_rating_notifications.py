"""Tests for dataset rating notification worker."""

import uuid

import pytest

import ckan.model as model
from ckan.tests import factories

from ckanext.artesp_theme.logic import auth_helpers
from ckanext.artesp_theme.logic import rating_notifications
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


def _package(user=None, owner_org="artesp"):
    package = model.Package(
        name="rating-pkg-{}".format(uuid.uuid4().hex[:8]),
        title="Rating package",
        owner_org=owner_org,
        creator_user_id=user["id"] if isinstance(user, dict) else getattr(user, "id", None),
        state="active",
    )
    model.Session.add(package)
    model.Session.commit()
    return {"id": package.id, "name": package.name, "title": package.title}


def test_worker_sends_notifications_to_active_recipients(monkeypatch, artesp_org):
    author = factories.User()
    creator = factories.User()
    sysadmin = factories.Sysadmin()
    pkg = _package(user=creator, owner_org=artesp_org["id"])

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

    assert sysadmin["id"] in sent_to
    assert creator["id"] in sent_to
    assert author["id"] not in sent_to


# ---------------------------------------------------------------------------
# Additional coverage for missing branches
# ---------------------------------------------------------------------------

def test_worker_returns_early_when_rating_not_found(monkeypatch, artesp_org):
    """Line 19: rating not found → early return (no error)."""
    called = []
    monkeypatch.setattr(
        rating_notifications.tk,
        "get_action",
        lambda name: (lambda ctx, dd: called.append(name)),
    )
    # Non-existent rating id — should return silently
    rating_notifications.send_rating_comment_notifications("pkg-id", "nonexistent-rating-id")
    assert called == []


def test_worker_returns_early_when_rating_has_no_comment(monkeypatch, artesp_org):
    """Line 19: rating exists but has no comment → early return."""
    pkg = _package(owner_org=artesp_org["id"])
    author = factories.User()

    rating = DatasetRating(
        user_id=author["id"],
        package_id=pkg["id"],
        overall_rating=3,
        comment="",  # empty comment
    )
    model.Session.add(rating)
    model.Session.commit()

    called = []
    monkeypatch.setattr(
        rating_notifications.tk,
        "get_action",
        lambda name: (lambda ctx, dd: called.append(name)),
    )

    rating_notifications.send_rating_comment_notifications(pkg["id"], rating.id)
    assert called == []


def test_worker_logs_and_returns_when_no_recipients(monkeypatch, artesp_org):
    """Lines 32-33: no recipients → log and return without sending mail."""
    creator = factories.User()
    pkg = _package(user=creator, owner_org=artesp_org["id"])
    author = factories.User()

    rating = DatasetRating(
        user_id=author["id"],
        package_id=pkg["id"],
        overall_rating=4,
        comment="Good data",
    )
    model.Session.add(rating)
    model.Session.commit()

    # Patch so _resolve_recipients returns empty list
    monkeypatch.setattr(rating_notifications, "_resolve_recipients", lambda pkg_dict, user_id: [])

    sent = []
    monkeypatch.setattr("ckan.lib.mailer.mail_user", lambda user, subj, body: sent.append(user.id))

    def fake_get_action(name):
        if name == "package_show":
            return lambda ctx, dd: {
                "id": pkg["id"],
                "name": pkg["name"],
                "title": pkg["title"],
                "creator_user_id": creator["id"],
            }
        raise AssertionError(name)

    monkeypatch.setattr(rating_notifications.tk, "get_action", fake_get_action)

    rating_notifications.send_rating_comment_notifications(pkg["id"], rating.id)
    assert sent == []


def test_worker_continues_after_mailer_exception(monkeypatch, artesp_org):
    """Lines 52-53: MailerException per recipient → log warning, continue."""
    from ckan.lib import mailer

    creator = factories.User()
    sysadmin = factories.Sysadmin()
    pkg = _package(user=creator, owner_org=artesp_org["id"])
    author = factories.User()

    rating = DatasetRating(
        user_id=author["id"],
        package_id=pkg["id"],
        overall_rating=5,
        comment="Feedback here",
    )
    model.Session.add(rating)
    model.Session.commit()

    recipient_user = model.User.get(creator["id"])

    def fake_get_action(name):
        if name == "package_show":
            return lambda ctx, dd: {
                "id": pkg["id"],
                "name": pkg["name"],
                "title": pkg["title"],
                "creator_user_id": creator["id"],
            }
        if name == "package_collaborator_list":
            return lambda ctx, dd: []
        raise AssertionError(name)

    monkeypatch.setattr(rating_notifications.tk, "get_action", fake_get_action)

    call_count = [0]

    def fail_mail_user(user, subject, body):
        call_count[0] += 1
        raise mailer.MailerException("SMTP failure")

    monkeypatch.setattr("ckan.lib.mailer.mail_user", fail_mail_user)

    # Should not raise; mailer exception is caught
    rating_notifications.send_rating_comment_notifications(pkg["id"], rating.id)
    assert call_count[0] >= 1


def test_resolve_recipients_skips_inactive_user(monkeypatch, artesp_org):
    """Line 72: inactive user is skipped."""
    creator = factories.User()

    # Make a deactivated user
    deactivated_user = factories.User()
    deactivated_obj = model.User.get(deactivated_user["id"])
    deactivated_obj.state = "deleted"
    model.Session.add(deactivated_obj)
    model.Session.commit()

    pkg_dict = {
        "id": "pkg-id",
        "name": "pkg-name",
        "creator_user_id": deactivated_user["id"],
    }

    def fake_get_action(name):
        if name == "package_collaborator_list":
            return lambda ctx, dd: []
        raise AssertionError(name)

    monkeypatch.setattr(rating_notifications.tk, "get_action", fake_get_action)

    # author is different, deactivated creator should be excluded
    recipients = rating_notifications._resolve_recipients(pkg_dict, creator["id"])
    recipient_ids = [r.id for r in recipients]
    assert deactivated_user["id"] not in recipient_ids


def test_resolve_recipients_skips_duplicate_user_id(monkeypatch, artesp_org):
    """Line 74: duplicate by user.id is deduplicated."""
    creator = factories.User()

    # Same user as both creator and collaborator
    pkg_dict = {
        "id": "pkg-id",
        "name": "pkg-name",
        "creator_user_id": creator["id"],
    }

    def fake_get_action(name):
        if name == "package_collaborator_list":
            # Return creator as collaborator too — should deduplicate
            return lambda ctx, dd: [{"user_id": creator["id"]}]
        raise AssertionError(name)

    monkeypatch.setattr(rating_notifications.tk, "get_action", fake_get_action)

    recipients = rating_notifications._resolve_recipients(pkg_dict, "some-other-author-id")
    # Creator appears only once
    creator_ids = [r.id for r in recipients if r.id == creator["id"]]
    assert len(creator_ids) <= 1


def test_resolve_recipients_skips_author(monkeypatch, artesp_org):
    """Line 79: the author is not added to recipients."""
    creator = factories.User()

    pkg_dict = {
        "id": "pkg-id",
        "name": "pkg-name",
        "creator_user_id": creator["id"],
    }

    def fake_get_action(name):
        if name == "package_collaborator_list":
            return lambda ctx, dd: []
        raise AssertionError(name)

    monkeypatch.setattr(rating_notifications.tk, "get_action", fake_get_action)

    # Use creator as the author — creator should NOT appear in recipients
    recipients = rating_notifications._resolve_recipients(pkg_dict, creator["id"])
    assert all(r.id != creator["id"] for r in recipients)


def test_resolve_recipients_includes_collaborators(monkeypatch, artesp_org):
    """Line 95: collaborators from package_collaborator_list are included."""
    creator = factories.User()
    collaborator = factories.User()
    author = factories.User()

    pkg_dict = {
        "id": "pkg-id",
        "name": "pkg-name",
        "creator_user_id": None,  # No creator, just collaborator
    }

    def fake_get_action(name):
        if name == "package_collaborator_list":
            return lambda ctx, dd: [{"user_id": collaborator["id"]}]
        raise AssertionError(name)

    monkeypatch.setattr(rating_notifications.tk, "get_action", fake_get_action)

    recipients = rating_notifications._resolve_recipients(pkg_dict, author["id"])
    recipient_ids = [r.id for r in recipients]
    assert collaborator["id"] in recipient_ids


def test_resolve_recipients_handles_collaborator_list_validation_error(monkeypatch, artesp_org):
    """Lines 96-97: ValidationError from package_collaborator_list → treat as empty list."""
    creator = factories.User()

    pkg_dict = {
        "id": "pkg-id",
        "name": "pkg-name",
        "creator_user_id": creator["id"],
    }

    def fake_get_action(name):
        if name == "package_collaborator_list":
            def raise_validation(ctx, dd):
                raise rating_notifications.tk.ValidationError({"id": ["Invalid"]})
            return raise_validation
        raise AssertionError(name)

    monkeypatch.setattr(rating_notifications.tk, "get_action", fake_get_action)

    # Should not raise; ValidationError from collaborator list is swallowed
    recipients = rating_notifications._resolve_recipients(pkg_dict, "other-author-id")
    assert isinstance(recipients, list)
