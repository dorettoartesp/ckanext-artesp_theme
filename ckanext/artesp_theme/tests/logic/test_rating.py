"""Tests for rating.py classification helpers."""

import ckan.model as model
import pytest
from ckan.tests import factories
from sqlalchemy import text

from ckanext.artesp_theme.logic import rating


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.usefixtures("with_plugins", "clean_db"),
]


@pytest.fixture
def ldap_user_table():
    """Create ``ldap_user`` table mimicking ckanext-ldap, tear it down after."""
    model.Session.execute(
        text(
            "CREATE TABLE IF NOT EXISTS ldap_user ("
            " user_id TEXT PRIMARY KEY,"
            " ldap_id TEXT"
            ")"
        )
    )
    model.Session.commit()
    try:
        yield
    finally:
        model.Session.execute(text("DROP TABLE IF EXISTS ldap_user"))
        model.Session.commit()


def _insert_ldap_user(user_id, ldap_id="cn=test"):
    model.Session.execute(
        text("INSERT INTO ldap_user (user_id, ldap_id) VALUES (:u, :l)"),
        {"u": user_id, "l": ldap_id},
    )
    model.Session.commit()


class TestIsLdapUser:
    def test_returns_false_for_empty_or_none(self):
        assert rating.is_ldap_user("") is False
        assert rating.is_ldap_user(None) is False

    def test_returns_false_when_table_missing(self):
        # Fixture ldap_user_table is not requested here
        user = factories.User()
        assert rating.is_ldap_user(user["id"]) is False

    def test_returns_true_when_user_in_ldap_table(self, ldap_user_table):
        user = factories.User()
        _insert_ldap_user(user["id"])
        assert rating.is_ldap_user(user["id"]) is True

    def test_returns_false_when_user_not_in_ldap_table(self, ldap_user_table):
        user = factories.User()
        assert rating.is_ldap_user(user["id"]) is False


class TestGetRatingAuthorKind:
    def test_defaults_to_govbr(self, ldap_user_table):
        user = factories.User()
        assert rating.get_rating_author_kind(user["id"]) == "govbr"

    def test_returns_ldap_when_in_table(self, ldap_user_table):
        user = factories.User()
        _insert_ldap_user(user["id"])
        assert rating.get_rating_author_kind(user["id"]) == "ldap"

    def test_returns_govbr_when_table_missing(self):
        user = factories.User()
        assert rating.get_rating_author_kind(user["id"]) == "govbr"
