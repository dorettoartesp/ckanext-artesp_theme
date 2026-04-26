"""Tests for views.py."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

import ckan.plugins.toolkit as tk
from ckan.lib import base


def _assert_about_page_has_blueprint_and_statistics_nav(app):
    resp = app.get(tk.h.url_for("artesp_theme.about_ckan"))

    assert resp.status_code == 200
    assert "CKAN" in resp.text
    assert 'href="/estatisticas"' in resp.text
    assert "Estatísticas" in resp.text
    assert 'href="https://www.artesp.sp.gov.br/artesp"' in resp.text
    assert 'target="_blank"' in resp.text


def _assert_default_login_keeps_forgot_password(app):
    resp = app.get(tk.h.url_for("user.login"))

    assert resp.status_code == 200
    assert "Forgotten your password?" in resp.text
    assert "Forgot your password?" in resp.text


def _assert_logout_first_uses_ckan_logout_for_internal_users(app):
    current_user = SimpleNamespace(name="usuario-ldap")

    with patch.object(tk.h, "artesp_is_external_user", return_value=False):
        with app.flask_app.test_request_context(
            "/user/login",
            environ_base={"CKAN_CURRENT_URL": "/user/login"},
        ):
            html = base.render("user/logout_first.html", extra_vars={"current_user": current_user})

    assert 'href="/user/_logout"' in html
    assert "Log out now" in html


def _assert_govbr_link_snippets_handle_missing_extras(app):
    with app.flask_app.test_request_context(
        "/user/teste",
        environ_overrides={"CKAN_LANG": "pt_BR"},
    ):
        html = base.render_snippet("user/snippets/govbr_link.html", user=None)

    assert "Nenhuma conta Gov.br vinculada." in html
    assert 'href="/user/oidc/link"' in html

    user = {
        "name": "usuario-interno",
        "display_name": "Usuario Interno",
        "plugin_extras": None,
    }

    with app.flask_app.test_request_context(
        "/user/teste",
        environ_overrides={"CKAN_LANG": "pt_BR"},
    ):
        html = base.render_snippet("user/snippets/govbr_link.html", user=user)

    assert "Nenhuma conta Gov.br vinculada." in html
    assert 'href="/user/oidc/link"' in html


def _assert_header_snippets(app):
    user = SimpleNamespace(
        id="usuario-interno-id",
        name="usuario-interno",
        display_name="Usuario Interno",
        sysadmin=False,
    )

    with patch.object(tk.h, "artesp_is_external_user", return_value=False), patch.object(
        tk.h, "user_image", return_value=""
    ), patch.object(tk.h, "csrf_input", return_value=""):
        with app.flask_app.test_request_context(
            "/dataset/exemplo",
            environ_overrides={"CKAN_LANG": "pt_BR"},
        ):
            tk.c.user = user.name
            tk.c.userobj = user
            base.render("header.html")

    sysadmin = SimpleNamespace(
        id="sysadmin-id",
        name="sysadmin-user",
        display_name="Sysadmin User",
        sysadmin=True,
    )

    with patch.object(tk.h, "artesp_is_external_user", return_value=False), patch.object(
        tk.h, "artesp_auth_provider", return_value="local"
    ), patch.object(tk.h, "user_image", return_value=""), patch.object(
        tk.h, "csrf_input", return_value=""
    ):
        with app.flask_app.test_request_context(
            "/dataset/exemplo",
            environ_overrides={"CKAN_LANG": "pt_BR"},
        ):
            tk.c.user = sysadmin.name
            tk.c.userobj = sysadmin
            html = base.render("header.html")

    assert 'href="/admin/audit"' in html
    assert "Auditoria" in html

    with patch.object(tk.h, "artesp_auth_provider", return_value="govbr"), patch.object(
        tk.h, "artesp_is_external_user", return_value=False
    ), patch.object(tk.h, "user_image", return_value=""), patch.object(
        tk.h, "csrf_input", return_value=""
    ):
        with app.flask_app.test_request_context(
            "/dataset/exemplo",
            environ_overrides={"CKAN_LANG": "pt_BR"},
        ):
            tk.c.user = user.name
            tk.c.userobj = user
            html = base.render("header.html")

    assert 'action="/user/oidc/logout"' in html


def _assert_package_info_follow_button(app):
    pkg = SimpleNamespace(
        id="90986ead-e102-4cc8-affc-d01245497032",
        name="seed-artesp-dataset-muitos-recursos",
        title="Dataset de teste com muitos recursos",
    )
    current_user = SimpleNamespace(is_authenticated=True)

    with patch("flask_login.utils._get_user", return_value=current_user), patch.object(
        tk.h, "follow_count", return_value=2
    ):
        with app.flask_app.test_request_context(
            "/dataset/seed-artesp-dataset-muitos-recursos",
            environ_overrides={"CKAN_LANG": "pt_BR"},
        ):
            html = base.render_snippet(
                "package/snippets/info.html",
                pkg=pkg,
                am_following=True,
            )

    assert "Dataset de teste com muitos recursos" in html
    assert "Seguidores" in html
    assert "Desseguir" in html
    assert "Unfollow" not in html
    assert 'hx-post="/dataset/unfollow/90986ead-e102-4cc8-affc-d01245497032"' in html


def _assert_followed_page_lists_mixed_followees(app):
    user_dict = {
        "id": "usuario-interno-id",
        "name": "usuario-interno",
        "display_name": "Usuario Interno",
        "number_created_packages": 0,
        "email": "usuario-interno@example.com",
        "created": "2026-04-19T00:00:00.000000",
        "state": "active",
        "plugin_extras": {"artesp": {"user_type": "internal"}},
    }
    followees = [
        {
            "type": "dataset",
            "display_name": "Base de Acidentes",
            "dict": {"id": "dataset-id", "name": "base-de-acidentes"},
        },
        {
            "type": "organization",
            "display_name": "ARTESP",
            "dict": {"id": "org-id", "name": "artesp"},
        },
        {
            "type": "group",
            "display_name": "Rodoviário",
            "dict": {"id": "group-id", "name": "rodoviario"},
        },
        {
            "type": "user",
            "display_name": "Maria Santos",
            "dict": {"id": "user-id", "name": "maria-santos"},
        },
    ]

    def fake_get_action(name):
        actions = {
            "user_show": lambda context, data_dict: user_dict,
            "followee_list": lambda context, data_dict: followees,
        }
        return actions[name]

    with patch(
        "ckanext.artesp_theme.govbr.blueprint.toolkit.get_action",
        side_effect=fake_get_action,
    ), patch(
        "ckan.model.User.get",
        return_value=SimpleNamespace(name="usuario-interno", sysadmin=False),
    ), patch.object(
        tk.h, "organizations_available", return_value=[]
    ), patch.object(
        tk.h, "groups_available", return_value=[]
    ), patch.object(
        tk.h, "follow_count", return_value=0
    ), patch.object(
        tk.h, "user_image", return_value=""
    ), patch.object(
        tk.h, "SI_number_span", side_effect=lambda value: str(value)
    ), patch.object(
        tk.h, "render_datetime", return_value="19/04/2026"
    ), patch.object(
        tk.h, "check_access", return_value=False
    ):
        resp = app.get(
            "/user/usuario-interno/followed",
            extra_environ={"CKAN_LANG": "pt_BR"},
        )

    assert resp.status_code == 200
    assert "Seguindo" in resp.text
    assert "Conjunto de Dados" in resp.text
    assert "Organização" in resp.text
    assert "Grupo" in resp.text
    assert "Usuário" in resp.text
    assert 'href="/dataset/base-de-acidentes"' in resp.text
    assert 'href="/organization/artesp"' in resp.text
    assert 'href="/group/rodoviario"' in resp.text
    assert 'href="/user/maria-santos"' in resp.text
    assert "Base de Acidentes" in resp.text
    assert "ARTESP" in resp.text
    assert "Rodoviário" in resp.text
    assert "Maria Santos" in resp.text


def _assert_statistics_pages(app):
    dashboard = {
        "generated_at_label": "09/04/2026 10:30",
        "has_data": True,
        "filters": {
            "theme": "rodoviario",
            "theme_label": "Rodoviário",
            "period": "6m",
            "period_label": "Últimos 6 meses",
            "available_themes": [
                {"value": "all", "label": "Todos os temas"},
                {"value": "rodoviario", "label": "Rodoviário"},
            ],
            "available_periods": [
                {"value": "6m", "label": "Últimos 6 meses"},
                {"value": "12m", "label": "Últimos 12 meses"},
            ],
        },
        "kpis": {
            "dataset_count": 12,
            "resource_count": 44,
            "theme_count": 5,
            "format_count": 6,
            "organization_count": 1,
            "average_resources_per_dataset_label": "3,7",
            "empty_theme_count": 2,
            "datasets_without_theme_count": 1,
        },
        "topic_labels": ["Legislação", "Rodoviário", "Sem grupo"],
        "insights": [
            {
                "title": "Rodoviário concentra 20 recurso(s)",
                "description": "Tema com maior volume.",
            },
            {
                "title": "Acidentes reúne 9 recurso(s)",
                "description": "Maior conjunto.",
            },
            {
                "title": "CSV é o formato mais recorrente",
                "description": "Formato dominante.",
            },
        ],
        "charts": {
            "resources_by_theme": [{"label": "Rodoviário", "value": 20, "percent": 100.0}],
            "datasets_by_theme": [{"label": "Rodoviário", "value": 5, "percent": 100.0}],
            "timeline": [{"label": "2025", "value": 3, "percent": 100.0}],
            "top_datasets": [{"label": "Acidentes", "value": 9, "percent": 100.0}],
            "formats": [{"label": "CSV", "value": 8, "percent": 100.0}],
        },
        "table_rows": [
            {
                "rank": 1,
                "name": "acidentes",
                "title": "Acidentes",
                "theme": "Rodoviário",
                "resource_count": 9,
                "formats_label": "CSV",
                "modified_label": "09/04/2026",
                "share_percent": 20.5,
                "share_label": "20,5",
            }
        ],
        "table_total_count": 1,
    }

    with patch(
        "ckanext.artesp_theme.controllers.artesp_helpers.get_dashboard_statistics",
        return_value=dashboard,
    ) as get_dashboard_statistics:
        resp = app.get(tk.h.url_for("artesp_theme.statistics", theme="rodoviario", period="6m"))

    assert resp.status_code == 200
    get_dashboard_statistics.assert_called_once_with({"theme": "rodoviario", "period": "6m"})
    assert "Painel do Portal de Dados Abertos" in resp.text
    assert "Indicadores principais do portal" in resp.text
    assert "Rodoviário concentra 20 recurso(s)" in resp.text
    assert 'data-artesp-style="official-portal"' in resp.text
    assert "dashboard-statistics__brandline" not in resp.text
    assert "dashboard-statistics__section-title" in resp.text
    assert "dashboard-statistics__filter-icon" in resp.text
    assert "dashboard-statistics__stat-icon fa fa-database" in resp.text
    assert 'name="theme"' in resp.text
    assert 'value="rodoviario"' in resp.text
    assert 'name="period"' in resp.text
    assert 'value="6m"' in resp.text
    assert 'data-dashboard-endpoint="/api/3/action/artesp_theme_dashboard_statistics"' in resp.text
    assert "cdn.jsdelivr.net" not in resp.text
    assert "chart.umd.min.js" not in resp.text
    assert "<canvas" not in resp.text
    assert "Acidentes" in resp.text

    dashboard_without_rating = {
        "generated_at_label": "09/04/2026 10:30",
        "has_data": True,
        "filters": {
            "theme": "all",
            "theme_label": "Todos os temas",
            "period": "6m",
            "period_label": "Últimos 6 meses",
            "available_themes": [{"value": "all", "label": "Todos os temas"}],
            "available_periods": [{"value": "6m", "label": "Últimos 6 meses"}],
        },
        "kpis": {
            "dataset_count": 1,
            "resource_count": 1,
            "theme_count": 1,
            "format_count": 1,
            "organization_count": 1,
            "average_resources_per_dataset_label": "1,0",
            "empty_theme_count": 0,
            "datasets_without_theme_count": 0,
        },
        "topic_labels": ["Sem grupo"],
        "insights": [{"title": "Sem avaliações", "description": "Renderiza sem bloco rating."}],
        "charts": {
            "resources_by_theme": [],
            "datasets_by_theme": [],
            "timeline": [],
            "top_datasets": [],
            "formats": [],
        },
        "table_rows": [],
        "table_total_count": 0,
    }

    with patch(
        "ckanext.artesp_theme.controllers.artesp_helpers.get_dashboard_statistics",
        return_value=dashboard_without_rating,
    ):
        resp = app.get(tk.h.url_for("artesp_theme.statistics"))

    assert resp.status_code == 200
    assert "Ainda não há avaliações registradas para o filtro selecionado." in resp.text


def _assert_form_snippets(app):
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
    assert "resource-edit" in html

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
    assert '<select id="field-private" name="private" class="form-control">' in html

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
    assert html.index('id="field-fixed-organization"') < html.index('id="field-groups__0__id"')
    assert html.index('id="field-groups__0__id"') < html.index('id="field-private"')


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.usefixtures("with_plugins")
def test_default_theme_views_and_snippets(app):
    _assert_about_page_has_blueprint_and_statistics_nav(app)
    _assert_default_login_keeps_forgot_password(app)
    _assert_logout_first_uses_ckan_logout_for_internal_users(app)
    _assert_govbr_link_snippets_handle_missing_extras(app)
    _assert_header_snippets(app)
    _assert_package_info_follow_button(app)
    _assert_followed_page_lists_mixed_followees(app)
    _assert_statistics_pages(app)
    _assert_form_snippets(app)


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.ckan_config("ckanext.ldap.uri", "ldap://ldap:389")
@pytest.mark.usefixtures("with_plugins")
def test_ldap_login_and_password_reset(app):
    resp = app.get(tk.h.url_for("user.login"))

    assert resp.status_code == 200
    assert 'action="/user/verify"' in resp.text
    assert "Forgotten your password?" not in resp.text
    assert "Forgot your password?" not in resp.text

    resp = app.get(tk.h.url_for("user.request_reset"), status=403)

    assert resp.status_code == 403
    assert "Unauthorized to request reset password." in resp.text


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.ckan_config("ckanext.ldap.uri", "ldap://ldap:389")
@pytest.mark.ckan_config("ckanext.artesp.govbr.enabled", "true")
@pytest.mark.ckan_config("ckanext.artesp.govbr.client_id", "govbr-client-id")
@pytest.mark.usefixtures("with_plugins")
def test_govbr_ldap_login_page(app):
    resp = app.get(tk.h.url_for("user.login"))

    assert resp.status_code == 200
    assert "artesp-login-access" in resp.text
    assert 'href="/user/oidc/login"' in resp.text
    assert "artesp-govbr-login" in resp.text
    assert "<span>Entrar com</span><strong>gov.br</strong>" in resp.text
    assert "artesp-login-divider" in resp.text
    assert "<span>ou</span>" in resp.text
    assert "artesp-ldap-toggle" in resp.text
    assert 'aria-expanded="false"' in resp.text
    assert 'aria-controls="govbr-ldap-form"' in resp.text
    assert "data-artesp-login-toggle" in resp.text
    assert 'id="govbr-ldap-form" class="artesp-ldap-panel" hidden' in resp.text
    assert 'action="/user/verify"' in resp.text
    assert "Acesso ao portal" not in resp.text
    assert "Use sua conta gov.br" not in resp.text
    assert "Servidores ARTESP podem usar credenciais internas" not in resp.text
    assert (
        "Acesse informações públicas sobre a infraestrutura de transportes "
        "concedidos do Estado de São Paulo."
    ) in resp.text

    with app.flask_app.test_request_context(
        "/user/login",
        environ_base={"CKAN_CURRENT_URL": "/user/login"},
    ):
        html = base.render(
            "user/login.html",
            extra_vars={"error_summary": {"login": ["Login failed"]}},
        )

    assert 'aria-expanded="true"' in html
    assert 'id="govbr-ldap-form" class="artesp-ldap-panel">' in html
    assert 'id="govbr-ldap-form" class="artesp-ldap-panel" hidden' not in html
    assert "Login failed" in html


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.ckan_config("ckanext.ldap.uri", "ldap://ldap:389")
@pytest.mark.ckan_config("ckanext.artesp.govbr.enabled", "true")
@pytest.mark.ckan_config("ckanext.artesp.govbr.client_id", "")
@pytest.mark.usefixtures("with_plugins")
def test_login_page_hides_govbr_actions_without_client_id(app):
    resp = app.get(tk.h.url_for("user.login"))

    assert resp.status_code == 200
    assert 'action="/user/verify"' in resp.text
    assert 'href="/user/oidc/login"' not in resp.text
    assert "artesp-govbr-login" not in resp.text
    assert "artesp-login-divider" not in resp.text
    assert "artesp-ldap-toggle" not in resp.text


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.ckan_config("ckanext.artesp.govbr.enabled", "true")
@pytest.mark.ckan_config("ckanext.artesp.govbr.client_id", "govbr-client-id")
@pytest.mark.usefixtures("with_plugins")
def test_logout_first_page_uses_govbr_logout(app):
    current_user = SimpleNamespace(name="usuario-ldap")

    with patch.object(tk.h, "artesp_auth_provider", return_value="govbr"), patch.object(
        tk.h, "artesp_is_external_user", return_value=False
    ):
        with app.flask_app.test_request_context(
            "/user/login",
            environ_base={"CKAN_CURRENT_URL": "/user/login"},
        ):
            html = base.render("user/logout_first.html", extra_vars={"current_user": current_user})

    assert 'href="/user/oidc/logout"' in html
    assert "Log out now" in html


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.ckan_config("ckan.recaptcha.publickey", "legacy-google-key")
@pytest.mark.usefixtures("with_plugins")
def test_login_page_does_not_render_captcha(app):
    resp = app.get(tk.h.url_for("user.login"))

    assert resp.status_code == 200
    assert "g-recaptcha" not in resp.text
    assert "Recaptcha" not in resp.text


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme")
@pytest.mark.ckan_config("ckanext.artesp.rating.altcha_hmac_secret", "rating-altcha-secret")
@pytest.mark.usefixtures("with_plugins")
def test_rating_snippet_renders_altcha_for_comments(app):
    pkg = SimpleNamespace(
        id="90986ead-e102-4cc8-affc-d01245497032",
        name="seed-artesp-dataset-muitos-recursos",
        title="Dataset de teste com muitos recursos",
    )
    current_user = SimpleNamespace(is_authenticated=True)

    with patch("flask_login.utils._get_user", return_value=current_user):
        with app.flask_app.test_request_context(
            "/dataset/seed-artesp-dataset-muitos-recursos",
            environ_overrides={"CKAN_LANG": "pt_BR"},
        ):
            html = base.render_snippet("package/snippets/rating.html", pkg=pkg)

    assert "altcha-widget" in html
    assert "/dataset-rating/comment-captcha/challenge" in html
    assert 'challenge="/dataset-rating/comment-captcha/challenge"' in html
    assert "challengeurl=" not in html
    assert "https://cdn.jsdelivr.net/npm/altcha@3.0.4/dist/main/altcha.i18n.min.js" in html
    assert "https://cdn.jsdelivr.net/npm/altcha@3.0.4/dist/external/altcha.min.css" in html
    assert 'class="artesp-rating__comment-captcha"' in html
    assert 'class="artesp-rating__comment-captcha" hidden' not in html
    assert "g-recaptcha" not in html


@pytest.mark.ckan_config("ckan.plugins", "artesp_theme scheming_datasets")
@pytest.mark.usefixtures("with_plugins")
def test_scheming_organization_snippet_keeps_visibility_enabled_for_fixed_artesp_org(app):
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
    assert '<select id="field-private" name="private" class="form-control form-select">' in html
    assert 'id="field-groups__0__id"' in html
    assert html.index("field-owner_org") < html.index('id="field-groups__0__id"')
    assert html.index('id="field-groups__0__id"') < html.index('id="field-private"')
