"""Additional focused tests for auth_helpers.py coverage gaps."""

import sys
import types
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import ckan.model as model
import ckan.plugins.toolkit as tk
import pytest
from ckan.tests import factories

from ckanext.artesp_theme.logic import auth_helpers


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.ckan_config("ckan.auth.allow_dataset_collaborators", True),
    pytest.mark.ckan_config("ckan.auth.allow_admin_collaborators", True),
    pytest.mark.usefixtures("with_plugins", "non_clean_db"),
]


def _artesp_org():
    org = auth_helpers.get_artesp_org()
    if org:
        return {"id": org.id, "name": org.name}
    return factories.Organization(name="artesp")


class TestAuthenticatedUserHelpers:
    def test_get_authenticated_user_prefers_auth_user_obj(self):
        user = factories.User()
        user_obj = model.User.get(user["name"])

        result = auth_helpers.get_authenticated_user(
            {"auth_user_obj": user_obj, "user": "ignored"}
        )

        assert result is user_obj

    def test_get_authenticated_user_looks_up_username(self):
        user = factories.User()

        result = auth_helpers.get_authenticated_user({"user": user["name"]})

        assert result.id == user["id"]

    def test_get_authenticated_user_returns_none_without_user(self):
        assert auth_helpers.get_authenticated_user({}) is None

    def test_is_sysadmin_returns_true_for_sysadmin(self):
        sysadmin = factories.Sysadmin()

        assert auth_helpers.is_sysadmin({"user": sysadmin["name"]}) is True

    def test_is_external_user_supports_string_identifier(self):
        user = factories.User()
        user_obj = model.User.get(user["name"])
        user_obj.plugin_extras = {"artesp": {"user_type": "external"}}
        model.Session.add(user_obj)
        model.Session.commit()

        assert auth_helpers.is_external_user(user["name"]) is True

    @pytest.mark.usefixtures("clean_db")
    def test_is_external_user_returns_false_for_missing_user(self):
        assert auth_helpers.is_external_user("missing-user") is False


class TestArtespConfigurationHelpers:
    @pytest.mark.ckan_config("ckanext.ldap.organization.id", " custom-artesp ")
    def test_get_artesp_org_identifier_uses_configured_value(self):
        assert auth_helpers.get_artesp_org_identifier() == "custom-artesp"

    @pytest.mark.ckan_config("ckanext.ldap.organization.title", " ARTESP Custom ")
    def test_get_artesp_org_title_uses_configured_value(self):
        assert auth_helpers.get_artesp_org_title() == "ARTESP Custom"

    def test_get_artesp_org_display_name_falls_back_to_org_fields(self, monkeypatch):
        fake_org = SimpleNamespace(display_name="", title="Org Title", name="org-name")
        monkeypatch.setattr(auth_helpers, "get_artesp_org", lambda: fake_org)
        monkeypatch.setattr(auth_helpers, "get_artesp_org_title", lambda: "")

        assert auth_helpers.get_artesp_org_display_name() == "Org Title"

    def test_get_artesp_org_display_name_returns_none_without_org(self, monkeypatch):
        monkeypatch.setattr(auth_helpers, "get_artesp_org", lambda: None)
        monkeypatch.setattr(auth_helpers, "get_artesp_org_title", lambda: "")

        assert auth_helpers.get_artesp_org_display_name() is None

    @pytest.mark.ckan_config("ckanext.artesp_theme.reconcile_ldap_login", "true")
    def test_should_reconcile_ldap_login_reads_config(self):
        assert auth_helpers.should_reconcile_ldap_login() is True


