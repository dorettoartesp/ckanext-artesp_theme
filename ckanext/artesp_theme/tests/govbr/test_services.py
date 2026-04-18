"""TDD: ExternalUserService — find_or_create, link_account, unlink_account."""
from unittest.mock import MagicMock, patch, call

import pytest

from ckanext.artesp_theme.govbr.models import UserInfo
from ckanext.artesp_theme.govbr.services import (
    ExternalUserService,
    GovBRLinkError,
)


GOVBR_SUB = "12345678901"
CPF_HASH = "govbr_" + __import__("hashlib").sha256(GOVBR_SUB.encode()).hexdigest()[:12]


@pytest.fixture
def userinfo():
    return UserInfo(
        sub=GOVBR_SUB,
        name="João Silva",
        email="joao@example.com",
        email_verified=True,
    )


@pytest.fixture
def service():
    return ExternalUserService()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_ckan_user(
    name=CPF_HASH,
    email="joao@example.com",
    plugin_extras=None,
    state="active",
):
    u = MagicMock()
    u.name = name
    u.email = email
    u.state = state
    u.plugin_extras = plugin_extras or {}
    return u


# ---------------------------------------------------------------------------
# username derivation
# ---------------------------------------------------------------------------

class TestUsernameDerivation:
    def test_username_is_deterministic(self, service, userinfo):
        assert service.derive_username(userinfo.sub) == service.derive_username(userinfo.sub)

    def test_username_starts_with_govbr(self, service, userinfo):
        assert service.derive_username(userinfo.sub).startswith("govbr_")

    def test_username_does_not_contain_cpf(self, service, userinfo):
        assert GOVBR_SUB not in service.derive_username(userinfo.sub)

    def test_username_length_reasonable(self, service, userinfo):
        name = service.derive_username(userinfo.sub)
        assert 10 <= len(name) <= 40


# ---------------------------------------------------------------------------
# find_or_create — new external user
# ---------------------------------------------------------------------------

class TestFindOrCreateNewExternalUser:
    def test_creates_new_user_when_not_found(self, service, userinfo):
        with (
            patch.object(service, "_find_by_govbr_sub", return_value=None),
            patch.object(service, "_find_by_name", return_value=None),
            patch.object(service, "_create_external_user") as mock_create,
            patch.object(service, "_save_user"),
        ):
            mock_create.return_value = _make_ckan_user()
            result = service.find_or_create(userinfo)
            mock_create.assert_called_once()
            assert result is not None

    def test_new_user_gets_external_user_type(self, service, userinfo):
        created = _make_ckan_user()
        with (
            patch.object(service, "_find_by_govbr_sub", return_value=None),
            patch.object(service, "_find_by_name", return_value=None),
            patch.object(service, "_create_external_user", return_value=created),
            patch.object(service, "_save_user"),
        ):
            service.find_or_create(userinfo)
            extras = created.plugin_extras
            assert extras.get("artesp", {}).get("user_type") == "external"

    def test_new_user_gets_govbr_sub_stored(self, service, userinfo):
        created = _make_ckan_user()
        with (
            patch.object(service, "_find_by_govbr_sub", return_value=None),
            patch.object(service, "_find_by_name", return_value=None),
            patch.object(service, "_create_external_user", return_value=created),
            patch.object(service, "_save_user"),
        ):
            service.find_or_create(userinfo)
            extras = created.plugin_extras
            assert extras.get("artesp", {}).get("govbr_sub") == GOVBR_SUB


# ---------------------------------------------------------------------------
# find_or_create — existing external user (already linked)
# ---------------------------------------------------------------------------

class TestFindOrCreateExistingExternalUser:
    def test_returns_existing_external_user(self, service, userinfo):
        existing = _make_ckan_user(
            plugin_extras={"artesp": {"user_type": "external", "govbr_sub": GOVBR_SUB}}
        )
        with patch.object(service, "_find_by_govbr_sub", return_value=existing):
            result = service.find_or_create(userinfo)
        assert result is existing

    def test_does_not_create_when_existing_found(self, service, userinfo):
        existing = _make_ckan_user(
            plugin_extras={"artesp": {"user_type": "external", "govbr_sub": GOVBR_SUB}}
        )
        with (
            patch.object(service, "_find_by_govbr_sub", return_value=existing),
            patch.object(service, "_create_external_user") as mock_create,
        ):
            service.find_or_create(userinfo)
            mock_create.assert_not_called()


