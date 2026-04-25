"""Unit tests for logic/auth_helpers.py.

These tests focus on the pure-Python helper functions using mocks to avoid
requiring a live database where possible. DB-touching tests use the standard
CKAN fixtures.
"""
from unittest.mock import MagicMock, patch, call

import pytest

import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.tests import factories

from ckanext.artesp_theme.logic import auth_helpers


pytestmark = [
    pytest.mark.integration,
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.ckan_config("ckan.auth.allow_dataset_collaborators", True),
    pytest.mark.ckan_config("ckan.auth.allow_admin_collaborators", True),
    pytest.mark.usefixtures("with_plugins", "non_clean_db"),
    pytest.mark.xdist_group("auth_helpers"),
]


def _artesp_org():
    org = auth_helpers.get_artesp_org()
    if org:
        return {"id": org.id, "name": org.name}
    return factories.Organization(name="artesp")


# ---------------------------------------------------------------------------
# get_user
# ---------------------------------------------------------------------------

class TestGetUser:
    def test_returns_none_for_falsy_identifier(self):
        assert auth_helpers.get_user(None) is None
        assert auth_helpers.get_user("") is None

    def test_returns_object_directly_when_has_id_attr(self):
        fake_user = MagicMock()
        fake_user.id = "uid-123"
        result = auth_helpers.get_user(fake_user)
        assert result is fake_user

    def test_looks_up_string_identifier(self):
        user = factories.User()
        result = auth_helpers.get_user(user["name"])
        assert result is not None
        assert result.id == user["id"]


# ---------------------------------------------------------------------------
# find_local_user_by_identifier
# ---------------------------------------------------------------------------

class TestFindLocalUserByIdentifier:
    def test_returns_none_for_falsy_identifier(self):
        assert auth_helpers.find_local_user_by_identifier(None) is None
        assert auth_helpers.find_local_user_by_identifier("") is None

    def test_finds_user_by_name(self):
        user = factories.User()
        result = auth_helpers.find_local_user_by_identifier(user["name"])
        assert result is not None
        assert result.id == user["id"]

    def test_falls_back_to_email_search(self):
        """Lines 52-53 / 56-60: fallback to email search when get_user returns None."""
        user = factories.User()
        # get_user("some@email.com") returns None; fallback queries by email
        result = auth_helpers.find_local_user_by_identifier(user["email"])
        assert result is not None
        assert result.id == user["id"]

    def test_returns_none_for_unknown_identifier(self):
        with patch.object(auth_helpers, "get_user", return_value=None), patch.object(
            model.Session, "query"
        ) as mock_query:
            mock_query.return_value.filter.return_value.filter.return_value.one_or_none.return_value = None
            result = auth_helpers.find_local_user_by_identifier(
                "totally-unknown-identifier"
            )
        assert result is None


# ---------------------------------------------------------------------------
# is_external_user (additional coverage via DB user)
# ---------------------------------------------------------------------------

class TestIsExternalUserDB:
    def test_returns_false_for_regular_user(self):
        user = factories.User()
        user_obj = model.User.get(user["name"])
        assert auth_helpers.is_external_user(user_obj) is False


# ---------------------------------------------------------------------------
# get_artesp_org
# ---------------------------------------------------------------------------

class TestGetArtespOrg:
    def test_returns_none_when_org_not_found(self):
        with patch.object(model.Group, "get", return_value=None):
            result = auth_helpers.get_artesp_org()
        assert result is None

    def test_returns_org_when_exists(self):
        _artesp_org()
        org = auth_helpers.get_artesp_org()
        assert org is not None
        assert org.name == "artesp"

    def test_returns_none_for_inactive_org(self):
        inactive_org = MagicMock(is_organization=True, state="deleted")
        with patch.object(model.Group, "get", return_value=inactive_org):
            result = auth_helpers.get_artesp_org()
        assert result is None


# ---------------------------------------------------------------------------
# get_group
# ---------------------------------------------------------------------------

