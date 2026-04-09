"""Tests for views.py."""

import pytest
from types import SimpleNamespace
from unittest.mock import patch

import ckan.plugins.toolkit as tk
from ckan.lib import base


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_artesp_theme_blueprint(app, reset_db):
    resp = app.get(tk.h.url_for("artesp_theme.about_ckan"))
    assert resp.status_code == 200
    assert "CKAN" in resp.text


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.ckan_config("ckanext.ldap.uri", "ldap://ldap:389")
@pytest.mark.usefixtures("with_plugins")
def test_login_page_hides_forgot_password_when_ldap_enabled(app, reset_db):
    resp = app.get(tk.h.url_for("user.login"))

    assert resp.status_code == 200
    assert 'action="/user/verify"' in resp.text
    assert "Forgotten your password?" not in resp.text
    assert "Forgot your password?" not in resp.text


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.ckan_config("ckanext.ldap.uri", "ldap://ldap:389")
@pytest.mark.usefixtures("with_plugins")
def test_request_reset_route_is_forbidden_when_ldap_enabled(app, reset_db):
    resp = app.get(tk.h.url_for("user.request_reset"), status=403)

    assert resp.status_code == 403
    assert "Unauthorized to request reset password." in resp.text


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_login_page_keeps_forgot_password_when_ldap_disabled(app, reset_db):
    resp = app.get(tk.h.url_for("user.login"))

    assert resp.status_code == 200
    assert "Forgotten your password?" in resp.text
    assert "Forgot your password?" in resp.text


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_resource_form_renders_without_scheming_fields(app, reset_db):
    with app.flask_app.test_request_context("/dataset/teste/resource/new"):
        html = base.render_snippet(
            "package/snippets/resource_form.html",
            data={},
            errors={},
            error_summary={},
            include_metadata=False,
            pkg_name="teste",
            stage=None,
            dataset_type="dataset",
        )

    assert 'id="field-name"' in html
    assert 'id="field-format"' in html
    assert 'resource-edit' in html


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_package_basic_fields_keep_visibility_enabled_for_fixed_artesp_org(app, reset_db):
    artesp_org = SimpleNamespace(id="artesp-id", name="artesp", title="ARTESP")

    with patch(
        "ckanext.artesp_theme.logic.auth_helpers.get_artesp_org",
        return_value=artesp_org,
    ), patch(
        "ckanext.artesp_theme.logic.auth_helpers.get_artesp_org_display_name",
        return_value="ARTESP",
    ):
        with app.flask_app.test_request_context("/dataset/new"):
            html = base.render_snippet(
                "package/snippets/package_basic_fields.html",
                data={},
                errors={},
            )

    assert 'data-module="dataset-visibility"' not in html
    assert 'name="owner_org" value="{0}"'.format(artesp_org.id) in html
    assert (
        '<select id="field-private" name="private" class="form-control">'
        in html
    )


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_package_basic_fields_render_optional_group_selector_after_organization(
    app, reset_db
):
    groups = [
        {"id": "grupo-1", "display_name": "Grupo 1"},
        {"id": "grupo-2", "display_name": "Grupo 2"},
    ]
    artesp_org = SimpleNamespace(id="artesp-id", name="artesp", title="ARTESP")

    with patch(
        "ckanext.artesp_theme.logic.auth_helpers.get_artesp_org",
        return_value=artesp_org,
    ), patch(
        "ckanext.artesp_theme.logic.auth_helpers.get_artesp_org_display_name",
        return_value="ARTESP",
    ), patch.object(tk.h, "groups_available", return_value=groups):
        with app.flask_app.test_request_context("/dataset/new?group=grupo-2"):
            html = base.render_snippet(
                "package/snippets/package_basic_fields.html",
                data={"group_id": "grupo-2"},
                errors={},
            )

    assert 'id="field-groups__0__id"' in html
    assert 'name="groups__0__id"' in html
    assert "Grupo 1" in html
    assert "Grupo 2" in html
    assert '<option value=""' in html
    assert '<option value="grupo-2" selected>' in html
    assert html.index('id="field-fixed-organization"') < html.index(
        'id="field-groups__0__id"'
    )
    assert html.index('id="field-groups__0__id"') < html.index('id="field-private"')


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme scheming_datasets")
@pytest.mark.usefixtures("with_plugins")
def test_scheming_organization_snippet_keeps_visibility_enabled_for_fixed_artesp_org(
    app, reset_db
):
    artesp_org = SimpleNamespace(id="artesp-id", name="artesp", title="ARTESP")
    groups = [
        {"id": "grupo-1", "display_name": "Grupo 1"},
        {"id": "grupo-2", "display_name": "Grupo 2"},
    ]

    with patch(
        "ckanext.artesp_theme.logic.auth_helpers.get_artesp_org",
        return_value=artesp_org,
    ), patch(
        "ckanext.artesp_theme.logic.auth_helpers.get_artesp_org_display_name",
        return_value="ARTESP",
    ), patch.object(tk.h, "groups_available", return_value=groups):
        with app.flask_app.test_request_context("/dataset/new"):
            html = base.render_snippet(
                "scheming/form_snippets/organization.html",
                field={"field_name": "owner_org", "label": "Organization"},
                data={},
                errors={},
            )

    assert 'data-module="dataset-visibility"' not in html
    assert 'name="owner_org" value="{0}"'.format(artesp_org.id) in html
    assert 'id="field-groups__0__id"' in html
    assert (
        '<select id="field-private" name="private" class="form-control form-select">'
        in html
    )
    assert html.index('field-owner_org') < html.index('id="field-groups__0__id"')
    assert html.index('id="field-groups__0__id"') < html.index('id="field-private"')
