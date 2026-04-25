"""Tests for auth.py."""

from types import SimpleNamespace
import uuid

import ckan.model as model
import pytest
from ckan.tests import factories

from ckanext.artesp_theme.logic import auth as artesp_auth
from ckanext.artesp_theme.logic import auth_helpers


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.ckan_config(
        "ckanext.artesp_theme.default_dataset_collaborator_capacity", "editor"
    ),
    pytest.mark.usefixtures("with_plugins"),
]


def _artesp_org():
    org = auth_helpers.get_artesp_org()
    if org:
        return {"id": org.id, "name": org.name}
    return factories.Organization(name="artesp")


def _auth_user(sysadmin=False):
    return SimpleNamespace(id="auth-user-{}".format(sysadmin), sysadmin=sysadmin)


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


def _dataset(owner_org, user):
    suffix = uuid.uuid4().hex[:10]
    package = model.Package(
        name="dataset-auth-role-override-{}".format(suffix),
        title="Dataset auth role override",
        owner_org=owner_org,
        creator_user_id=user["id"],
        state="active",
    )
    model.Session.add(package)
    model.Session.flush()
    return {"id": package.id, "name": package.name}


def test_artesp_theme_get_sum():
    assert artesp_auth.artesp_theme_get_sum({"model": model}, {})["success"]


def test_dashboard_statistics_allows_anonymous_access():
    assert artesp_auth.artesp_theme_dashboard_statistics({"model": model}, {})[
        "success"
    ]


def test_get_auth_functions_export_group_and_organization_management():
    auth_functions = artesp_auth.get_auth_functions()

    assert (
        auth_functions["artesp_theme_dashboard_statistics"]
        is artesp_auth.artesp_theme_dashboard_statistics
    )
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
    regular_user = _auth_user(sysadmin=False)
    sysadmin = _auth_user(sysadmin=True)

    denied = getattr(artesp_auth, action_name)(
        {"model": model, "auth_user_obj": regular_user},
        {},
    )
    allowed = getattr(artesp_auth, action_name)(
        {"model": model, "auth_user_obj": sysadmin},
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
    regular_user = _auth_user(sysadmin=False)
    sysadmin = _auth_user(sysadmin=True)

    denied = getattr(artesp_auth, action_name)(
        {"model": model, "auth_user_obj": regular_user},
        {},
    )
    allowed = getattr(artesp_auth, action_name)(
        {"model": model, "auth_user_obj": sysadmin},
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
    artesp_org = _artesp_org()
    creator = _user("auth-role-creator")
    collaborator = _user("auth-role-collaborator")
    package = _dataset(artesp_org["id"], creator)

    denied = artesp_auth.package_collaborator_create(
        {"model": model, "user": creator["name"]},
        {
            "id": package["id"],
            "user_id": collaborator["id"],
            "capacity": "member",
        },
    )

    assert denied["success"] is False