class TestGetGroup:
    def test_returns_none_for_falsy(self):
        assert auth_helpers.get_group(None) is None
        assert auth_helpers.get_group("") is None

    def test_returns_object_with_id_directly(self):
        fake_group = MagicMock()
        fake_group.id = "grp-123"
        assert auth_helpers.get_group(fake_group) is fake_group

    def test_looks_up_group_by_name(self):
        group_dict = factories.Group(name="test-group-xyz")
        result = auth_helpers.get_group("test-group-xyz")
        assert result is not None
        assert result.id == group_dict["id"]

    def test_returns_none_for_missing_group(self):
        with patch.object(model.Group, "get", return_value=None):
            result = auth_helpers.get_group("nonexistent-group-abcdef")
        assert result is None


# ---------------------------------------------------------------------------
# ensure_user_membership
# ---------------------------------------------------------------------------

class TestEnsureUserMembership:
    def test_creates_membership_when_absent(self):
        org_dict = _artesp_org()
        user_dict = factories.User()
        user_obj = model.User.get(user_dict["name"])
        org_obj = model.Group.get(org_dict["id"])

        result = auth_helpers.ensure_user_membership(user_obj, org_obj, "member", enforce_capacity=True)
        assert result is True

        # Verify membership was actually created
        membership = (
            model.Session.query(model.Member)
            .filter(model.Member.table_name == "user")
            .filter(model.Member.table_id == user_obj.id)
            .filter(model.Member.group_id == org_obj.id)
            .first()
        )
        assert membership is not None

    def test_returns_false_for_invalid_user(self):
        org_dict = _artesp_org()
        org_obj = model.Group.get(org_dict["id"])
        result = auth_helpers.ensure_user_membership(None, org_obj, "member", enforce_capacity=False)
        assert result is False

    def test_returns_false_for_missing_group(self):
        user_dict = factories.User()
        user_obj = model.User.get(user_dict["name"])
        result = auth_helpers.ensure_user_membership(user_obj, None, "member", enforce_capacity=False)
        assert result is False

    def test_returns_true_without_enforcing_capacity_when_already_member(self):
        org_dict = _artesp_org()
        user_dict = factories.User()
        user_obj = model.User.get(user_dict["name"])
        org_obj = model.Group.get(org_dict["id"])

        # Add membership first
        auth_helpers.ensure_user_membership(user_obj, org_obj, "member", enforce_capacity=False)

        # Second call without enforcement should return True without re-calling member_create
        result = auth_helpers.ensure_user_membership(user_obj, org_obj, "editor", enforce_capacity=False)
        assert result is True


# ---------------------------------------------------------------------------
# get_package / get_resource / get_package_from_resource
# ---------------------------------------------------------------------------

class TestGetPackage:
    def test_returns_none_for_empty_data_dict(self):
        assert auth_helpers.get_package({}) is None
        assert auth_helpers.get_package(None) is None

    def test_returns_package_by_id(self):
        org_dict = _artesp_org()
        pkg_dict = factories.Dataset(owner_org=org_dict["id"])
        result = auth_helpers.get_package({"id": pkg_dict["id"]})
        assert result is not None
        assert result.id == pkg_dict["id"]

    def test_returns_package_by_name(self):
        org_dict = _artesp_org()
        pkg_dict = factories.Dataset(owner_org=org_dict["id"])
        result = auth_helpers.get_package({"name": pkg_dict["name"]})
        assert result is not None

    def test_returns_package_by_package_id(self):
        org_dict = _artesp_org()
        pkg_dict = factories.Dataset(owner_org=org_dict["id"])
        result = auth_helpers.get_package({"package_id": pkg_dict["id"]})
        assert result is not None


class TestGetResource:
    def test_returns_none_for_empty(self):
        assert auth_helpers.get_resource({}) is None

    def test_returns_resource_by_id(self):
        org_dict = _artesp_org()
        pkg_dict = factories.Dataset(owner_org=org_dict["id"])
        resource_dict = factories.Resource(package_id=pkg_dict["id"])
        result = auth_helpers.get_resource({"id": resource_dict["id"]})
        assert result is not None
        assert result.id == resource_dict["id"]

    def test_returns_resource_by_resource_id(self):
        org_dict = _artesp_org()
        pkg_dict = factories.Dataset(owner_org=org_dict["id"])
        resource_dict = factories.Resource(package_id=pkg_dict["id"])
        result = auth_helpers.get_resource({"resource_id": resource_dict["id"]})
        assert result is not None