# ---------------------------------------------------------------------------
# find_or_create — internal user with govbr_sub linked (LDAP flow)
# ---------------------------------------------------------------------------

class TestFindOrCreateLinkedInternalUser:
    def test_returns_internal_user_when_sub_linked(self, service, userinfo):
        internal = _make_ckan_user(
            name="ldap_joao",
            plugin_extras={"artesp": {"user_type": "internal", "govbr_sub": GOVBR_SUB}},
        )
        with patch.object(service, "_find_by_govbr_sub", return_value=internal):
            result = service.find_or_create(userinfo)
        assert result is internal

    def test_internal_user_returned_without_modification(self, service, userinfo):
        internal = _make_ckan_user(
            name="ldap_joao",
            plugin_extras={"artesp": {"user_type": "internal", "govbr_sub": GOVBR_SUB}},
        )
        with (
            patch.object(service, "_find_by_govbr_sub", return_value=internal),
            patch.object(service, "_create_external_user") as mock_create,
        ):
            service.find_or_create(userinfo)
            mock_create.assert_not_called()


# ---------------------------------------------------------------------------
# link_account
# ---------------------------------------------------------------------------

class TestLinkAccount:
    def test_stores_govbr_sub_in_plugin_extras(self, service, userinfo):
        ldap_user = _make_ckan_user(name="ldap_joao", plugin_extras={"artesp": {"user_type": "internal"}})
        with (
            patch.object(service, "_find_by_govbr_sub", return_value=None),
            patch.object(service, "_save_user") as mock_save,
        ):
            service.link_account(ldap_user, userinfo)
            mock_save.assert_called_once_with(ldap_user)
            assert ldap_user.plugin_extras["artesp"]["govbr_sub"] == GOVBR_SUB

    def test_raises_if_sub_already_linked_to_another_user(self, service, userinfo):
        other_user = _make_ckan_user(name="other_user")
        ldap_user = _make_ckan_user(name="ldap_joao")
        with patch.object(service, "_find_by_govbr_sub", return_value=other_user):
            with pytest.raises(GovBRLinkError, match="already linked"):
                service.link_account(ldap_user, userinfo)

    def test_no_error_if_sub_linked_to_same_user(self, service, userinfo):
        ldap_user = _make_ckan_user(
            name="ldap_joao",
            plugin_extras={"artesp": {"user_type": "internal", "govbr_sub": GOVBR_SUB}},
        )
        with (
            patch.object(service, "_find_by_govbr_sub", return_value=ldap_user),
            patch.object(service, "_save_user"),
        ):
            service.link_account(ldap_user, userinfo)  # should not raise


# ---------------------------------------------------------------------------
# unlink_account
# ---------------------------------------------------------------------------

class TestUnlinkAccount:
    def test_removes_govbr_sub_from_plugin_extras(self, service):
        user = _make_ckan_user(
            plugin_extras={"artesp": {"user_type": "internal", "govbr_sub": GOVBR_SUB}}
        )
        with patch.object(service, "_save_user") as mock_save:
            service.unlink_account(user)
            mock_save.assert_called_once_with(user)
            assert "govbr_sub" not in user.plugin_extras.get("artesp", {})

    def test_unlink_idempotent_when_not_linked(self, service):
        user = _make_ckan_user(plugin_extras={"artesp": {"user_type": "internal"}})
        with patch.object(service, "_save_user"):
            service.unlink_account(user)  # should not raise


# ---------------------------------------------------------------------------
# get_by_govbr_sub (public alias for _find_by_govbr_sub)
# ---------------------------------------------------------------------------

class TestGetByGovBRSub:
    def test_returns_none_when_not_found(self, service):
        with patch.object(service, "_find_by_govbr_sub", return_value=None):
            assert service.get_by_govbr_sub(GOVBR_SUB) is None

    def test_returns_user_when_found(self, service):
        user = _make_ckan_user()
        with patch.object(service, "_find_by_govbr_sub", return_value=user):
            assert service.get_by_govbr_sub(GOVBR_SUB) is user