class TestMembershipAndOrganizationHelpers:
    @pytest.mark.usefixtures("clean_db")
    def test_get_active_groups_excludes_organizations(self):
        factories.Organization(name="artesp")
        group = factories.Group(name="grupo-ativo")

        groups = auth_helpers.get_active_groups()

        assert [item.name for item in groups] == [group["name"]]

    def test_get_ldap_users_rolls_back_on_query_error(self, monkeypatch):
        rolled_back = []

        monkeypatch.setattr(
            model.Session,
            "execute",
            lambda statement: (_ for _ in ()).throw(Exception("db error")),
        )
        monkeypatch.setattr(model.Session, "rollback", lambda: rolled_back.append(True))

        assert auth_helpers.get_ldap_users() == []
        assert rolled_back == [True]

    def test_get_ldap_users_returns_only_active_users(self, monkeypatch):
        active_user = factories.User()
        deleted_user = factories.User()
        deleted_obj = model.User.get(deleted_user["name"])
        deleted_obj.state = "deleted"
        model.Session.add(deleted_obj)
        model.Session.commit()

        fake_result = SimpleNamespace(
            fetchall=lambda: [(active_user["id"],), (deleted_user["id"],), (None,)]
        )
        monkeypatch.setattr(model.Session, "execute", lambda statement: fake_result)

        users = auth_helpers.get_ldap_users()

        assert [user.id for user in users] == [active_user["id"]]

    def test_ensure_user_membership_returns_true_when_capacity_already_matches(
        self, monkeypatch
    ):
        org = _artesp_org()
        user = factories.User()
        user_obj = model.User.get(user["name"])
        group_obj = model.Group.get(org["id"])

        auth_helpers.ensure_user_membership(
            user_obj,
            group_obj,
            "member",
            enforce_capacity=True,
        )

        monkeypatch.setattr(
            auth_helpers.tk,
            "get_action",
            lambda name: (_ for _ in ()).throw(AssertionError("should not create")),
        )

        assert (
            auth_helpers.ensure_user_membership(
                user_obj,
                group_obj,
                "member",
                enforce_capacity=True,
            )
            is True
        )

    @pytest.mark.ckan_config("ckanext.ldap.organization.role", "editor")
    def test_ensure_user_membership_in_artesp_uses_configured_role(self, monkeypatch):
        captured = {}
        fake_org = SimpleNamespace(id="org-id")

        monkeypatch.setattr(auth_helpers, "get_artesp_org", lambda: fake_org)
        monkeypatch.setattr(
            auth_helpers,
            "ensure_user_membership",
            lambda user, group, desired_capacity, enforce_capacity: captured.update(
                {
                    "user": user,
                    "group": group,
                    "desired_capacity": desired_capacity,
                    "enforce_capacity": enforce_capacity,
                }
            )
            or True,
        )

        assert auth_helpers.ensure_user_membership_in_artesp("alice") is True
        assert captured == {
            "user": "alice",
            "group": fake_org,
            "desired_capacity": "editor",
            "enforce_capacity": True,
        }

    def test_ensure_user_memberships_in_all_groups_counts_successes(self, monkeypatch):
        groups = [SimpleNamespace(id="g1"), SimpleNamespace(id="g2")]
        results = iter([True, False])

        monkeypatch.setattr(auth_helpers, "get_active_groups", lambda: groups)
        monkeypatch.setattr(
            auth_helpers,
            "ensure_user_membership",
            lambda *args, **kwargs: next(results),
        )

        assert auth_helpers.ensure_user_memberships_in_all_groups("alice") == 1

    def test_ensure_all_ldap_users_in_group_returns_zero_for_organization(
        self, monkeypatch
    ):
        monkeypatch.setattr(
            auth_helpers,
            "get_group",
            lambda group_id: SimpleNamespace(is_organization=True),
        )

        assert auth_helpers.ensure_all_ldap_users_in_group("org-id") == 0

    def test_ensure_all_ldap_users_in_group_counts_successes(self, monkeypatch):
        fake_group = SimpleNamespace(id="group-id", is_organization=False)
        fake_users = [SimpleNamespace(id="u1"), SimpleNamespace(id="u2")]
        results = iter([True, False])

        monkeypatch.setattr(auth_helpers, "get_group", lambda group_id: fake_group)
        monkeypatch.setattr(auth_helpers, "get_ldap_users", lambda: fake_users)
        monkeypatch.setattr(
            auth_helpers,
            "ensure_user_membership",
            lambda *args, **kwargs: next(results),
        )

        assert auth_helpers.ensure_all_ldap_users_in_group("group-id") == 1

    def test_ensure_artesp_org_state_creates_missing_org(self, monkeypatch):
        created_payloads = []

        def fake_get_action(name):
            if name == "organization_show":
                def show(context, data_dict):
                    raise tk.ObjectNotFound()
                return show
            if name == "organization_create":
                return lambda context, data_dict: created_payloads.append(dict(data_dict))
            raise AssertionError(name)

        monkeypatch.setattr(auth_helpers.tk, "get_action", fake_get_action)
        monkeypatch.setattr(auth_helpers, "get_artesp_org", lambda: "org-created")

        assert auth_helpers.ensure_artesp_org_state() == "org-created"
        assert created_payloads == [{"name": "artesp", "title": "ARTESP"}]

    def test_ensure_artesp_org_state_patches_title_and_state(self, monkeypatch):
        patched_payloads = []

        def fake_get_action(name):
            if name == "organization_show":
                return lambda context, data_dict: {
                    "id": "org-id",
                    "title": "Old title",
                    "state": "deleted",
                }
            if name == "organization_patch":
                return lambda context, data_dict: patched_payloads.append(dict(data_dict))
            raise AssertionError(name)

        monkeypatch.setattr(auth_helpers.tk, "get_action", fake_get_action)
        monkeypatch.setattr(auth_helpers, "get_artesp_org", lambda: "patched-org")

        assert auth_helpers.ensure_artesp_org_state() == "patched-org"
        assert patched_payloads == [
            {"id": "org-id", "title": "ARTESP", "state": "active"}
        ]