class TestGetPackageFromResource:
    def test_returns_none_for_empty(self):
        assert auth_helpers.get_package_from_resource({}) is None

    def test_returns_package_via_resource_id(self):
        org_dict = _artesp_org()
        pkg_dict = factories.Dataset(owner_org=org_dict["id"])
        resource_dict = factories.Resource(package_id=pkg_dict["id"])
        result = auth_helpers.get_package_from_resource({"id": resource_dict["id"]})
        assert result is not None
        assert result.id == pkg_dict["id"]

    def test_returns_package_via_package_id_when_no_resource(self):
        org_dict = _artesp_org()
        pkg_dict = factories.Dataset(owner_org=org_dict["id"])
        result = auth_helpers.get_package_from_resource({"package_id": pkg_dict["id"]})
        assert result is not None

    def test_returns_none_when_package_id_missing(self):
        result = auth_helpers.get_package_from_resource({"something": "else"})
        assert result is None


# ---------------------------------------------------------------------------
# package_belongs_to_user
# ---------------------------------------------------------------------------

class TestPackageBelongsToUser:
    def test_returns_true_when_creator(self):
        org_dict = _artesp_org()
        user_dict = factories.User()
        pkg_dict = factories.Dataset(user=user_dict, owner_org=org_dict["id"])
        pkg_obj = model.Package.get(pkg_dict["id"])
        user_obj = model.User.get(user_dict["id"])

        assert auth_helpers.package_belongs_to_user(pkg_obj, user_obj) is True

    def test_returns_false_when_not_creator(self):
        org_dict = _artesp_org()
        user_dict = factories.User()
        other_user = factories.User()
        pkg_dict = factories.Dataset(user=user_dict, owner_org=org_dict["id"])
        pkg_obj = model.Package.get(pkg_dict["id"])
        other_user_obj = model.User.get(other_user["id"])

        assert auth_helpers.package_belongs_to_user(pkg_obj, other_user_obj) is False

    def test_returns_false_for_none(self):
        assert auth_helpers.package_belongs_to_user(None, None) is False


# ---------------------------------------------------------------------------
# get_collaborator / get_collaborator_by_user_id
# ---------------------------------------------------------------------------

class TestGetCollaborator:
    def test_returns_none_when_no_collaborator(self):
        org_dict = _artesp_org()
        user_dict = factories.User()
        pkg_dict = factories.Dataset(owner_org=org_dict["id"])
        pkg_obj = model.Package.get(pkg_dict["id"])
        user_obj = model.User.get(user_dict["id"])

        assert auth_helpers.get_collaborator(pkg_obj, user_obj) is None

    def test_returns_collaborator_when_exists(self):
        org_dict = _artesp_org()
        creator_dict = factories.User()
        collab_dict = factories.User()
        pkg_dict = factories.Dataset(user=creator_dict, owner_org=org_dict["id"])
        pkg_obj = model.Package.get(pkg_dict["id"])
        collab_obj = model.User.get(collab_dict["id"])

        # Add collaborator via action
        tk.get_action("package_collaborator_create")(
            {"ignore_auth": True},
            {"id": pkg_dict["id"], "user_id": collab_dict["id"], "capacity": "editor"},
        )

        result = auth_helpers.get_collaborator(pkg_obj, collab_obj)
        assert result is not None
        assert result.user_id == collab_dict["id"]

    def test_returns_none_for_none_args(self):
        assert auth_helpers.get_collaborator(None, None) is None


