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


def test_get_auth_functions_export_group_and_organization_create():
    auth_functions = artesp_auth.get_auth_functions()

    assert auth_functions["organization_create"] is artesp_auth.organization_create
    assert auth_functions["group_create"] is artesp_auth.group_create


def test_organization_create_is_reserved_for_sysadmins():
    regular_user = factories.User()
    sysadmin = factories.Sysadmin()

    denied = artesp_auth.organization_create(
        {"model": model, "user": regular_user["name"]},
        {},
    )
    allowed = artesp_auth.organization_create(
        {"model": model, "user": sysadmin["name"]},
        {},
    )

    assert denied["success"] is False
    assert allowed["success"] is True


def test_group_create_is_reserved_for_sysadmins():
    regular_user = factories.User()
    sysadmin = factories.Sysadmin()

    denied = artesp_auth.group_create(
        {"model": model, "user": regular_user["name"]},
        {},
    )
    allowed = artesp_auth.group_create(
        {"model": model, "user": sysadmin["name"]},
        {},
    )

    assert denied["success"] is False
    assert allowed["success"] is True


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