class TestCollaboratorResolutionHelpers:
    def test_package_has_valid_creator_returns_true_for_existing_creator(self):
        org = _artesp_org()
        creator = factories.User()
        package = factories.Dataset(user=creator, owner_org=org["id"])
        package_obj = model.Package.get(package["id"])

        assert auth_helpers.package_has_valid_creator(package_obj) is True

    def test_get_target_user_supports_username_and_empty_payload(self):
        user = factories.User()

        assert auth_helpers.get_target_user({}).__class__ is None.__class__
        assert auth_helpers.get_target_user({"username": user["name"]}).id == user["id"]

    def test_resolve_or_create_collaborator_user_returns_none_when_ldap_missing(
        self, monkeypatch
    ):
        monkeypatch.setattr(auth_helpers, "find_local_user_by_identifier", lambda value: None)

        with patch.dict(
            sys.modules,
            {
                "ckanext.ldap.lib.exceptions": None,
                "ckanext.ldap.lib.search": None,
                "ckanext.ldap.routes": None,
            },
        ):
            assert auth_helpers.resolve_or_create_collaborator_user("alice") is None

    def test_resolve_or_create_collaborator_user_raises_validation_error_for_multiple_match(
        self, monkeypatch
    ):
        class MultipleMatchError(Exception):
            pass

        class UserConflictError(Exception):
            pass

        fake_exceptions = types.SimpleNamespace(
            MultipleMatchError=MultipleMatchError,
            UserConflictError=UserConflictError,
        )
        fake_search = types.SimpleNamespace(
            find_ldap_user=lambda user_identifier: (_ for _ in ()).throw(
                MultipleMatchError("many matches")
            )
        )
        fake_helpers = types.SimpleNamespace(get_or_create_ldap_user=lambda user_dict: None)
        fake_routes = types.SimpleNamespace(_helpers=fake_helpers)

        monkeypatch.setattr(auth_helpers, "find_local_user_by_identifier", lambda value: None)

        with patch.dict(
            sys.modules,
            {
                "ckanext.ldap.lib.exceptions": fake_exceptions,
                "ckanext.ldap.lib.search": fake_search,
                "ckanext.ldap.routes": fake_routes,
            },
        ):
            with pytest.raises(tk.ValidationError):
                auth_helpers.resolve_or_create_collaborator_user("alice")

    def test_resolve_or_create_collaborator_user_returns_none_when_ldap_user_not_found(
        self, monkeypatch
    ):
        class MultipleMatchError(Exception):
            pass

        class UserConflictError(Exception):
            pass

        fake_exceptions = types.SimpleNamespace(
            MultipleMatchError=MultipleMatchError,
            UserConflictError=UserConflictError,
        )
        fake_search = types.SimpleNamespace(find_ldap_user=lambda user_identifier: None)
        fake_helpers = types.SimpleNamespace(get_or_create_ldap_user=lambda user_dict: None)
        fake_routes = types.SimpleNamespace(_helpers=fake_helpers)

        monkeypatch.setattr(auth_helpers, "find_local_user_by_identifier", lambda value: None)

        with patch.dict(
            sys.modules,
            {
                "ckanext.ldap.lib.exceptions": fake_exceptions,
                "ckanext.ldap.lib.search": fake_search,
                "ckanext.ldap.routes": fake_routes,
            },
        ):
            assert auth_helpers.resolve_or_create_collaborator_user("alice") is None

    def test_resolve_or_create_collaborator_user_raises_validation_error_for_conflict(
        self, monkeypatch
    ):
        class MultipleMatchError(Exception):
            pass

        class UserConflictError(Exception):
            pass

        fake_exceptions = types.SimpleNamespace(
            MultipleMatchError=MultipleMatchError,
            UserConflictError=UserConflictError,
        )
        fake_search = types.SimpleNamespace(
            find_ldap_user=lambda user_identifier: {"cn": "cn=Alice"}
        )
        fake_helpers = types.SimpleNamespace(
            get_or_create_ldap_user=lambda user_dict: (_ for _ in ()).throw(
                UserConflictError("conflict")
            )
        )
        fake_routes = types.SimpleNamespace(_helpers=fake_helpers)

        monkeypatch.setattr(auth_helpers, "find_local_user_by_identifier", lambda value: None)

        with patch.dict(
            sys.modules,
            {
                "ckanext.ldap.lib.exceptions": fake_exceptions,
                "ckanext.ldap.lib.search": fake_search,
                "ckanext.ldap.routes": fake_routes,
            },
        ):
            with pytest.raises(tk.ValidationError):
                auth_helpers.resolve_or_create_collaborator_user("alice")

    def test_resolve_or_create_collaborator_user_creates_user_and_ensures_memberships(
        self, monkeypatch
    ):
        class MultipleMatchError(Exception):
            pass

        class UserConflictError(Exception):
            pass

        fake_exceptions = types.SimpleNamespace(
            MultipleMatchError=MultipleMatchError,
            UserConflictError=UserConflictError,
        )
        fake_search = types.SimpleNamespace(
            find_ldap_user=lambda user_identifier: {"cn": "cn=Alice"}
        )
        fake_helpers = types.SimpleNamespace(
            get_or_create_ldap_user=lambda user_dict: "ldap-alice"
        )
        fake_routes = types.SimpleNamespace(_helpers=fake_helpers)
        resolved_user = SimpleNamespace(id="user-id", name="ldap-alice")
        lookups = iter([None, resolved_user])
        ensured = []

        monkeypatch.setattr(
            auth_helpers,
            "find_local_user_by_identifier",
            lambda value: next(lookups),
        )
        monkeypatch.setattr(
            auth_helpers,
            "ensure_user_membership_in_artesp",
            lambda username: ensured.append(("artesp", username)),
        )
        monkeypatch.setattr(
            auth_helpers,
            "ensure_user_memberships_in_all_groups",
            lambda username: ensured.append(("groups", username)),
        )

        with patch.dict(
            sys.modules,
            {
                "ckanext.ldap.lib.exceptions": fake_exceptions,
                "ckanext.ldap.lib.search": fake_search,
                "ckanext.ldap.routes": fake_routes,
            },
        ):
            result = auth_helpers.resolve_or_create_collaborator_user("alice")

        assert result is resolved_user
        assert ensured == [("artesp", "ldap-alice"), ("groups", "ldap-alice")]