class TestGetCollaboratorByUserId:
    def test_returns_collaborator_by_user_id(self):
        org_dict = _artesp_org()
        creator_dict = factories.User()
        collab_dict = factories.User()
        pkg_dict = factories.Dataset(user=creator_dict, owner_org=org_dict["id"])
        pkg_obj = model.Package.get(pkg_dict["id"])

        tk.get_action("package_collaborator_create")(
            {"ignore_auth": True},
            {"id": pkg_dict["id"], "user_id": collab_dict["id"], "capacity": "editor"},
        )

        result = auth_helpers.get_collaborator_by_user_id(pkg_obj, collab_dict["id"])
        assert result is not None
        assert result.user_id == collab_dict["id"]

    def test_returns_none_for_none_args(self):
        assert auth_helpers.get_collaborator_by_user_id(None, None) is None
        assert auth_helpers.get_collaborator_by_user_id(None, "user-id") is None


# ---------------------------------------------------------------------------
# would_orphan_collaborator_governance
# ---------------------------------------------------------------------------

class TestWouldOrphanCollaboratorGovernance:
    def test_returns_false_for_none(self):
        assert auth_helpers.would_orphan_collaborator_governance(None, None) is False

    def test_returns_false_when_valid_creator_exists(self):
        org_dict = _artesp_org()
        creator_dict = factories.User()
        pkg_dict = factories.Dataset(user=creator_dict, owner_org=org_dict["id"])
        pkg_obj = model.Package.get(pkg_dict["id"])

        # Package has a valid creator → no orphan risk
        result = auth_helpers.would_orphan_collaborator_governance(pkg_obj, creator_dict["id"])
        assert result is False

    def test_returns_true_when_no_creator_and_last_admin_removed(self):
        org_dict = _artesp_org()
        admin_dict = factories.User()
        pkg_dict = factories.Dataset(owner_org=org_dict["id"])
        pkg_obj = model.Package.get(pkg_dict["id"])

        # Remove creator
        pkg_obj.creator_user_id = None
        model.Session.add(pkg_obj)
        model.Session.commit()

        # Add admin collaborator directly via DB
        member = model.PackageMember(
            package_id=pkg_dict["id"],
            user_id=admin_dict["id"],
            capacity="admin",
        )
        model.Session.add(member)
        model.Session.commit()

        # Removing the only admin → would orphan
        result = auth_helpers.would_orphan_collaborator_governance(pkg_obj, admin_dict["id"])
        assert result is True

    def test_returns_false_when_other_admin_exists(self):
        org_dict = _artesp_org()
        admin1_dict = factories.User()
        admin2_dict = factories.User()
        pkg_dict = factories.Dataset(owner_org=org_dict["id"])
        pkg_obj = model.Package.get(pkg_dict["id"])

        pkg_obj.creator_user_id = None
        model.Session.add(pkg_obj)
        model.Session.commit()

        # Add two admin collaborators directly via DB
        for admin in [admin1_dict, admin2_dict]:
            member = model.PackageMember(
                package_id=pkg_dict["id"],
                user_id=admin["id"],
                capacity="admin",
            )
            model.Session.add(member)
        model.Session.commit()

        # Removing admin1 → admin2 still exists → no orphan
        result = auth_helpers.would_orphan_collaborator_governance(pkg_obj, admin1_dict["id"])
        assert result is False


# ---------------------------------------------------------------------------
# normalize_package_collaborator_create_data
# ---------------------------------------------------------------------------

