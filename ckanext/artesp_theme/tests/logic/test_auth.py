"""Tests for auth.py."""

import ckan.model as model
import pytest
from ckan.tests import factories

from ckanext.artesp_theme.logic import auth as artesp_auth


pytestmark = [
    pytest.mark.ckan_config("ckan.plugins", "artesp_theme"),
    pytest.mark.usefixtures("with_plugins", "clean_db"),
]


def test_artesp_theme_get_sum():
    assert artesp_auth.artesp_theme_get_sum({"model": model}, {})["success"]


def test_get_auth_functions_exports_organization_create():
    auth_functions = artesp_auth.get_auth_functions()

    assert auth_functions["organization_create"] is artesp_auth.organization_create


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