class TestPermissionHelpers:
    def test_is_dataset_collaborators_enabled_reads_config(self):
        assert auth_helpers.is_dataset_collaborators_enabled() is True

    def test_is_admin_collaborators_enabled_reads_config(self):
        with patch.object(
            auth_helpers.tk,
            "config",
            {"ckan.auth.allow_admin_collaborators": False},
        ):
            assert auth_helpers.is_admin_collaborators_enabled() is False

    def test_requested_capacity_is_allowed_handles_empty_and_known(self, monkeypatch):
        monkeypatch.setattr(
            auth_helpers.authz,
            "get_collaborator_capacities",
            lambda: ["member", "editor", "admin"],
        )

        assert auth_helpers.requested_capacity_is_allowed("") is False
        assert auth_helpers.requested_capacity_is_allowed("editor") is True

    def test_user_has_edit_collaborator_capacity_returns_true_for_editor(self):
        org = _artesp_org()
        creator = factories.User()
        editor = factories.User()
        package = factories.Dataset(user=creator, owner_org=org["id"])
        package_obj = model.Package.get(package["id"])
        editor_obj = model.User.get(editor["name"])

        tk.get_action("package_collaborator_create")(
            {"ignore_auth": True},
            {"id": package["id"], "user_id": editor["id"], "capacity": "editor"},
        )

        assert auth_helpers.user_has_edit_collaborator_capacity(package_obj, editor_obj) is True

    @pytest.mark.ckan_config("ckan.auth.allow_dataset_collaborators", False)
    def test_user_has_edit_collaborator_capacity_returns_false_when_disabled(self):
        org = _artesp_org()
        creator = factories.User()
        other_user = factories.User()
        package = factories.Dataset(user=creator, owner_org=org["id"])
        package_obj = model.Package.get(package["id"])
        other_user_obj = model.User.get(other_user["name"])

        assert auth_helpers.user_has_edit_collaborator_capacity(package_obj, other_user_obj) is False

    def test_user_can_edit_package_allows_editor_collaborator(self):
        org = _artesp_org()
        creator = factories.User()
        editor = factories.User()
        package = factories.Dataset(user=creator, owner_org=org["id"])
        package_obj = model.Package.get(package["id"])
        editor_obj = model.User.get(editor["name"])

        tk.get_action("package_collaborator_create")(
            {"ignore_auth": True},
            {"id": package["id"], "user_id": editor["id"], "capacity": "editor"},
        )

        assert auth_helpers.user_can_edit_package(package_obj, editor_obj) is True

    def test_user_can_manage_collaborators_allows_owner_and_admin(self):
        org = _artesp_org()
        creator = factories.User()
        dataset_admin = factories.User()
        sysadmin = factories.Sysadmin()
        package = factories.Dataset(user=creator, owner_org=org["id"])
        package_obj = model.Package.get(package["id"])
        creator_obj = model.User.get(creator["name"])
        admin_obj = model.User.get(dataset_admin["name"])

        tk.get_action("package_collaborator_create")(
            {"user": sysadmin["name"]},
            {"id": package["id"], "user_id": dataset_admin["id"], "capacity": "admin"},
        )

        assert auth_helpers.user_can_manage_collaborators(package_obj, creator_obj) is True
        assert auth_helpers.user_can_manage_collaborators(package_obj, admin_obj) is True

    @pytest.mark.ckan_config("ckan.auth.allow_admin_collaborators", False)
    def test_user_can_manage_collaborators_returns_false_when_admin_feature_disabled(
        self,
    ):
        org = _artesp_org()
        creator = factories.User()
        collaborator = factories.User()
        package = factories.Dataset(user=creator, owner_org=org["id"])
        package_obj = model.Package.get(package["id"])
        collaborator_obj = model.User.get(collaborator["name"])

        assert auth_helpers.user_can_manage_collaborators(package_obj, collaborator_obj) is False