class TestNormalizePackageCollaboratorCreateData:
    def test_raises_validation_error_when_no_username(self):
        with pytest.raises(tk.ValidationError):
            auth_helpers.normalize_package_collaborator_create_data(
                {"ignore_auth": True}, {}
            )

    def test_raises_not_found_when_user_not_found(self, monkeypatch):
        monkeypatch.setattr(auth_helpers, "resolve_or_create_collaborator_user", lambda uid: None)
        with pytest.raises(tk.ObjectNotFound):
            auth_helpers.normalize_package_collaborator_create_data(
                {"ignore_auth": True},
                {"user_id": "nonexistent-user-id-abc123"},
            )

    def test_sysadmin_must_provide_capacity(self):
        sysadmin = factories.Sysadmin()
        target = factories.User()
        sysadmin_obj = model.User.get(sysadmin["name"])

        with pytest.raises(tk.ValidationError):
            auth_helpers.normalize_package_collaborator_create_data(
                {"auth_user_obj": sysadmin_obj},
                {"user_id": target["id"]},
            )

    def test_regular_user_gets_default_capacity(self):
        org_dict = _artesp_org()
        creator_dict = factories.User()
        target_dict = factories.User()
        creator_obj = model.User.get(creator_dict["name"])
        pkg_dict = factories.Dataset(user=creator_dict, owner_org=org_dict["id"])

        result = auth_helpers.normalize_package_collaborator_create_data(
            {"auth_user_obj": creator_obj},
            {"user_id": target_dict["id"], "id": pkg_dict["id"]},
        )
        assert result["capacity"] == auth_helpers.DEFAULT_DATASET_COLLABORATOR_CAPACITY

    def test_raises_not_authorized_when_non_default_capacity_requested(self):
        org_dict = _artesp_org()
        creator_dict = factories.User()
        target_dict = factories.User()
        creator_obj = model.User.get(creator_dict["name"])
        pkg_dict = factories.Dataset(user=creator_dict, owner_org=org_dict["id"])

        with pytest.raises(tk.NotAuthorized):
            auth_helpers.normalize_package_collaborator_create_data(
                {"auth_user_obj": creator_obj},
                {"user_id": target_dict["id"], "id": pkg_dict["id"], "capacity": "member"},
            )

    def test_raises_not_authorized_when_existing_collaborator_and_non_sysadmin(self):
        org_dict = _artesp_org()
        creator_dict = factories.User()
        target_dict = factories.User()
        creator_obj = model.User.get(creator_dict["name"])
        pkg_dict = factories.Dataset(user=creator_dict, owner_org=org_dict["id"])

        # Add as collaborator first
        tk.get_action("package_collaborator_create")(
            {"ignore_auth": True},
            {"id": pkg_dict["id"], "user_id": target_dict["id"], "capacity": "editor"},
        )

        with pytest.raises(tk.NotAuthorized):
            auth_helpers.normalize_package_collaborator_create_data(
                {"auth_user_obj": creator_obj},
                {"user_id": target_dict["id"], "id": pkg_dict["id"]},
            )


# ---------------------------------------------------------------------------
# get_default_dataset_collaborator_capacity
# ---------------------------------------------------------------------------

class TestGetDefaultDatasetCollaboratorCapacity:
    def test_returns_editor_by_default(self):
        assert auth_helpers.get_default_dataset_collaborator_capacity() == "editor"

    @pytest.mark.ckan_config(
        "ckanext.artesp_theme.default_dataset_collaborator_capacity", "member"
    )
    def test_returns_configured_capacity(self):
        assert auth_helpers.get_default_dataset_collaborator_capacity() == "member"

    @pytest.mark.ckan_config(
        "ckanext.artesp_theme.default_dataset_collaborator_capacity", "superadmin"
    )
    def test_falls_back_to_editor_for_invalid_value(self):
        assert auth_helpers.get_default_dataset_collaborator_capacity() == "editor"


# ---------------------------------------------------------------------------
# is_artesp_owner_org
# ---------------------------------------------------------------------------

class TestIsArtespOwnerOrg:
    def test_returns_false_for_empty(self):
        assert auth_helpers.is_artesp_owner_org(None) is False
        assert auth_helpers.is_artesp_owner_org("") is False

    def test_returns_false_when_org_not_found(self):
        with patch.object(model.Group, "get", return_value=None):
            assert auth_helpers.is_artesp_owner_org("artesp") is False

    def test_returns_true_for_artesp_org_id(self):
        org_dict = _artesp_org()
        assert auth_helpers.is_artesp_owner_org(org_dict["id"]) is True

    def test_returns_true_for_artesp_org_name(self):
        _artesp_org()
        assert auth_helpers.is_artesp_owner_org("artesp") is True
