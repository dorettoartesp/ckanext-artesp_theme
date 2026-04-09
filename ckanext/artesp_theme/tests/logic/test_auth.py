"""Tests for auth.py."""

import ckan.model as model
import pytest
from ckan.tests import factories, helpers as test_helpers

from ckanext.artesp_theme.logic import auth as artesp_auth


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.ckan_config(
        "ckanext.artesp_theme.default_dataset_collaborator_capacity", "editor"
    ),
    pytest.mark.usefixtures("with_plugins", "clean_db"),
]


def test_artesp_theme_get_sum():
    assert artesp_auth.artesp_theme_get_sum({"model": model}, {})["success"]


def test_get_auth_functions_export_group_and_organization_management():
    auth_functions = artesp_auth.get_auth_functions()

    assert auth_functions["request_reset"] is artesp_auth.request_reset
    assert auth_functions["user_reset"] is artesp_auth.user_reset
    assert auth_functions["organization_create"] is artesp_auth.organization_create
    assert auth_functions["organization_update"] is artesp_auth.organization_update
    assert auth_functions["organization_delete"] is artesp_auth.organization_delete
    assert auth_functions["group_create"] is artesp_auth.group_create
    assert auth_functions["group_update"] is artesp_auth.group_update
    assert auth_functions["group_delete"] is artesp_auth.group_delete


@pytest.mark.parametrize(
    "action_name",
    [
        "organization_create",
        "organization_update",
        "organization_delete",
    ],
)
def test_organization_management_is_reserved_for_sysadmins(action_name):
    regular_user = factories.User()
    sysadmin = factories.Sysadmin()

    denied = getattr(artesp_auth, action_name)(
        {"model": model, "user": regular_user["name"]},
        {},
    )
    allowed = getattr(artesp_auth, action_name)(
        {"model": model, "user": sysadmin["name"]},
        {},
    )

    assert denied["success"] is False
    assert allowed["success"] is True


@pytest.mark.parametrize(
    "action_name",
    [
        "group_create",
        "group_update",
        "group_delete",
    ],
)
def test_group_management_is_reserved_for_sysadmins(action_name):
    regular_user = factories.User()
    sysadmin = factories.Sysadmin()

    denied = getattr(artesp_auth, action_name)(
        {"model": model, "user": regular_user["name"]},
        {},
    )
    allowed = getattr(artesp_auth, action_name)(
        {"model": model, "user": sysadmin["name"]},
        {},
    )

    assert denied["success"] is False
    assert allowed["success"] is True


@pytest.mark.ckan_config("ckanext.ldap.uri", "ldap://ldap:389")
@pytest.mark.parametrize("action_name", ["request_reset", "user_reset"])
def test_password_reset_is_disabled_when_ldap_is_enabled(action_name):
    result = getattr(artesp_auth, action_name)({"model": model}, {})

    assert result["success"] is False
    assert "Password reset is disabled for LDAP users" in result["msg"]


@pytest.mark.parametrize("action_name", ["request_reset", "user_reset"])
def test_password_reset_is_allowed_when_ldap_is_disabled(action_name):
    result = getattr(artesp_auth, action_name)({"model": model}, {})

    assert result["success"] is True


def test_package_collaborator_create_blocks_non_sysadmin_role_override():
    artesp_org = factories.Organization(name="artesp")
    creator = factories.User()
    collaborator = factories.User()
    package = test_helpers.call_action(
        "package_create",
        context={"user": creator["name"]},
        name="dataset-auth-role-override",
        title="Dataset auth role override",
        owner_org=artesp_org["id"],
    )

    denied = artesp_auth.package_collaborator_create(
        {"model": model, "user": creator["name"]},
        {
            "id": package["id"],
            "user_id": collaborator["id"],
            "capacity": "member",
        },
    )

    assert denied["success"] is False
