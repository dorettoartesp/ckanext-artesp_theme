"""Tests for rating.py classification helpers."""

import ckan.model as model
import pytest
from sqlalchemy import text

from ckanext.artesp_theme.logic import rating


pytestmark = [
    pytest.mark.integration,
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.usefixtures("with_plugins"),
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


def _drop_ldap_user_table():
    model.Session.execute(text("DROP TABLE IF EXISTS ldap_user"))
    model.Session.commit()


class TestIsLdapUser:
    def test_returns_false_for_empty_or_none(self):
        assert rating.is_ldap_user("") is False
        assert rating.is_ldap_user(None) is False

    def test_returns_false_when_table_missing(self):
        # Fixture ldap_user_table is not requested here
        _drop_ldap_user_table()
        assert rating.is_ldap_user("missing-table-user") is False

    def test_returns_true_when_user_in_ldap_table(self, ldap_user_table):
        _insert_ldap_user("ldap-user")
        assert rating.is_ldap_user("ldap-user") is True

    def test_returns_false_when_user_not_in_ldap_table(self, ldap_user_table):
        assert rating.is_ldap_user("not-ldap-user") is False


class TestGetRatingAuthorKind:
    def test_defaults_to_govbr(self, ldap_user_table):
        assert rating.get_rating_author_kind("govbr-user") == "govbr"

    def test_returns_ldap_when_in_table(self, ldap_user_table):
        _insert_ldap_user("ldap-author")
        assert rating.get_rating_author_kind("ldap-author") == "ldap"

    def test_returns_govbr_when_table_missing(self):
        _drop_ldap_user_table()
        assert rating.get_rating_author_kind("missing-table-author") == "govbr"
